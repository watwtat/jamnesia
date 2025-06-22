import uuid
from datetime import datetime
from typing import Any, Dict, List


class PokerHandBuilder:
    """Class to build poker hands and generate PHH"""

    def __init__(self):
        self.hand_data = {}

    def create_game(
        self,
        players: List[Dict[str, Any]],
        small_blind: float = 1.0,
        big_blind: float = 2.0,
    ) -> None:
        """Create a new game"""

        self.hand_data = {
            "players": players,
            "small_blind": small_blind,
            "big_blind": big_blind,
            "actions": [],
            "hole_cards": {},
            "board_cards": [],
        }

    def deal_hole_cards(self, hole_cards: Dict[str, str]) -> None:
        """Deal hole cards"""
        self.hand_data["hole_cards"] = hole_cards

    def add_action(self, player_name: str, action_type: str, amount: float = 0) -> None:
        """Add an action"""
        action_data = {
            "player_name": player_name,
            "action_type": action_type,
            "amount": amount,
            "street": self._get_current_street(),
        }
        self.hand_data["actions"].append(action_data)

    def deal_flop(self, cards: str) -> None:
        """Deal the flop"""
        self.hand_data["flop"] = cards
        self.hand_data["board_cards"].extend([cards[i : i + 2] for i in range(0, 6, 2)])

    def deal_turn(self, card: str) -> None:
        """Deal the turn"""
        self.hand_data["turn"] = card
        self.hand_data["board_cards"].append(card)

    def deal_river(self, card: str) -> None:
        """Deal the river"""
        self.hand_data["river"] = card
        self.hand_data["board_cards"].append(card)

    def generate_phh(self) -> str:
        """Generate PHH format string"""
        phh_lines = []

        # Handle case where game wasn't created
        if not self.hand_data:
            return 'variant = "NLHE"'

        # Get player count and blinds
        players = self.hand_data.get("players", [])
        player_count = len(players)
        small_blind = self.hand_data.get("small_blind", 1.0)
        big_blind = self.hand_data.get("big_blind", 2.0)

        # Header
        phh_lines.append('variant = "NLHE"')
        phh_lines.append(f"ante_trimming_status = true")
        phh_lines.append(f"antes = [{', '.join(['0'] * player_count)}]")

        # Handle blinds based on player count
        if player_count == 0:
            blinds_list = []
        elif player_count == 1:
            blinds_list = [str(int(small_blind))]
        else:
            blinds_list = [str(int(small_blind)), str(int(big_blind))]
            blinds_list.extend(["0"] * (player_count - 2))

        phh_lines.append(f"blinds_or_straddles = [{', '.join(blinds_list)}]")
        phh_lines.append(f"min_bet = {int(big_blind)}")

        # Starting stacks
        stacks = [str(int(p["stack"])) for p in players]
        phh_lines.append(f"starting_stacks = [{', '.join(stacks)}]")

        # Actions section
        phh_lines.append("")
        phh_lines.append("# Actions")

        # Hole cards
        hole_cards = self.hand_data.get("hole_cards", {})
        if hole_cards:
            for i, player in enumerate(players):
                if player["name"] in hole_cards:
                    cards = hole_cards[player["name"]]
                    phh_lines.append(f"d dh p{i} {cards}")

        # Board cards
        if "flop" in self.hand_data:
            flop = self.hand_data["flop"]
            phh_lines.append(f"d db {flop}")
        if "turn" in self.hand_data:
            turn = self.hand_data["turn"]
            phh_lines.append(f"d db {turn}")
        if "river" in self.hand_data:
            river = self.hand_data["river"]
            phh_lines.append(f"d db {river}")

        # Player actions
        actions = self.hand_data.get("actions", [])
        for action in actions:
            player_idx = self._get_player_index(action["player_name"])
            action_type = action["action_type"]
            amount = action.get("amount", 0)

            if action_type == "fold":
                phh_lines.append(f"p{player_idx} f")
            elif action_type == "check":
                phh_lines.append(f"p{player_idx} cc")
            elif action_type == "call":
                phh_lines.append(f"p{player_idx} cc")
            elif action_type == "bet":
                phh_lines.append(f"p{player_idx} cbr {int(amount)}")
            elif action_type == "raise":
                phh_lines.append(f"p{player_idx} cbr {int(amount)}")

        return "\n".join(phh_lines)

    def _get_current_street(self) -> str:
        """Get current street"""
        if "river" in self.hand_data:
            return "river"
        elif "turn" in self.hand_data:
            return "turn"
        elif "flop" in self.hand_data:
            return "flop"
        else:
            return "preflop"

    def _get_player_index(self, player_name: str) -> int:
        """Get player index from player name"""
        players = self.hand_data.get("players", [])
        for i, player in enumerate(players):
            if player["name"] == player_name:
                return i
        raise ValueError(f"Player {player_name} not found")


def create_sample_hand() -> Dict[str, Any]:
    """Create a sample hand"""
    builder = PokerHandBuilder()

    # Player setup
    players = [
        {"name": "Alice", "stack": 100.0},
        {"name": "Bob", "stack": 100.0},
        {"name": "Charlie", "stack": 150.0},
    ]

    builder.create_game(players, small_blind=1.0, big_blind=2.0)

    # Deal hole cards
    hole_cards = {"Alice": "AsKh", "Bob": "QdQc", "Charlie": "7s2h"}
    builder.deal_hole_cards(hole_cards)

    # Preflop actions
    builder.add_action("Charlie", "fold")
    builder.add_action("Alice", "raise", 6.0)
    builder.add_action("Bob", "call")

    # Flop
    builder.deal_flop("AhKd5c")
    builder.add_action("Alice", "bet", 8.0)
    builder.add_action("Bob", "fold")

    return {
        "play_id": str(uuid.uuid4()),
        "phh_content": builder.generate_phh(),
        "hand_data": builder.hand_data,
    }
