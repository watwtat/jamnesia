import unittest
from app import process_hand_actions, should_advance_street


class TestStreetProgression(unittest.TestCase):
    """Test cases for automatic street progression logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.players_data = [
            {"name": "Alice", "stack": 100},
            {"name": "Bob", "stack": 100},
            {"name": "Charlie", "stack": 100}
        ]
        
        self.small_blind = 1.0
        self.big_blind = 2.0

    def test_preflop_to_flop_progression(self):
        """Test automatic progression from preflop to flop"""
        actions = [
            {"player_name": "Charlie", "action_type": "call", "amount": 2},  # calls BB
            {"player_name": "Alice", "action_type": "call", "amount": 1},   # SB calls
            {"player_name": "Bob", "action_type": "check"}                  # BB checks
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # All actions should be marked as preflop since betting round completed
        streets = [action["street"] for action in result]
        self.assertEqual(len([s for s in streets if s == "preflop"]), 3)
        
        # Verify pot size calculation
        final_pot = result[-1]["pot_size"]
        self.assertEqual(final_pot, 6.0)  # 2 + 1 + 1 + 2 (SB + call + call + BB)

    def test_preflop_with_raise_to_flop(self):
        """Test preflop with raise progressing to flop"""
        actions = [
            {"player_name": "Charlie", "action_type": "raise", "amount": 6},
            {"player_name": "Alice", "action_type": "call", "amount": 6},
            {"player_name": "Bob", "action_type": "call", "amount": 6}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # All actions should be preflop
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))
        
        # Verify pot calculation with raise
        final_pot = result[-1]["pot_size"]
        expected_pot = self.small_blind + self.big_blind + 6 + 5 + 4  # blinds + raise + calls (additional amounts)
        self.assertEqual(final_pot, expected_pot)

    def test_multiple_street_progression(self):
        """Test progression through multiple streets"""
        actions = [
            # Preflop
            {"player_name": "Charlie", "action_type": "call", "amount": 2},
            {"player_name": "Alice", "action_type": "call", "amount": 1},
            {"player_name": "Bob", "action_type": "check"},
            # Should auto-progress to flop here
            {"player_name": "Alice", "action_type": "check"},
            {"player_name": "Bob", "action_type": "bet", "amount": 3},
            {"player_name": "Charlie", "action_type": "call", "amount": 3},
            {"player_name": "Alice", "action_type": "fold"},
            # Should auto-progress to turn here
            {"player_name": "Bob", "action_type": "check"},
            {"player_name": "Charlie", "action_type": "check"}
            # Should auto-progress to river here
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Check street progression
        streets = [action["street"] for action in result]
        self.assertIn("preflop", streets)
        self.assertIn("flop", streets)
        self.assertIn("turn", streets)
        
        # Verify the progression order
        preflop_count = len([s for s in streets if s == "preflop"])
        flop_count = len([s for s in streets if s == "flop"])
        turn_count = len([s for s in streets if s == "turn"])
        
        self.assertEqual(preflop_count, 3)  # 3 preflop actions
        self.assertEqual(flop_count, 4)     # 4 flop actions (check, bet, call, fold)
        self.assertEqual(turn_count, 2)     # 2 turn actions

    def test_fold_progression(self):
        """Test progression when players fold"""
        actions = [
            {"player_name": "Charlie", "action_type": "fold"},
            {"player_name": "Alice", "action_type": "call", "amount": 1},
            {"player_name": "Bob", "action_type": "check"}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # All should be preflop
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))
        
        # Check fold action
        fold_action = next(action for action in result if action["action_type"] == "fold")
        self.assertEqual(fold_action["player_name"], "Charlie")
        self.assertEqual(fold_action["amount"], 0)

    def test_all_fold_scenario(self):
        """Test when everyone folds except one player"""
        actions = [
            {"player_name": "Charlie", "action_type": "fold"},
            {"player_name": "Alice", "action_type": "fold"}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should all be preflop since hand ends
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))

    def test_missing_player_auto_fold(self):
        """Test that players without actions get auto-folded"""
        actions = [
            {"player_name": "Charlie", "action_type": "call", "amount": 2},
            {"player_name": "Alice", "action_type": "call", "amount": 1}
            # Bob (BB) is missing - should get auto-folded
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should have auto-fold for Bob
        player_names = [action["player_name"] for action in result]
        self.assertIn("Bob", player_names)
        
        # Check Bob's auto-fold action
        bob_action = next(action for action in result if action["player_name"] == "Bob")
        self.assertEqual(bob_action["action_type"], "fold")

    def test_should_advance_street_function(self):
        """Test the should_advance_street helper function"""
        active_players = {"Alice", "Bob"}
        folded_players = {"Charlie"}
        players_acted = {"Alice", "Bob"}
        player_bets = {"Alice": 5, "Bob": 5, "Charlie": 0}
        current_bet = 5
        
        # Should advance when all active players acted and bets are equal
        self.assertTrue(should_advance_street(active_players, folded_players, players_acted, player_bets, current_bet))
        
        # Should not advance when not all players have acted
        players_acted_incomplete = {"Alice"}
        self.assertFalse(should_advance_street(active_players, folded_players, players_acted_incomplete, player_bets, current_bet))
        
        # Should not advance when bets are not equal
        player_bets_unequal = {"Alice": 5, "Bob": 3, "Charlie": 0}
        self.assertFalse(should_advance_street(active_players, folded_players, players_acted, player_bets_unequal, current_bet))

    def test_check_scenario(self):
        """Test scenario with all checks"""
        actions = [
            # Preflop (skip to make it simpler)
            {"player_name": "Charlie", "action_type": "call", "amount": 2},
            {"player_name": "Alice", "action_type": "call", "amount": 1},
            {"player_name": "Bob", "action_type": "check"},
            # Flop - all check
            {"player_name": "Alice", "action_type": "check"},
            {"player_name": "Bob", "action_type": "check"},
            {"player_name": "Charlie", "action_type": "check"}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should have preflop and flop actions
        streets = [action["street"] for action in result]
        self.assertIn("preflop", streets)
        self.assertIn("flop", streets)
        
        # Check actions should have amount 0
        check_actions = [action for action in result if action["action_type"] == "check"]
        for check_action in check_actions:
            self.assertEqual(check_action["amount"], 0)

    def test_betting_validation(self):
        """Test betting validation and error scenarios"""
        # Test invalid check when there's a bet
        actions = [
            {"player_name": "Charlie", "action_type": "raise", "amount": 10},
            {"player_name": "Alice", "action_type": "check"}  # Should fail - can't check when there's a bet
        ]
        
        with self.assertRaises(ValueError) as cm:
            process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        self.assertIn("cannot check when there's a bet", str(cm.exception))

    def test_insufficient_chips(self):
        """Test behavior when player doesn't have enough chips"""
        # Create players with limited stacks
        limited_players = [
            {"name": "Alice", "stack": 5},
            {"name": "Bob", "stack": 5}
        ]
        
        actions = [
            {"player_name": "Bob", "action_type": "raise", "amount": 10}  # Wants to bet more than stack
        ]
        
        with self.assertRaises(ValueError) as cm:
            process_hand_actions(limited_players, actions, 1.0, 2.0)
        
        self.assertIn("cannot bet", str(cm.exception))

    def test_nonexistent_player(self):
        """Test error when referencing non-existent player"""
        actions = [
            {"player_name": "Dave", "action_type": "call", "amount": 2}  # Dave doesn't exist
        ]
        
        with self.assertRaises(ValueError) as cm:
            process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        self.assertIn("not found", str(cm.exception))

    def test_double_action_validation(self):
        """Test that folded players can't act again"""
        actions = [
            {"player_name": "Charlie", "action_type": "fold"},
            {"player_name": "Charlie", "action_type": "call", "amount": 2}  # Should fail - already folded
        ]
        
        with self.assertRaises(ValueError) as cm:
            process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        self.assertIn("has already folded", str(cm.exception))


if __name__ == "__main__":
    unittest.main()