import unittest
from poker_engine import PokerHandBuilder, create_sample_hand


class TestPokerHandBuilder(unittest.TestCase):
    """Test cases for PokerHandBuilder class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.builder = PokerHandBuilder()
        self.test_players = [
            {'name': 'Alice', 'stack': 100.0},
            {'name': 'Bob', 'stack': 150.0},
            {'name': 'Charlie', 'stack': 200.0}
        ]
    
    def test_create_game(self):
        """Test game creation with players"""
        self.builder.create_game(self.test_players, small_blind=1.0, big_blind=2.0)
        
        self.assertEqual(len(self.builder.hand_data['players']), 3)
        self.assertEqual(self.builder.hand_data['small_blind'], 1.0)
        self.assertEqual(self.builder.hand_data['big_blind'], 2.0)
        self.assertEqual(self.builder.hand_data['actions'], [])
        self.assertEqual(self.builder.hand_data['hole_cards'], {})
        self.assertEqual(self.builder.hand_data['board_cards'], [])
    
    def test_deal_hole_cards(self):
        """Test dealing hole cards to players"""
        self.builder.create_game(self.test_players)
        hole_cards = {
            'Alice': 'AsKh',
            'Bob': 'QdQc',
            'Charlie': '7s2h'
        }
        
        self.builder.deal_hole_cards(hole_cards)
        
        self.assertEqual(self.builder.hand_data['hole_cards'], hole_cards)
    
    def test_add_action(self):
        """Test adding player actions"""
        self.builder.create_game(self.test_players)
        
        # Add preflop action
        self.builder.add_action('Alice', 'bet', 5.0)
        
        self.assertEqual(len(self.builder.hand_data['actions']), 1)
        action = self.builder.hand_data['actions'][0]
        self.assertEqual(action['player_name'], 'Alice')
        self.assertEqual(action['action_type'], 'bet')
        self.assertEqual(action['amount'], 5.0)
        self.assertEqual(action['street'], 'preflop')
    
    def test_deal_flop(self):
        """Test dealing flop cards"""
        self.builder.create_game(self.test_players)
        flop = 'AhKd5c'
        
        self.builder.deal_flop(flop)
        
        self.assertEqual(self.builder.hand_data['flop'], flop)
        self.assertEqual(self.builder.hand_data['board_cards'], ['Ah', 'Kd', '5c'])
    
    def test_deal_turn(self):
        """Test dealing turn card"""
        self.builder.create_game(self.test_players)
        self.builder.deal_flop('AhKd5c')
        turn = '9s'
        
        self.builder.deal_turn(turn)
        
        self.assertEqual(self.builder.hand_data['turn'], turn)
        self.assertEqual(self.builder.hand_data['board_cards'], ['Ah', 'Kd', '5c', '9s'])
    
    def test_deal_river(self):
        """Test dealing river card"""
        self.builder.create_game(self.test_players)
        self.builder.deal_flop('AhKd5c')
        self.builder.deal_turn('9s')
        river = '3d'
        
        self.builder.deal_river(river)
        
        self.assertEqual(self.builder.hand_data['river'], river)
        self.assertEqual(self.builder.hand_data['board_cards'], ['Ah', 'Kd', '5c', '9s', '3d'])
    
    def test_get_current_street(self):
        """Test street detection"""
        self.builder.create_game(self.test_players)
        
        # Preflop
        self.assertEqual(self.builder._get_current_street(), 'preflop')
        
        # Flop
        self.builder.deal_flop('AhKd5c')
        self.assertEqual(self.builder._get_current_street(), 'flop')
        
        # Turn
        self.builder.deal_turn('9s')
        self.assertEqual(self.builder._get_current_street(), 'turn')
        
        # River
        self.builder.deal_river('3d')
        self.assertEqual(self.builder._get_current_street(), 'river')
    
    def test_get_player_index(self):
        """Test player index lookup"""
        self.builder.create_game(self.test_players)
        
        self.assertEqual(self.builder._get_player_index('Alice'), 0)
        self.assertEqual(self.builder._get_player_index('Bob'), 1)
        self.assertEqual(self.builder._get_player_index('Charlie'), 2)
        
        with self.assertRaises(ValueError):
            self.builder._get_player_index('NonExistent')
    
    def test_generate_phh_basic(self):
        """Test PHH generation with basic hand"""
        self.builder.create_game(self.test_players[:2], small_blind=1.0, big_blind=2.0)
        self.builder.deal_hole_cards({'Alice': 'AsKh', 'Bob': 'QdQc'})
        self.builder.add_action('Alice', 'bet', 5.0)
        self.builder.add_action('Bob', 'call')
        
        phh = self.builder.generate_phh()
        
        self.assertIn('variant = "NLHE"', phh)
        self.assertIn('ante_trimming_status = true', phh)
        self.assertIn('antes = [0, 0]', phh)
        self.assertIn('blinds_or_straddles = [1, 2]', phh)
        self.assertIn('min_bet = 2', phh)
        self.assertIn('starting_stacks = [100, 150]', phh)
        self.assertIn('d dh p0 AsKh', phh)
        self.assertIn('d dh p1 QdQc', phh)
        self.assertIn('p0 cbr 5', phh)
        self.assertIn('p1 cc', phh)
    
    def test_generate_phh_with_board(self):
        """Test PHH generation with board cards"""
        self.builder.create_game(self.test_players[:2])
        self.builder.deal_hole_cards({'Alice': 'AsKh', 'Bob': 'QdQc'})
        self.builder.deal_flop('AhKd5c')
        self.builder.deal_turn('9s')
        self.builder.deal_river('3d')
        
        phh = self.builder.generate_phh()
        
        self.assertIn('d db AhKd5c', phh)
        self.assertIn('d db 9s', phh)
        self.assertIn('d db 3d', phh)
    
    def test_action_types_in_phh(self):
        """Test different action types in PHH generation"""
        self.builder.create_game(self.test_players[:3])
        
        # Test all action types
        self.builder.add_action('Alice', 'fold')
        self.builder.add_action('Bob', 'check')
        self.builder.add_action('Charlie', 'bet', 10.0)
        
        phh = self.builder.generate_phh()
        
        self.assertIn('p0 f', phh)  # fold
        self.assertIn('p1 cc', phh)  # check
        self.assertIn('p2 cbr 10', phh)  # bet


class TestCreateSampleHand(unittest.TestCase):
    """Test cases for create_sample_hand function"""
    
    def test_create_sample_hand_structure(self):
        """Test sample hand creation returns correct structure"""
        result = create_sample_hand()
        
        self.assertIn('play_id', result)
        self.assertIn('phh_content', result)
        self.assertIn('hand_data', result)
        
        # Check play_id is a valid UUID string
        self.assertIsInstance(result['play_id'], str)
        self.assertEqual(len(result['play_id']), 36)  # UUID length with hyphens
        
        # Check PHH content is generated
        self.assertIsInstance(result['phh_content'], str)
        self.assertGreater(len(result['phh_content']), 0)
        
        # Check hand_data structure
        hand_data = result['hand_data']
        self.assertIn('players', hand_data)
        self.assertIn('actions', hand_data)
        self.assertEqual(len(hand_data['players']), 3)
        self.assertGreater(len(hand_data['actions']), 0)
    
    def test_sample_hand_content(self):
        """Test sample hand contains expected content"""
        result = create_sample_hand()
        phh = result['phh_content']
        
        # Check for expected PHH structure
        self.assertIn('variant = "NLHE"', phh)
        self.assertIn('starting_stacks = [100, 100, 150]', phh)
        self.assertIn('d dh p0 AsKh', phh)  # Alice's hole cards
        self.assertIn('d dh p1 QdQc', phh)  # Bob's hole cards
        self.assertIn('d dh p2 7s2h', phh)  # Charlie's hole cards
        self.assertIn('d db AhKd5c', phh)  # Flop
        self.assertIn('p2 f', phh)  # Charlie folds
        self.assertIn('p0 cbr 6', phh)  # Alice raises
        self.assertIn('p1 cc', phh)  # Bob calls


class TestPokerHandBuilderEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.builder = PokerHandBuilder()
    
    def test_generate_phh_without_game(self):
        """Test PHH generation without creating game first"""
        # Should not raise error, but return minimal PHH
        phh = self.builder.generate_phh()
        self.assertIsInstance(phh, str)
    
    def test_empty_players_list(self):
        """Test creating game with empty players list"""
        self.builder.create_game([])
        
        self.assertEqual(len(self.builder.hand_data['players']), 0)
        
        phh = self.builder.generate_phh()
        self.assertIn('antes = []', phh)
        self.assertIn('starting_stacks = []', phh)
    
    def test_single_player_game(self):
        """Test creating game with single player"""
        single_player = [{'name': 'Alice', 'stack': 100.0}]
        self.builder.create_game(single_player, small_blind=1.0, big_blind=2.0)
        
        phh = self.builder.generate_phh()
        
        self.assertIn('antes = [0]', phh)
        self.assertIn('blinds_or_straddles = [1]', phh)
        self.assertIn('starting_stacks = [100]', phh)
    
    def test_large_blinds(self):
        """Test with large blind values"""
        players = [{'name': 'Alice', 'stack': 1000.0}, {'name': 'Bob', 'stack': 1000.0}]
        self.builder.create_game(players, small_blind=25.0, big_blind=50.0)
        
        phh = self.builder.generate_phh()
        
        self.assertIn('blinds_or_straddles = [25, 50]', phh)
        self.assertIn('min_bet = 50', phh)
    
    def test_hole_cards_partial_players(self):
        """Test dealing hole cards to only some players"""
        players = [
            {'name': 'Alice', 'stack': 100.0},
            {'name': 'Bob', 'stack': 100.0},
            {'name': 'Charlie', 'stack': 100.0}
        ]
        self.builder.create_game(players)
        
        # Only give hole cards to Alice and Bob
        hole_cards = {'Alice': 'AsKh', 'Bob': 'QdQc'}
        self.builder.deal_hole_cards(hole_cards)
        
        phh = self.builder.generate_phh()
        
        self.assertIn('d dh p0 AsKh', phh)
        self.assertIn('d dh p1 QdQc', phh)
        self.assertNotIn('d dh p2', phh)  # Charlie should not have hole cards
    
    def test_action_with_zero_amount(self):
        """Test actions with zero amount"""
        players = [{'name': 'Alice', 'stack': 100.0}]
        self.builder.create_game(players)
        
        self.builder.add_action('Alice', 'check', 0)
        self.builder.add_action('Alice', 'fold')  # No amount specified
        
        actions = self.builder.hand_data['actions']
        self.assertEqual(actions[0]['amount'], 0)
        self.assertEqual(actions[1]['amount'], 0)


if __name__ == '__main__':
    unittest.main()