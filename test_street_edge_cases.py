import unittest
from app import process_hand_actions, should_advance_street


class TestStreetEdgeCases(unittest.TestCase):
    """Test edge cases for automatic street progression"""

    def setUp(self):
        """Set up test fixtures"""
        self.players_data = [
            {"name": "Alice", "stack": 100},
            {"name": "Bob", "stack": 100},
            {"name": "Charlie", "stack": 100},
            {"name": "Dave", "stack": 100}
        ]
        
        self.small_blind = 1.0
        self.big_blind = 2.0

    def test_heads_up_scenario(self):
        """Test heads-up (2 player) scenario"""
        heads_up_players = [
            {"name": "Alice", "stack": 100},
            {"name": "Bob", "stack": 100}
        ]
        
        actions = [
            {"player_name": "Alice", "action_type": "call", "amount": 1},  # SB calls
            {"player_name": "Bob", "action_type": "check"}                # BB checks
        ]
        
        result = process_hand_actions(heads_up_players, actions, self.small_blind, self.big_blind)
        
        # Should progress to flop
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))
        
        # Verify pot size
        final_pot = result[-1]["pot_size"]
        self.assertEqual(final_pot, 4.0)  # 1 + 2 + 1 = 4

    def test_all_in_scenario(self):
        """Test all-in scenarios"""
        short_stack_players = [
            {"name": "Alice", "stack": 5},
            {"name": "Bob", "stack": 100},
            {"name": "Charlie", "stack": 100}
        ]
        
        actions = [
            {"player_name": "Charlie", "action_type": "raise", "amount": 10},
            {"player_name": "Alice", "action_type": "call", "amount": 5},  # All-in with remaining stack
            {"player_name": "Bob", "action_type": "call", "amount": 10}
        ]
        
        result = process_hand_actions(short_stack_players, actions, self.small_blind, self.big_blind)
        
        # Alice should be all-in with remaining stack
        alice_action = next(action for action in result if action["player_name"] == "Alice")
        self.assertEqual(alice_action["remaining_stack"], 0)  # Should be 0 after all-in

    def test_single_player_remaining(self):
        """Test when only one player remains active"""
        actions = [
            {"player_name": "Charlie", "action_type": "fold"},
            {"player_name": "Alice", "action_type": "fold"},
            {"player_name": "Dave", "action_type": "fold"}
            # Bob wins by default
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # All actions should be preflop since hand ends when only one player remains
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))

    def test_empty_actions_list(self):
        """Test with no actions provided"""
        actions = []
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should create fold actions for all players except blinds
        self.assertEqual(len(result), 4)  # All 4 players should have fold actions
        
        # All should be folds with preflop street
        for action in result:
            self.assertEqual(action["action_type"], "fold")
            self.assertEqual(action["street"], "preflop")

    def test_complex_multi_street_scenario(self):
        """Test complex scenario going through all streets"""
        actions = [
            # Preflop
            {"player_name": "Charlie", "action_type": "raise", "amount": 6},
            {"player_name": "Dave", "action_type": "call", "amount": 6},
            {"player_name": "Alice", "action_type": "call", "amount": 6},
            {"player_name": "Bob", "action_type": "call", "amount": 6},
            
            # Flop (should auto-advance here)
            {"player_name": "Alice", "action_type": "check"},
            {"player_name": "Bob", "action_type": "bet", "amount": 8},
            {"player_name": "Charlie", "action_type": "fold"},
            {"player_name": "Dave", "action_type": "call", "amount": 8},
            {"player_name": "Alice", "action_type": "call", "amount": 8},
            
            # Turn (should auto-advance here)
            {"player_name": "Alice", "action_type": "check"},
            {"player_name": "Bob", "action_type": "check"},
            {"player_name": "Dave", "action_type": "bet", "amount": 15},
            {"player_name": "Alice", "action_type": "fold"},
            {"player_name": "Bob", "action_type": "call", "amount": 15},
            
            # River (should auto-advance here)
            {"player_name": "Bob", "action_type": "check"},
            {"player_name": "Dave", "action_type": "check"}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should have actions on all streets
        streets = [action["street"] for action in result]
        unique_streets = set(streets)
        
        self.assertIn("preflop", unique_streets)
        self.assertIn("flop", unique_streets)
        self.assertIn("turn", unique_streets)
        self.assertIn("river", unique_streets)
        
        # Verify street progression order
        street_indices = []
        for action in result:
            if action["street"] == "preflop":
                street_indices.append(0)
            elif action["street"] == "flop":
                street_indices.append(1)
            elif action["street"] == "turn":
                street_indices.append(2)
            elif action["street"] == "river":
                street_indices.append(3)
        
        # Should be in ascending order (no street should come before a previous one)
        self.assertEqual(street_indices, sorted(street_indices))

    def test_zero_amount_calls(self):
        """Test calls with zero additional amount (already matching bet)"""
        actions = [
            {"player_name": "Charlie", "action_type": "call", "amount": 2},  # calls BB
            {"player_name": "Alice", "action_type": "call", "amount": 1},   # SB calls (only needs 1 more)
            {"player_name": "Bob", "action_type": "check"}                  # BB checks (0 additional)
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Bob's check should have 0 amount
        bob_action = next(action for action in result if action["player_name"] == "Bob" and action["action_type"] == "check")
        self.assertEqual(bob_action["amount"], 0)

    def test_large_raise_scenario(self):
        """Test scenario with large raises"""
        actions = [
            {"player_name": "Charlie", "action_type": "raise", "amount": 50},
            {"player_name": "Dave", "action_type": "raise", "amount": 80},
            {"player_name": "Alice", "action_type": "fold"},
            {"player_name": "Bob", "action_type": "fold"},
            {"player_name": "Charlie", "action_type": "call", "amount": 80}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Should all be preflop
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))
        
        # Verify final pot size calculation
        final_pot = result[-1]["pot_size"]
        expected_pot = self.small_blind + self.big_blind + 50 + 80 + 30  # blinds + first raise + reraise + call additional
        self.assertEqual(final_pot, expected_pot)

    def test_maximum_players(self):
        """Test with maximum number of players (9)"""
        max_players = [{"name": f"Player{i}", "stack": 100} for i in range(1, 10)]
        
        # Everyone calls preflop (proper order: Player3-9, then SB, then BB)
        actions = []
        for i in range(3, 10):  # Player3 to Player9 call
            actions.append({"player_name": f"Player{i}", "action_type": "call", "amount": 2})
        
        # Blinds act
        actions.append({"player_name": "Player1", "action_type": "call", "amount": 1})  # SB calls (needs 1 more)
        actions.append({"player_name": "Player2", "action_type": "check"})              # BB checks (already has 2)
        
        result = process_hand_actions(max_players, actions, self.small_blind, self.big_blind)
        
        # Should all be preflop
        streets = [action["street"] for action in result]
        self.assertTrue(all(s == "preflop" for s in streets))
        
        # Pot should have contributions from all 9 players
        final_pot = result[-1]["pot_size"]
        self.assertEqual(final_pot, 18.0)  # 9 players * 2 BB each

    def test_remaining_stack_accuracy(self):
        """Test accuracy of remaining stack calculations"""
        actions = [
            {"player_name": "Charlie", "action_type": "raise", "amount": 20},
            {"player_name": "Alice", "action_type": "call", "amount": 20},
            {"player_name": "Bob", "action_type": "fold"}
        ]
        
        result = process_hand_actions(self.players_data, actions, self.small_blind, self.big_blind)
        
        # Check Charlie's remaining stack (started with 100, bet 20)
        charlie_action = next(action for action in result if action["player_name"] == "Charlie")
        self.assertEqual(charlie_action["remaining_stack"], 80.0)
        
        # Check Alice's remaining stack (started with 100, SB=1, then called 20 total)
        alice_action = next(action for action in result if action["player_name"] == "Alice")
        self.assertEqual(alice_action["remaining_stack"], 80.0)  # 100 - 20 = 80
        
        # Check Bob's remaining stack (started with 100, BB=2, then folded)
        bob_action = next(action for action in result if action["player_name"] == "Bob")
        self.assertEqual(bob_action["remaining_stack"], 98.0)  # 100 - 2 = 98


if __name__ == "__main__":
    unittest.main()