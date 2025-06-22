#!/usr/bin/env python3
"""
Test street detection functionality
"""

import json
import unittest

from flask import Flask

from app import app
from models import Action, Hand, Player, Position, db


class TestStreetDetection(unittest.TestCase):
    """Test street detection in actions"""

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

    def test_street_detection_in_sample_hand(self):
        """Test that sample hand has correct street information"""
        response = self.client.post("/api/create-sample", json={})

        self.assertEqual(response.status_code, 200)
        result = response.get_json()

        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            actions = (
                Action.query.filter_by(hand_id=hand.id)
                .order_by(Action.action_order)
                .all()
            )

            # Verify we have actions
            self.assertGreater(len(actions), 0)

            # Check street information
            expected_streets = ["preflop", "preflop", "preflop", "flop", "flop"]
            actual_streets = [action.street for action in actions]

            self.assertEqual(actual_streets, expected_streets)

    def test_street_detection_in_custom_hand(self):
        """Test street detection with custom hand data"""
        hand_data = {
            "players": [
                {"name": "Player1", "stack": 100.0},
                {"name": "Player2", "stack": 100.0},
                {"name": "Player3", "stack": 100.0},
            ],
            "actions": [
                {"player_name": "Player1", "action_type": "fold", "street": "preflop"},
                {"player_name": "Player2", "action_type": "call", "street": "preflop"},
                {"player_name": "Player3", "action_type": "check", "street": "preflop"},
                {
                    "player_name": "Player2",
                    "action_type": "bet",
                    "amount": 5.0,
                    "street": "flop",
                },
                {"player_name": "Player3", "action_type": "call", "street": "flop"},
                {
                    "player_name": "Player2",
                    "action_type": "bet",
                    "amount": 10.0,
                    "street": "turn",
                },
                {"player_name": "Player3", "action_type": "fold", "street": "turn"},
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
            "flop": "AsKhQd",
            "turn": "Jc",
        }

        response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()

        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            actions = (
                Action.query.filter_by(hand_id=hand.id)
                .order_by(Action.action_order)
                .all()
            )

            # Verify we have the correct number of actions
            self.assertEqual(len(actions), 7)

            # Check street information
            expected_streets = [
                "preflop",
                "preflop",
                "preflop",
                "flop",
                "flop",
                "turn",
                "turn",
            ]
            actual_streets = [action.street for action in actions]

            self.assertEqual(actual_streets, expected_streets)

    def test_street_defaults_to_preflop(self):
        """Test that actions without street specification default to preflop"""
        hand_data = {
            "players": [
                {"name": "Player1", "stack": 100.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [
                {
                    "player_name": "Player1",
                    "action_type": "fold",
                },  # No street specified
                {
                    "player_name": "Player2",
                    "action_type": "check",
                },  # No street specified
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
        }

        response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()

        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            actions = (
                Action.query.filter_by(hand_id=hand.id)
                .order_by(Action.action_order)
                .all()
            )

            # All actions should default to preflop
            for action in actions:
                self.assertEqual(action.street, "preflop")

    def test_mixed_street_scenarios(self):
        """Test various street scenarios"""
        hand_data = {
            "players": [
                {"name": "Player1", "stack": 100.0},
                {"name": "Player2", "stack": 100.0},
            ],
            "actions": [
                {"player_name": "Player1", "action_type": "call", "street": "preflop"},
                {"player_name": "Player2", "action_type": "check", "street": "preflop"},
                {
                    "player_name": "Player1",
                    "action_type": "bet",
                    "amount": 5.0,
                    "street": "flop",
                },
                {
                    "player_name": "Player2",
                    "action_type": "raise",
                    "amount": 15.0,
                    "street": "flop",
                },
                {"player_name": "Player1", "action_type": "call", "street": "flop"},
                {"player_name": "Player1", "action_type": "check", "street": "turn"},
                {
                    "player_name": "Player2",
                    "action_type": "bet",
                    "amount": 20.0,
                    "street": "turn",
                },
                {"player_name": "Player1", "action_type": "call", "street": "turn"},
                {"player_name": "Player1", "action_type": "check", "street": "river"},
                {"player_name": "Player2", "action_type": "check", "street": "river"},
            ],
            "small_blind": 1.0,
            "big_blind": 2.0,
            "flop": "AsKhQd",
            "turn": "Jc",
            "river": "2s",
        }

        response = self.client.post(
            "/api/save-hand",
            data=json.dumps(hand_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()

        with self.app.app_context():
            hand = Hand.query.filter_by(play_id=result["play_id"]).first()
            actions = (
                Action.query.filter_by(hand_id=hand.id)
                .order_by(Action.action_order)
                .all()
            )

            # Verify we have all actions
            self.assertEqual(len(actions), 10)

            # Check street progression
            expected_streets = [
                "preflop",
                "preflop",
                "flop",
                "flop",
                "flop",
                "turn",
                "turn",
                "turn",
                "river",
                "river",
            ]
            actual_streets = [action.street for action in actions]

            self.assertEqual(actual_streets, expected_streets)

            # Verify street distribution
            preflop_actions = [a for a in actions if a.street == "preflop"]
            flop_actions = [a for a in actions if a.street == "flop"]
            turn_actions = [a for a in actions if a.street == "turn"]
            river_actions = [a for a in actions if a.street == "river"]

            self.assertEqual(len(preflop_actions), 2)
            self.assertEqual(len(flop_actions), 3)
            self.assertEqual(len(turn_actions), 3)
            self.assertEqual(len(river_actions), 2)


if __name__ == "__main__":
    unittest.main()
