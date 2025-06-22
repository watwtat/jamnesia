import os
import uuid

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

from models import Action, Hand, Player, Position, db
from poker_engine import PokerHandBuilder

app = Flask(__name__)

# データベース設定
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///jamnesia.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

db.init_app(app)


@app.before_request
def create_tables():
    """Create tables on first startup"""
    if not hasattr(create_tables, "_called"):
        db.create_all()
        create_tables._called = True


@app.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@app.route("/input")
def input_form():
    """Hand input form"""
    return render_template("input.html")


@app.route("/api/save-hand", methods=["POST"])
def save_hand():
    """Save hand to database"""
    try:
        data = request.get_json()

        # Check required fields
        required_fields = ["players", "actions"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate maximum number of players
        players_data = data["players"]
        if len(players_data) >= 10:
            return jsonify({"error": "Maximum of 9 players allowed"}), 400

        # Generate play ID if not specified
        play_id = data.get("play_id", str(uuid.uuid4()))

        # Build hand with PokerKit
        builder = PokerHandBuilder()
        players_data = data["players"]

        builder.create_game(
            players=players_data,
            small_blind=data.get("small_blind", 1.0),
            big_blind=data.get("big_blind", 2.0),
        )

        # Set hole cards
        if "hole_cards" in data:
            builder.deal_hole_cards(data["hole_cards"])

        # Validate and process actions
        player_stacks = {p["name"]: p["stack"] for p in players_data}
        current_bet = data.get("big_blind", 2.0)  # Start with big blind as current bet
        player_bets = {
            p["name"]: 0 for p in players_data
        }  # Track total bets per player
        processed_actions = []  # Store processed actions with correct amounts

        # Set initial blinds
        if len(players_data) >= 2:
            player_bets[players_data[0]["name"]] = data.get("small_blind", 1.0)
            player_bets[players_data[1]["name"]] = data.get("big_blind", 2.0)

        for action in data["actions"]:
            player_name = action["player_name"]
            action_type = action["action_type"]
            amount = action.get("amount", 0)
            street = action.get("street", "preflop")  # Get street from action data

            # Validate player exists
            if player_name not in player_stacks:
                return jsonify({"error": f"Player {player_name} not found"}), 400

            # Calculate actual action amount and validate
            if action_type == "call":
                # Calculate call amount (difference between current bet and player's current bet)
                call_amount = max(0, current_bet - player_bets[player_name])
                # Ensure player has enough chips
                available_chips = player_stacks[player_name] - player_bets[player_name]
                actual_amount = min(call_amount, available_chips)
                player_bets[player_name] += actual_amount
                builder.add_action(player_name, action_type, actual_amount)
                # Store processed action with correct amount and street
                processed_action = action.copy()
                processed_action["amount"] = actual_amount
                processed_action["street"] = street
                processed_actions.append(processed_action)

            elif action_type in ["bet", "raise"]:
                # For raise, the amount is the total bet, not additional
                total_bet = amount
                additional_amount = total_bet - player_bets[player_name]

                # Validate bet/raise amount doesn't exceed stack
                available_chips = player_stacks[player_name] - player_bets[player_name]
                if additional_amount > available_chips:
                    return (
                        jsonify(
                            {
                                "error": f"{player_name} cannot bet ${total_bet} (only ${available_chips} additional available)"
                            }
                        ),
                        400,
                    )

                player_bets[player_name] = total_bet
                current_bet = max(current_bet, total_bet)
                builder.add_action(player_name, action_type, amount)
                processed_action = action.copy()
                processed_action["street"] = street
                processed_actions.append(processed_action)

            else:  # fold, check
                builder.add_action(player_name, action_type, amount)
                processed_action = action.copy()
                processed_action["street"] = street
                processed_actions.append(processed_action)

        # Set board cards
        if "flop" in data:
            builder.deal_flop(data["flop"])
        if "turn" in data:
            builder.deal_turn(data["turn"])
        if "river" in data:
            builder.deal_river(data["river"])

        # Generate PHH
        phh_content = builder.generate_phh()

        # Save to database
        hand = Hand(
            play_id=play_id,
            game_type=data.get("game_type", "No Limit Texas Holdem"),
            board=data.get("board", ""),
            small_blind=data.get("small_blind", 1.0),
            big_blind=data.get("big_blind", 2.0),
            phh_content=phh_content,
        )

        db.session.add(hand)
        db.session.flush()  # Get ID

        # Save player information with position strings
        position_mapping = ["SB", "BB", "UTG", "UTG1", "MP", "LJ", "HJ", "CO", "BTN"]
        for i, player_data in enumerate(players_data):
            # Use position string if within range, otherwise fall back to position number
            position = position_mapping[i] if i < len(position_mapping) else f"P{i}"
            player = Player(
                hand_id=hand.id,
                name=player_data["name"],
                stack=player_data["stack"],
                hole_cards=data.get("hole_cards", {}).get(player_data["name"], ""),
                position=position,
            )
            db.session.add(player)

        # Save action information with corrected amounts
        for i, action_data in enumerate(processed_actions):
            action = Action(
                hand_id=hand.id,
                street=action_data.get("street", "preflop"),
                player_name=action_data["player_name"],
                action_type=action_data["action_type"],
                amount=action_data.get("amount", 0),
                pot_size=action_data.get("pot_size", 0.0),
                remaining_stack=action_data.get("remaining_stack", 0.0),
                action_order=i,
            )
            db.session.add(action)

        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "hand_id": hand.id,
                "play_id": play_id,
                "phh_content": phh_content,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-sample", methods=["POST"])
def create_sample():
    """Create a sample hand"""
    try:
        # Create sample hand data in the format expected by save_hand
        sample_hand_data = {
            "play_id": str(uuid.uuid4()),
            "players": [
                {"name": "Alice", "stack": 100.0},
                {"name": "Bob", "stack": 100.0},
                {"name": "Charlie", "stack": 150.0},
            ],
            "actions": [
                {
                    "player_name": "Charlie",
                    "action_type": "fold",
                    "street": "preflop",
                    "pot_size": 3.0,
                    "remaining_stack": 150.0,
                },
                {
                    "player_name": "Alice",
                    "action_type": "raise",
                    "amount": 6.0,
                    "street": "preflop",
                    "pot_size": 9.0,
                    "remaining_stack": 94.0,
                },
                {
                    "player_name": "Bob",
                    "action_type": "call",
                    "street": "preflop",
                    "pot_size": 15.0,
                    "remaining_stack": 94.0,
                },
                {
                    "player_name": "Alice",
                    "action_type": "bet",
                    "amount": 8.0,
                    "street": "flop",
                    "pot_size": 23.0,
                    "remaining_stack": 86.0,
                },
                {
                    "player_name": "Bob",
                    "action_type": "fold",
                    "street": "flop",
                    "pot_size": 23.0,
                    "remaining_stack": 94.0,
                },
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
            "hole_cards": {"Alice": "AsKh", "Bob": "QdQc", "Charlie": "7s2h"},
            "flop": "AhKd5c",
        }

        # Use the same validation logic as save_hand
        # This will automatically calculate correct call amounts
        data = sample_hand_data

        # Validate maximum number of players
        players_data = data["players"]
        if len(players_data) >= 10:
            return jsonify({"error": "Maximum of 9 players allowed"}), 400

        play_id = data.get("play_id", str(uuid.uuid4()))

        # Build hand with PokerKit
        builder = PokerHandBuilder()

        builder.create_game(
            players=players_data,
            small_blind=data.get("small_blind", 1.0),
            big_blind=data.get("big_blind", 2.0),
        )

        # Set hole cards
        if "hole_cards" in data:
            builder.deal_hole_cards(data["hole_cards"])

        # Validate and process actions (same logic as save_hand)
        player_stacks = {p["name"]: p["stack"] for p in players_data}
        current_bet = data.get("big_blind", 2.0)
        player_bets = {p["name"]: 0 for p in players_data}
        processed_actions = []

        # Set initial blinds
        if len(players_data) >= 2:
            player_bets[players_data[0]["name"]] = data.get("small_blind", 1.0)
            player_bets[players_data[1]["name"]] = data.get("big_blind", 2.0)

        for action in data["actions"]:
            player_name = action["player_name"]
            action_type = action["action_type"]
            amount = action.get("amount", 0)
            street = action.get("street", "preflop")  # Get street from action data

            if action_type == "call":
                call_amount = max(0, current_bet - player_bets[player_name])
                available_chips = player_stacks[player_name] - player_bets[player_name]
                actual_amount = min(call_amount, available_chips)
                player_bets[player_name] += actual_amount
                builder.add_action(player_name, action_type, actual_amount)
                processed_action = action.copy()
                processed_action["amount"] = actual_amount
                processed_action["street"] = street
                processed_actions.append(processed_action)

            elif action_type in ["bet", "raise"]:
                total_bet = amount
                additional_amount = total_bet - player_bets[player_name]
                available_chips = player_stacks[player_name] - player_bets[player_name]
                if additional_amount > available_chips:
                    return (
                        jsonify(
                            {
                                "error": f"{player_name} cannot bet ${total_bet} (only ${available_chips} additional available)"
                            }
                        ),
                        400,
                    )

                player_bets[player_name] = total_bet
                current_bet = max(current_bet, total_bet)
                builder.add_action(player_name, action_type, amount)
                processed_action = action.copy()
                processed_action["street"] = street
                processed_actions.append(processed_action)

            else:  # fold, check
                builder.add_action(player_name, action_type, amount)
                processed_action = action.copy()
                processed_action["street"] = street
                processed_actions.append(processed_action)

        # Set board cards
        if "flop" in data:
            builder.deal_flop(data["flop"])

        # Generate PHH
        phh_content = builder.generate_phh()

        # Save to database
        hand = Hand(
            play_id=play_id,
            game_type="No Limit Texas Holdem",
            board="AhKd5c",
            small_blind=1.0,
            big_blind=2.0,
            phh_content=phh_content,
        )

        db.session.add(hand)
        db.session.flush()

        # Save player information with position strings
        position_mapping = ["SB", "BB", "UTG", "UTG1", "MP", "LJ", "HJ", "CO", "BTN"]
        for i, player_data in enumerate(players_data):
            # Use position string if within range, otherwise fall back to position number
            position = position_mapping[i] if i < len(position_mapping) else f"P{i}"
            player = Player(
                hand_id=hand.id,
                name=player_data["name"],
                stack=player_data["stack"],
                hole_cards=data.get("hole_cards", {}).get(player_data["name"], ""),
                position=position,
            )
            db.session.add(player)

        # Save action information with corrected amounts
        for i, action_data in enumerate(processed_actions):
            action = Action(
                hand_id=hand.id,
                street=action_data.get("street", "preflop"),
                player_name=action_data["player_name"],
                action_type=action_data["action_type"],
                amount=action_data.get("amount", 0),
                pot_size=action_data.get("pot_size", 0.0),
                remaining_stack=action_data.get("remaining_stack", 0.0),
                action_order=i,
            )
            db.session.add(action)

        db.session.commit()

        return jsonify({"status": "success", "hand_id": hand.id, "play_id": play_id})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/hands")
def list_hands():
    """Get list of saved hands"""
    hands = Hand.query.order_by(Hand.created_at.desc()).all()

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        return render_template("hands_list.html", hands=hands)

    # Return JSON for normal API requests
    return jsonify(
        [
            {
                "id": hand.id,
                "play_id": hand.play_id,
                "game_type": hand.game_type,
                "created_at": hand.created_at.isoformat(),
            }
            for hand in hands
        ]
    )


@app.route("/api/hands/<play_id>")
def get_hand(play_id):
    """Get specific hand details"""
    hand = Hand.query.filter_by(play_id=play_id).first()
    if not hand:
        return jsonify({"error": "Hand not found"}), 404

    players = Player.query.filter_by(hand_id=hand.id).all()
    actions = (
        Action.query.filter_by(hand_id=hand.id).order_by(Action.action_order).all()
    )

    return jsonify(
        {
            "hand": {
                "id": hand.id,
                "play_id": hand.play_id,
                "game_type": hand.game_type,
                "board": hand.board,
                "phh_content": hand.phh_content,
                "created_at": hand.created_at.isoformat(),
            },
            "players": [
                {
                    "name": p.name,
                    "stack": p.stack,
                    "hole_cards": p.hole_cards,
                    "position": p.position,
                }
                for p in players
            ],
            "actions": [
                {
                    "street": a.street,
                    "player_name": a.player_name,
                    "action_type": a.action_type,
                    "amount": a.amount,
                    "action_order": a.action_order,
                }
                for a in actions
            ],
        }
    )


@app.route("/api/hands/<play_id>/details")
def get_hand_details_html(play_id):
    """Get specific hand details as HTML for modal display"""
    hand = Hand.query.filter_by(play_id=play_id).first()
    if not hand:
        return '<div class="text-red-500">Hand not found</div>', 404

    players = Player.query.filter_by(hand_id=hand.id).order_by(Player.position).all()
    actions = (
        Action.query.filter_by(hand_id=hand.id).order_by(Action.action_order).all()
    )

    return render_template(
        "hand_detail.html",
        hand=hand,
        players=players,
        actions=actions,
        Position=Position,
    )


@app.route("/api/hands/<play_id>/replay-ui")
def get_hand_replay_ui(play_id):
    """Get hand replay UI as HTML for modal display"""
    hand = Hand.query.filter_by(play_id=play_id).first()
    if not hand:
        return '<div class="text-red-500">Hand not found</div>', 404

    return render_template("hand_replay.html", hand=hand)


@app.route("/api/hands/<play_id>/replay")
def get_hand_replay(play_id):
    """Get hand replay data with step-by-step progression"""
    hand = Hand.query.filter_by(play_id=play_id).first()
    if not hand:
        return jsonify({"error": "Hand not found"}), 404

    players = Player.query.filter_by(hand_id=hand.id).all()
    actions = (
        Action.query.filter_by(hand_id=hand.id).order_by(Action.action_order).all()
    )

    # Build replay steps with proper state tracking
    replay_steps = []

    # Initialize player state tracking
    player_state = {}
    for p in players:
        player_state[p.name] = {
            "name": p.name,
            "original_stack": p.stack,
            "current_stack": p.stack,
            "hole_cards": p.hole_cards,
            "position": p.position,
            "current_bet": 0,
            "total_invested": 0,
            "is_active": True,
            "has_folded": False,
        }

    current_pot = 0
    current_street = "preflop"
    board_cards = []

    # Step 0: Initial game state
    initial_state = {
        "step": 0,
        "description": "Hand begins",
        "street": "preflop",
        "players": [
            {
                "name": state["name"],
                "stack": state["current_stack"],
                "hole_cards": state["hole_cards"],
                "position": state["position"],
                "current_bet": state["current_bet"],
                "is_active": state["is_active"],
            }
            for state in player_state.values()
        ],
        "pot_size": current_pot,
        "board": board_cards.copy(),
        "current_bet": 0,
        "action": None,
    }
    replay_steps.append(initial_state)

    # Step 1: Post blinds
    if len(players) >= 2:
        sb_player = next((p for p in players if p.position == "SB"), None)
        bb_player = next((p for p in players if p.position == "BB"), None)

        if sb_player:
            player_state[sb_player.name]["current_stack"] -= hand.small_blind
            player_state[sb_player.name]["current_bet"] = hand.small_blind
            player_state[sb_player.name]["total_invested"] = hand.small_blind
            current_pot += hand.small_blind

        if bb_player:
            player_state[bb_player.name]["current_stack"] -= hand.big_blind
            player_state[bb_player.name]["current_bet"] = hand.big_blind
            player_state[bb_player.name]["total_invested"] = hand.big_blind
            current_pot += hand.big_blind

        blinds_state = {
            "step": 1,
            "description": f"Blinds posted: {sb_player.name if sb_player else 'SB'} (${hand.small_blind}), {bb_player.name if bb_player else 'BB'} (${hand.big_blind})",
            "street": "preflop",
            "players": [
                {
                    "name": state["name"],
                    "stack": state["current_stack"],
                    "hole_cards": state["hole_cards"],
                    "position": state["position"],
                    "current_bet": state["current_bet"],
                    "is_active": state["is_active"],
                }
                for state in player_state.values()
            ],
            "pot_size": current_pot,
            "board": board_cards.copy(),
            "current_bet": hand.big_blind,
            "action": {"type": "blinds", "description": "Blinds posted"},
        }
        replay_steps.append(blinds_state)

    # Add each action as a step
    current_step = len(replay_steps)
    for action in actions:
        # Update board cards when street changes
        if action.street != current_street:
            current_street = action.street
            if hand.board:
                board_parts = hand.board.split()
                if action.street == "flop" and len(board_parts) >= 3:
                    board_cards = board_parts[:3]
                elif action.street == "turn" and len(board_parts) >= 4:
                    board_cards = board_parts[:4]
                elif action.street == "river" and len(board_parts) >= 5:
                    board_cards = board_parts[:5]

            # Reset current bets for new street
            for state in player_state.values():
                state["current_bet"] = 0

        # Process the action
        player_name = action.player_name
        if player_name in player_state:
            if action.action_type == "fold":
                player_state[player_name]["is_active"] = False
                player_state[player_name]["has_folded"] = True
                player_state[player_name]["current_bet"] = 0
            elif action.action_type in ["bet", "raise"]:
                additional_bet = (
                    action.amount - player_state[player_name]["current_bet"]
                )
                player_state[player_name]["current_stack"] -= additional_bet
                player_state[player_name]["current_bet"] = action.amount
                player_state[player_name]["total_invested"] += additional_bet
                current_pot += additional_bet
            elif action.action_type == "call":
                player_state[player_name]["current_stack"] -= action.amount
                player_state[player_name]["current_bet"] += action.amount
                player_state[player_name]["total_invested"] += action.amount
                current_pot += action.amount
            elif action.action_type == "check":
                # No money changes on check
                pass

        action_state = {
            "step": current_step,
            "description": f"{action.player_name} {action.action_type}"
            + (f" ${action.amount}" if action.amount > 0 else ""),
            "street": action.street,
            "players": [
                {
                    "name": state["name"],
                    "stack": state["current_stack"],
                    "hole_cards": state["hole_cards"],
                    "position": state["position"],
                    "current_bet": state["current_bet"],
                    "is_active": state["is_active"],
                }
                for state in player_state.values()
            ],
            "pot_size": current_pot,
            "board": board_cards.copy(),
            "current_bet": max(
                state["current_bet"]
                for state in player_state.values()
                if state["is_active"]
            )
            if any(state["is_active"] for state in player_state.values())
            else 0,
            "action": {
                "player": action.player_name,
                "type": action.action_type,
                "amount": action.amount,
                "street": action.street,
            },
        }
        replay_steps.append(action_state)
        current_step += 1

    return jsonify(
        {
            "hand_id": hand.play_id,
            "total_steps": len(replay_steps),
            "steps": replay_steps,
            "meta": {
                "game_type": hand.game_type,
                "small_blind": hand.small_blind,
                "big_blind": hand.big_blind,
                "board": hand.board,
                "created_at": hand.created_at.isoformat(),
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
