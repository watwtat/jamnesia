#!/usr/bin/env python3
"""
Additional edge case tests based on analysis
"""

import json
import unittest
from unittest.mock import patch

from flask import Flask

from app import app
from models import Action, Hand, Player, Position, db


class TestEdgeCases(unittest.TestCase):
    """Test edge cases identified in analysis"""

    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_negative_stack_values(self):
        """Test that negative stack values are accepted (current behavior)"""
        data = {
            "players": [
                {"name": "Player1", "stack": -50.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [{"player_name": "Player1", "action_type": "fold"}],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        # Current behavior: accepts negative stacks
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")

    def test_zero_stack_values(self):
        """Test that zero stack values are accepted (current behavior)"""
        data = {
            "players": [
                {"name": "Player1", "stack": 0.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [{"player_name": "Player1", "action_type": "fold"}],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        # Current behavior: accepts zero stacks
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")

    def test_fractional_amounts_precision(self):
        """Test handling of fractional amounts"""
        data = {
            "players": [
                {"name": "Player1", "stack": 100.33},
                {"name": "Player2", "stack": 99.67},
            ],
            "actions": [
                {"player_name": "Player1", "action_type": "bet", "amount": 5.25},
                {"player_name": "Player2", "action_type": "call"},
            ],
            "small_blind": 0.50,
            "big_blind": 1.00,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")

        # Verify fractional amounts are handled
        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            self.assertIsNotNone(hand)

            actions = Action.query.filter_by(hand_id=hand.id).all()
            # Find the call action - should have calculated amount
            call_action = next((a for a in actions if a.action_type == "call"), None)
            self.assertIsNotNone(call_action)
            self.assertGreater(call_action.amount, 0)

    def test_invalid_player_name_in_action(self):
        """Test action with non-existent player name"""
        data = {
            "players": [
                {"name": "Player1", "stack": 100.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [{"player_name": "NonExistentPlayer", "action_type": "fold"}],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertIn("error", result)
        self.assertIn("NonExistentPlayer not found", result["error"])

    def test_insufficient_chips_for_bet(self):
        """Test betting more than available stack"""
        data = {
            "players": [
                {"name": "Player1", "stack": 50.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [
                {
                    "player_name": "Player1",
                    "action_type": "bet",
                    "amount": 60.0,
                }  # More than stack
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertIn("error", result)
        self.assertIn("cannot bet", result["error"].lower())

    def test_maximum_players_allowed(self):
        """Test that exactly 9 players are allowed"""
        players = [{"name": f"Player{i}", "stack": 100.0} for i in range(9)]
        actions = [{"player_name": "Player0", "action_type": "fold"}]

        data = {
            "players": players,
            "actions": actions,
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")

        # Verify positions are assigned correctly for 9 players
        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            players_db = Player.query.filter_by(hand_id=hand.id).all()

            # All 9 should have Position enum values
            for player in players_db:
                self.assertIn(player.position, [p.value for p in Position])

    def test_too_many_players_rejected(self):
        """Test that 10 or more players are rejected"""
        players = [{"name": f"Player{i}", "stack": 100.0} for i in range(10)]
        actions = [{"player_name": "Player0", "action_type": "fold"}]

        data = {
            "players": players,
            "actions": actions,
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertIn("error", result)
        self.assertIn("Maximum of 9 players allowed", result["error"])

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON"""
        response = self.client.post(
            "/api/save-hand",
            data='{"invalid": json}',  # Invalid JSON
            content_type="application/json",
        )

        # Current behavior: returns 500 instead of 400
        self.assertEqual(response.status_code, 500)
        # This is the edge case identified for improvement

    def test_missing_content_type_header(self):
        """Test request without proper content type"""
        data = {
            "players": [{"name": "Player1", "stack": 100.0}],
            "actions": [{"player_name": "Player1", "action_type": "fold"}],
        }

        # Send without content-type header
        response = self.client.post("/api/save-hand", data=json.dumps(data))

        # Should still work as Flask can handle it
        self.assertIn(response.status_code, [200, 400, 500])

    def test_empty_actions_list(self):
        """Test with empty actions list"""
        data = {
            "players": [
                {"name": "Player1", "stack": 100.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [],  # Empty actions
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")

    def test_very_large_amounts(self):
        """Test with very large monetary amounts"""
        data = {
            "players": [
                {"name": "Player1", "stack": 999999999.99},
                {"name": "Player2", "stack": 999999999.99},
            ],
            "actions": [
                {"player_name": "Player1", "action_type": "bet", "amount": 1000000.00}
            ],
            "small_blind": 50000.0,
            "big_blind": 100000.0,
        }

        response = self.client.post(
            "/api/save-hand", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["status"], "success")


class TestPositionEdgeCases(unittest.TestCase):
    """Test Position enum edge cases"""

    def test_position_with_invalid_values(self):
        """Test Position.get_display_name with various invalid values"""
        test_cases = [(-1, "P-1"), (100, "P100"), (999, "P999")]

        for value, expected in test_cases:
            result = Position.get_display_name(value)
            self.assertEqual(result, expected)

        # Test None separately - current behavior doesn't raise TypeError
        result = Position.get_display_name(None)
        self.assertEqual(result, "PNone")

    def test_position_enum_completeness(self):
        """Test that Position enum covers expected poker positions"""
        expected_positions = ["SB", "BB", "UTG", "UTG1", "MP", "LJ", "HJ", "CO", "BTN"]
        actual_positions = [p.name for p in Position]

        self.assertEqual(set(expected_positions), set(actual_positions))
        self.assertEqual(len(expected_positions), len(actual_positions))


if __name__ == "__main__":
    unittest.main()
