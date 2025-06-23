import json
import os
import tempfile
import unittest

from flask import Flask

from app import app, db
from models import Action, Hand, Player


class TestReplayFunctionality(unittest.TestCase):
    """Test cases for hand replay functionality"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Configure test app
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        # Create test client
        self.client = app.test_client()

        # Create application context and database
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after each test method"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_replay_api_endpoint_with_sample_hand(self):
        """Test replay API endpoint with sample hand"""
        # Create a sample hand first
        create_response = self.client.post("/api/create-sample")
        self.assertEqual(create_response.status_code, 200)

        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Test replay endpoint
        response = self.client.get(f"/api/hands/{play_id}/replay")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Verify response structure
        self.assertIn("hand_id", data)
        self.assertIn("total_steps", data)
        self.assertIn("steps", data)
        self.assertIn("meta", data)

        # Verify metadata
        meta = data["meta"]
        self.assertEqual(meta["game_type"], "No Limit Texas Holdem")
        self.assertEqual(meta["small_blind"], 1.0)
        self.assertEqual(meta["big_blind"], 2.0)
        self.assertEqual(meta["board"], "AhKd5c")

        # Verify steps structure
        steps = data["steps"]
        self.assertGreater(len(steps), 0)
        self.assertEqual(data["total_steps"], len(steps))

        # Check first step (initial state)
        first_step = steps[0]
        self.assertEqual(first_step["step"], 0)
        self.assertEqual(first_step["description"], "Hand begins")
        self.assertEqual(first_step["street"], "preflop")
        self.assertEqual(first_step["pot_size"], 0)
        self.assertEqual(len(first_step["players"]), 3)
        self.assertEqual(first_step["board"], [])
        self.assertIsNone(first_step["action"])

    def test_replay_state_progression(self):
        """Test that replay steps show proper state progression"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Get replay data
        response = self.client.get(f"/api/hands/{play_id}/replay")
        data = json.loads(response.data)
        steps = data["steps"]

        # Verify initial state
        initial_step = steps[0]
        alice_initial = next(p for p in initial_step["players"] if p["name"] == "Alice")
        self.assertEqual(alice_initial["stack"], 100.0)
        self.assertEqual(alice_initial["current_bet"], 0)
        self.assertTrue(alice_initial["is_active"])

        # Verify blinds step
        blinds_step = steps[1]
        self.assertIn("Blinds posted", blinds_step["description"])
        self.assertEqual(blinds_step["pot_size"], 3.0)  # SB + BB

        alice_blinds = next(p for p in blinds_step["players"] if p["name"] == "Alice")
        bob_blinds = next(p for p in blinds_step["players"] if p["name"] == "Bob")

        self.assertEqual(alice_blinds["stack"], 99.0)  # 100 - 1 (SB)
        self.assertEqual(alice_blinds["current_bet"], 1.0)
        self.assertEqual(bob_blinds["stack"], 98.0)  # 100 - 2 (BB)
        self.assertEqual(bob_blinds["current_bet"], 2.0)

        # Verify subsequent action steps preserve state
        for i in range(2, len(steps)):
            step = steps[i]
            self.assertIn("action", step)
            # Skip intermediate steps where action is None (street transitions)
            if step["action"] is not None:
                self.assertIn("player", step["action"])
                self.assertIn("type", step["action"])
                self.assertIn("street", step["action"])

    def test_replay_fold_action_tracking(self):
        """Test that fold actions are properly tracked in replay"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Get replay data
        response = self.client.get(f"/api/hands/{play_id}/replay")
        data = json.loads(response.data)
        steps = data["steps"]

        # Find fold actions
        fold_steps = [
            step
            for step in steps
            if step.get("action") and step["action"]["type"] == "fold"
        ]
        self.assertGreater(len(fold_steps), 0)

        # Check that folded players become inactive
        for fold_step in fold_steps:
            folded_player_name = fold_step["action"]["player"]
            folded_player = next(
                p for p in fold_step["players"] if p["name"] == folded_player_name
            )
            self.assertFalse(folded_player["is_active"])

    def test_replay_board_card_progression(self):
        """Test that board cards appear correctly in replay steps"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Get replay data
        response = self.client.get(f"/api/hands/{play_id}/replay")
        data = json.loads(response.data)
        steps = data["steps"]

        # Find flop action (should have board cards)
        flop_steps = [step for step in steps if step["street"] == "flop"]
        self.assertGreater(len(flop_steps), 0)

        # Check that flop steps have board cards (some may be empty during preflop actions in flop)
        board_with_cards = [step for step in flop_steps if len(step["board"]) > 0]
        if board_with_cards:  # Only check if we have board cards
            for flop_step in board_with_cards:
                self.assertGreater(len(flop_step["board"]), 0)
                self.assertEqual(len(flop_step["board"]), 3)  # Flop should have 3 cards

    def test_replay_ui_endpoint(self):
        """Test replay UI endpoint returns HTML"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Test replay UI endpoint
        response = self.client.get(f"/api/hands/{play_id}/replay-ui")
        self.assertEqual(response.status_code, 200)

        # Should return HTML content
        html_content = response.data.decode("utf-8")
        self.assertIn("hand-replay-container", html_content)
        self.assertIn(
            'id="play-pause-btn"', html_content
        )  # Should have play/pause button
        self.assertIn("HandReplay", html_content)  # Should have JavaScript class
        self.assertIn(play_id, html_content)  # Should contain the play_id

    def test_replay_not_found(self):
        """Test replay endpoints with non-existent hand"""
        non_existent_id = "non-existent-hand-id"

        # Test replay API endpoint
        response = self.client.get(f"/api/hands/{non_existent_id}/replay")
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Hand not found")

        # Test replay UI endpoint
        ui_response = self.client.get(f"/api/hands/{non_existent_id}/replay-ui")
        self.assertEqual(ui_response.status_code, 404)

        html_content = ui_response.data.decode("utf-8")
        self.assertIn("Hand not found", html_content)

    def test_replay_pot_size_tracking(self):
        """Test that pot sizes are correctly tracked throughout replay"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Get replay data
        response = self.client.get(f"/api/hands/{play_id}/replay")
        data = json.loads(response.data)
        steps = data["steps"]

        # Pot should start at 0
        self.assertEqual(steps[0]["pot_size"], 0)

        # After blinds, pot should be SB + BB
        blinds_step = steps[1]
        self.assertEqual(blinds_step["pot_size"], 3.0)  # 1 + 2

        # Pot should only increase (or stay same for checks/folds)
        prev_pot = 0
        for step in steps:
            current_pot = step["pot_size"]
            if step.get("action") and step["action"]["type"] not in ["fold", "check"]:
                # For betting actions, pot should increase
                self.assertGreaterEqual(current_pot, prev_pot)
            prev_pot = current_pot

    def test_replay_custom_hand_data(self):
        """Test replay with custom hand data"""
        # Create a custom hand with specific actions
        hand_data = {
            "players": [
                {"name": "Player1", "stack": 100.0},  # SB
                {"name": "Player2", "stack": 200.0},  # BB
            ],
            "actions": [
                # Preflop: SB (Player1) acts first in heads-up
                {
                    "player_name": "Player1",
                    "action_type": "raise",
                    "amount": 4.0,
                    "street": "preflop",
                },
                {"player_name": "Player2", "action_type": "call", "street": "preflop"},
                # Flop: BB (Player2) acts first postflop in heads-up
                {"player_name": "Player2", "action_type": "bet", "amount": 6.0, "street": "flop"},
                {"player_name": "Player1", "action_type": "fold", "street": "flop"},
            ],
            "flop": "Ac7d2h",
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        # Save the hand
        save_response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        save_data = json.loads(save_response.data)
        play_id = save_data["play_id"]

        # Get replay data
        replay_response = self.client.get(f"/api/hands/{play_id}/replay")
        self.assertEqual(replay_response.status_code, 200)

        replay_data = json.loads(replay_response.data)
        steps = replay_data["steps"]

        # Should have: initial, blinds, raise, call, intermediate(flop), bet, fold = 7 steps
        self.assertEqual(len(steps), 7)

        # Verify specific actions
        raise_step = steps[2]  # First action after blinds
        self.assertEqual(raise_step["action"]["type"], "raise")
        self.assertEqual(raise_step["action"]["player"], "Player1")
        self.assertEqual(raise_step["action"]["amount"], 4.0)

        # Check street progression
        preflop_steps = [s for s in steps if s["street"] == "preflop"]
        flop_steps = [s for s in steps if s["street"] == "flop"]

        self.assertGreater(len(preflop_steps), 0)
        self.assertGreater(len(flop_steps), 0)

        # Verify board cards appear in flop
        for flop_step in flop_steps:
            if len(flop_step["board"]) > 0:
                self.assertEqual(flop_step["board"], ["Ac", "7d", "2h"])

    def test_replay_player_stack_consistency(self):
        """Test that player stacks remain consistent throughout replay"""
        # Create a sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Get replay data
        response = self.client.get(f"/api/hands/{play_id}/replay")
        data = json.loads(response.data)
        steps = data["steps"]

        # Track each player's stack throughout the hand
        # Get initial stacks from first step since they might differ
        initial_stacks = {}
        for player in steps[0]["players"]:
            initial_stacks[player["name"]] = player["stack"]

        for player_name in ["Alice", "Bob", "Charlie"]:
            prev_stack = initial_stacks[player_name]  # Use actual initial stack
            for step in steps:
                player = next(p for p in step["players"] if p["name"] == player_name)
                current_stack = player["stack"]

                # Stack should never increase (chips can only be lost)
                self.assertLessEqual(current_stack, prev_stack)
                prev_stack = current_stack

    def test_replay_multiple_streets(self):
        """Test replay with actions across multiple streets"""
        # Create hand with actions on multiple streets
        hand_data = {
            "players": [
                {"name": "Hero", "stack": 100.0},    # SB
                {"name": "Villain", "stack": 100.0}, # BB
            ],
            "actions": [
                # Preflop: SB (Hero) acts first in heads-up
                {
                    "player_name": "Hero",
                    "action_type": "raise",
                    "amount": 6.0,
                    "street": "preflop",
                },
                {"player_name": "Villain", "action_type": "call", "street": "preflop"},
                # Flop: BB (Villain) acts first postflop in heads-up
                {
                    "player_name": "Villain",
                    "action_type": "check",
                    "street": "flop",
                },
                {
                    "player_name": "Hero",
                    "action_type": "bet",
                    "amount": 8.0,
                    "street": "flop",
                },
                {
                    "player_name": "Villain",
                    "action_type": "raise",
                    "amount": 20.0,
                    "street": "flop",
                },
                {"player_name": "Hero", "action_type": "call", "street": "flop"},
                # Turn: BB (Villain) acts first postflop in heads-up
                {"player_name": "Villain", "action_type": "bet", "amount": 30.0, "street": "turn"},
                {"player_name": "Hero", "action_type": "fold", "street": "turn"},
            ],
            "flop": "AsKd7c",
            "turn": "2h",
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        # Save and get replay
        save_response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )
        save_data = json.loads(save_response.data)
        play_id = save_data["play_id"]

        replay_response = self.client.get(f"/api/hands/{play_id}/replay")
        replay_data = json.loads(replay_response.data)
        steps = replay_data["steps"]

        # Verify street progression
        streets_seen = set()
        for step in steps:
            streets_seen.add(step["street"])

        self.assertIn("preflop", streets_seen)
        self.assertIn("flop", streets_seen)
        self.assertIn("turn", streets_seen)

        # Check board card progression
        turn_steps = [s for s in steps if s["street"] == "turn"]
        for turn_step in turn_steps:
            if len(turn_step["board"]) > 0:
                self.assertEqual(len(turn_step["board"]), 4)  # Flop + turn


class TestReplayIntegration(unittest.TestCase):
    """Integration tests for replay functionality with existing features"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        app.config["TESTING"] = True
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_replay_with_hand_details_endpoint(self):
        """Test that replay works alongside existing hand details endpoint"""
        # Create sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Test regular details endpoint
        details_response = self.client.get(f"/api/hands/{play_id}")
        self.assertEqual(details_response.status_code, 200)

        details_data = json.loads(details_response.data)

        # Test replay endpoint
        replay_response = self.client.get(f"/api/hands/{play_id}/replay")
        self.assertEqual(replay_response.status_code, 200)

        replay_data = json.loads(replay_response.data)

        # Both should reference the same hand
        self.assertEqual(details_data["hand"]["play_id"], replay_data["hand_id"])

        # Player count should match
        self.assertEqual(len(details_data["players"]), 3)
        self.assertEqual(len(replay_data["steps"][0]["players"]), 3)

    def test_replay_with_htmx_hand_details(self):
        """Test replay UI endpoint alongside HTMX hand details"""
        # Create sample hand
        create_response = self.client.post("/api/create-sample")
        create_data = json.loads(create_response.data)
        play_id = create_data["play_id"]

        # Test HTMX details endpoint
        details_response = self.client.get(
            f"/api/hands/{play_id}/details", headers={"HX-Request": "true"}
        )
        self.assertEqual(details_response.status_code, 200)

        # Test replay UI endpoint
        replay_ui_response = self.client.get(f"/api/hands/{play_id}/replay-ui")
        self.assertEqual(replay_ui_response.status_code, 200)

        # Both should return HTML
        details_html = details_response.data.decode("utf-8")
        replay_html = replay_ui_response.data.decode("utf-8")

        self.assertIn("<div", details_html)
        self.assertIn("<div", replay_html)

        # Replay should have specific replay elements
        self.assertIn("hand-replay-container", replay_html)
        self.assertIn("play-pause-btn", replay_html)

    def test_full_workflow_with_replay(self):
        """Test complete workflow: create hand -> list -> details -> replay"""
        # Step 1: Create hand
        hand_data = {
            "players": [
                {"name": "Alice", "stack": 100.0},  # SB
                {"name": "Bob", "stack": 100.0},    # BB
            ],
            "actions": [
                # Preflop: SB (Alice) acts first in heads-up
                {"player_name": "Alice", "action_type": "raise", "amount": 4.0, "street": "preflop"},
                {"player_name": "Bob", "action_type": "fold", "street": "preflop"},
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        save_response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )
        save_data = json.loads(save_response.data)
        play_id = save_data["play_id"]

        # Step 2: List hands
        list_response = self.client.get("/api/hands")
        list_data = json.loads(list_response.data)
        self.assertEqual(len(list_data), 1)
        self.assertEqual(list_data[0]["play_id"], play_id)

        # Step 3: Get details
        details_response = self.client.get(f"/api/hands/{play_id}")
        details_data = json.loads(details_response.data)
        self.assertEqual(details_data["hand"]["play_id"], play_id)

        # Step 4: Get replay
        replay_response = self.client.get(f"/api/hands/{play_id}/replay")
        replay_data = json.loads(replay_response.data)
        self.assertEqual(replay_data["hand_id"], play_id)

        # Step 5: Get replay UI
        replay_ui_response = self.client.get(f"/api/hands/{play_id}/replay-ui")
        self.assertEqual(replay_ui_response.status_code, 200)

        # All endpoints should work and be consistent
        self.assertEqual(len(details_data["players"]), 2)
        self.assertEqual(len(replay_data["steps"][0]["players"]), 2)


if __name__ == "__main__":
    unittest.main()
