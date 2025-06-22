import unittest
import json
import tempfile
import os
from flask import Flask
from app import app, db
from models import Hand, Player, Action, Position


class TestApp(unittest.TestCase):
    """Test cases for Flask application routes and functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Configure test app
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
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
    
    def test_index_route(self):
        """Test main index page"""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jamnesia', response.data)
        self.assertIn(b'Poker Hand Management System', response.data)
        self.assertIn(b'Input New Hand', response.data)
        self.assertIn(b'Create Sample Hand', response.data)
    
    def test_input_route(self):
        """Test hand input form page"""
        response = self.client.get('/input')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Poker Hand Input', response.data)
        self.assertIn(b'Player Settings', response.data)
        self.assertIn(b'Board Cards', response.data)
        self.assertIn(b'Actions', response.data)
        self.assertIn(b'Save Hand', response.data)
    
    def test_create_sample_hand(self):
        """Test sample hand creation endpoint"""
        response = self.client.post('/api/create-sample')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('hand_id', data)
        self.assertIn('play_id', data)
        
        # Verify hand was created in database
        with app.app_context():
            hand = Hand.query.get(data['hand_id'])
            self.assertIsNotNone(hand)
            self.assertEqual(hand.play_id, data['play_id'])
            self.assertEqual(hand.game_type, 'No Limit Texas Holdem')
            self.assertEqual(len(hand.players), 3)
            self.assertGreater(len(hand.actions), 0)
    
    def test_save_hand_basic(self):
        """Test basic hand saving functionality"""
        test_data = {
            'players': [
                {'name': 'Alice', 'stack': 100.0},
                {'name': 'Bob', 'stack': 150.0}
            ],
            'actions': [
                {'player_name': 'Alice', 'action_type': 'bet', 'amount': 5.0},
                {'player_name': 'Bob', 'action_type': 'call'}
            ],
            'small_blind': 1.0,
            'big_blind': 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('hand_id', data)
        self.assertIn('play_id', data)
        self.assertIn('phh_content', data)
        
        # Verify PHH content
        phh = data['phh_content']
        self.assertIn('variant = "NLHE"', phh)
        self.assertIn('starting_stacks = [100, 150]', phh)
        self.assertIn('p0 cbr 5', phh)
        self.assertIn('p1 cc', phh)
    
    def test_save_hand_with_hole_cards(self):
        """Test hand saving with hole cards"""
        test_data = {
            'players': [
                {'name': 'Alice', 'stack': 100.0},
                {'name': 'Bob', 'stack': 100.0}
            ],
            'actions': [
                {'player_name': 'Alice', 'action_type': 'check'},
                {'player_name': 'Bob', 'action_type': 'check'}
            ],
            'hole_cards': {
                'Alice': 'AsKh',
                'Bob': 'QdQc'
            },
            'small_blind': 1.0,
            'big_blind': 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        phh = data['phh_content']
        
        self.assertIn('d dh p0 AsKh', phh)
        self.assertIn('d dh p1 QdQc', phh)
    
    def test_save_hand_with_board_cards(self):
        """Test hand saving with board cards"""
        test_data = {
            'players': [
                {'name': 'Alice', 'stack': 100.0},
                {'name': 'Bob', 'stack': 100.0}
            ],
            'actions': [
                {'player_name': 'Alice', 'action_type': 'bet', 'amount': 5.0},
                {'player_name': 'Bob', 'action_type': 'fold'}
            ],
            'flop': 'AhKd5c',
            'turn': '9s',
            'river': '3d',
            'small_blind': 1.0,
            'big_blind': 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        phh = data['phh_content']
        
        self.assertIn('d db AhKd5c', phh)
        self.assertIn('d db 9s', phh)
        self.assertIn('d db 3d', phh)
    
    def test_save_hand_missing_required_fields(self):
        """Test hand saving with missing required fields"""
        # Missing players
        test_data = {
            'actions': [{'player_name': 'Alice', 'action_type': 'fold'}]
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required field: players', data['error'])
        
        # Missing actions
        test_data = {
            'players': [{'name': 'Alice', 'stack': 100.0}]
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('Missing required field: actions', data['error'])
    
    def test_save_hand_invalid_json(self):
        """Test hand saving with invalid JSON"""
        response = self.client.post('/api/save-hand',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
    
    def test_list_hands_empty(self):
        """Test listing hands when none exist"""
        response = self.client.get('/api/hands')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data, [])
    
    def test_list_hands_with_data(self):
        """Test listing hands with existing data"""
        # Create a sample hand first
        self.client.post('/api/create-sample')
        
        response = self.client.get('/api/hands')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        
        hand_data = data[0]
        self.assertIn('id', hand_data)
        self.assertIn('play_id', hand_data)
        self.assertIn('game_type', hand_data)
        self.assertIn('created_at', hand_data)
        self.assertEqual(hand_data['game_type'], 'No Limit Texas Holdem')
    
    def test_list_hands_htmx_request(self):
        """Test listing hands with HTMX request returns HTML"""
        # Create a sample hand first
        self.client.post('/api/create-sample')
        
        response = self.client.get('/api/hands', headers={'HX-Request': 'true'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<div', response.data)  # Should return HTML, not JSON
        self.assertNotIn(b'[{', response.data)  # Should not be JSON array
    
    def test_get_hand_details(self):
        """Test retrieving specific hand details"""
        # Create a sample hand first
        create_response = self.client.post('/api/create-sample')
        create_data = json.loads(create_response.data)
        play_id = create_data['play_id']
        
        response = self.client.get(f'/api/hands/{play_id}')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('hand', data)
        self.assertIn('players', data)
        self.assertIn('actions', data)
        
        # Check hand details
        hand = data['hand']
        self.assertEqual(hand['play_id'], play_id)
        self.assertEqual(hand['game_type'], 'No Limit Texas Holdem')
        self.assertIn('phh_content', hand)
        
        # Check players
        players = data['players']
        self.assertEqual(len(players), 3)
        player_names = [p['name'] for p in players]
        self.assertIn('Alice', player_names)
        self.assertIn('Bob', player_names)
        self.assertIn('Charlie', player_names)
        
        # Check actions
        actions = data['actions']
        self.assertGreater(len(actions), 0)
        
        # Verify action structure
        action = actions[0]
        self.assertIn('street', action)
        self.assertIn('player_name', action)
        self.assertIn('action_type', action)
        self.assertIn('amount', action)
        self.assertIn('action_order', action)
    
    def test_get_hand_not_found(self):
        """Test retrieving non-existent hand"""
        response = self.client.get('/api/hands/non-existent-id')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Hand not found')
    
    def test_save_hand_with_custom_play_id(self):
        """Test saving hand with custom play_id"""
        custom_play_id = 'custom-test-hand-123'
        test_data = {
            'play_id': custom_play_id,
            'players': [
                {'name': 'Alice', 'stack': 100.0}
            ],
            'actions': [
                {'player_name': 'Alice', 'action_type': 'fold'}
            ]
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['play_id'], custom_play_id)
        
        # Verify we can retrieve it
        get_response = self.client.get(f'/api/hands/{custom_play_id}')
        self.assertEqual(get_response.status_code, 200)
    
    def test_save_hand_generates_uuid_when_no_play_id(self):
        """Test that play_id is auto-generated when not provided"""
        test_data = {
            'players': [{'name': 'Alice', 'stack': 100.0}],
            'actions': [{'player_name': 'Alice', 'action_type': 'fold'}]
        }
        
        response = self.client.post('/api/save-hand',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        play_id = data['play_id']
        
        # Should be a UUID format (36 characters with hyphens)
        self.assertEqual(len(play_id), 36)
        self.assertEqual(play_id.count('-'), 4)
    
    def test_multiple_hands_ordering(self):
        """Test that hands are returned in correct order (newest first)"""
        # Create multiple hands
        for i in range(3):
            test_data = {
                'players': [{'name': f'Player{i}', 'stack': 100.0}],
                'actions': [{'player_name': f'Player{i}', 'action_type': 'fold'}]
            }
            self.client.post('/api/save-hand',
                           data=json.dumps(test_data),
                           content_type='application/json')
        
        response = self.client.get('/api/hands')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)
        
        # Should be ordered by created_at desc (newest first)
        created_times = [hand['created_at'] for hand in data]
        self.assertEqual(created_times, sorted(created_times, reverse=True))


class TestAppIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
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
    
    def test_complete_hand_workflow(self):
        """Test complete workflow: save hand -> list hands -> get details"""
        # Step 1: Save a complete hand
        hand_data = {
            'players': [
                {'name': 'Alice', 'stack': 100.0},
                {'name': 'Bob', 'stack': 150.0},
                {'name': 'Charlie', 'stack': 200.0}
            ],
            'hole_cards': {
                'Alice': 'AsKh',
                'Bob': 'QdQc',
                'Charlie': '7s2h'
            },
            'actions': [
                {'player_name': 'Charlie', 'action_type': 'fold'},
                {'player_name': 'Alice', 'action_type': 'raise', 'amount': 6.0},
                {'player_name': 'Bob', 'action_type': 'call'},
                {'player_name': 'Alice', 'action_type': 'bet', 'amount': 8.0},
                {'player_name': 'Bob', 'action_type': 'fold'}
            ],
            'flop': 'AhKd5c',
            'small_blind': 1.0,
            'big_blind': 2.0
        }
        
        save_response = self.client.post('/api/save-hand',
                                       data=json.dumps(hand_data),
                                       content_type='application/json')
        
        self.assertEqual(save_response.status_code, 200)
        save_data = json.loads(save_response.data)
        play_id = save_data['play_id']
        
        # Step 2: List hands and verify our hand appears
        list_response = self.client.get('/api/hands')
        self.assertEqual(list_response.status_code, 200)
        
        list_data = json.loads(list_response.data)
        self.assertEqual(len(list_data), 1)
        self.assertEqual(list_data[0]['play_id'], play_id)
        
        # Step 3: Get detailed hand information
        detail_response = self.client.get(f'/api/hands/{play_id}')
        self.assertEqual(detail_response.status_code, 200)
        
        detail_data = json.loads(detail_response.data)
        
        # Verify all data is preserved
        self.assertEqual(len(detail_data['players']), 3)
        self.assertEqual(len(detail_data['actions']), 5)
        
        # Check PHH content includes all elements
        phh = detail_data['hand']['phh_content']
        self.assertIn('d dh p0 AsKh', phh)  # Alice hole cards
        self.assertIn('d dh p1 QdQc', phh)  # Bob hole cards
        self.assertIn('d dh p2 7s2h', phh)  # Charlie hole cards
        self.assertIn('d db AhKd5c', phh)   # Flop
        self.assertIn('p2 f', phh)          # Charlie fold
        self.assertIn('p0 cbr 6', phh)      # Alice raise
        self.assertIn('p1 cc', phh)         # Bob call
        self.assertIn('p0 cbr 8', phh)      # Alice bet
        self.assertIn('p1 f', phh)          # Bob fold
    
    def test_sample_hand_workflow(self):
        """Test sample hand creation and retrieval workflow"""
        # Create sample hand
        create_response = self.client.post('/api/create-sample')
        self.assertEqual(create_response.status_code, 200)
        
        create_data = json.loads(create_response.data)
        play_id = create_data['play_id']
        
        # Verify it appears in hand list
        list_response = self.client.get('/api/hands')
        list_data = json.loads(list_response.data)
        
        self.assertEqual(len(list_data), 1)
        self.assertEqual(list_data[0]['play_id'], play_id)
        
        # Get detailed view
        detail_response = self.client.get(f'/api/hands/{play_id}')
        detail_data = json.loads(detail_response.data)
        
        # Verify sample hand structure
        self.assertEqual(len(detail_data['players']), 3)
        self.assertGreater(len(detail_data['actions']), 0)
        
        # Check that PHH was generated
        phh = detail_data['hand']['phh_content']
        self.assertIn('variant = "NLHE"', phh)
        self.assertGreater(len(phh), 100)  # Should be a substantial PHH


class TestPositionIntegration(unittest.TestCase):
    """Test Position enum integration with Flask application"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Configure test app
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True
        
        self.client = app.test_client()
        
        # Create application context and initialize database
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test method"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_position_enum_in_sample_hand_creation(self):
        """Test that Position enum is used correctly in sample hand creation"""
        response = self.client.post('/api/create-sample')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        
        # Check that players were created with correct Position enum values
        with app.app_context():
            players = Player.query.order_by(Player.position).all()
            self.assertEqual(len(players), 3)
            
            # Alice should be SB (position 0)
            alice = players[0]
            self.assertEqual(alice.name, 'Alice')
            self.assertEqual(alice.position, Position.SB)
            self.assertEqual(alice.position, 0)
            
            # Bob should be BB (position 1) 
            bob = players[1]
            self.assertEqual(bob.name, 'Bob')
            self.assertEqual(bob.position, Position.BB)
            self.assertEqual(bob.position, 1)
            
            # Charlie should be UTG (position 2)
            charlie = players[2]
            self.assertEqual(charlie.name, 'Charlie')
            self.assertEqual(charlie.position, Position.UTG)
            self.assertEqual(charlie.position, 2)
    
    def test_position_enum_in_regular_hand_saving(self):
        """Test that Position enum is used correctly in regular hand saving"""
        hand_data = {
            "players": [
                {"name": "Alice", "stack": 100.0},
                {"name": "Bob", "stack": 100.0},
                {"name": "Charlie", "stack": 150.0},
                {"name": "David", "stack": 200.0}
            ],
            "actions": [
                {"player_name": "Alice", "action_type": "fold"},
                {"player_name": "Bob", "action_type": "raise", "amount": 10.0},
                {"player_name": "Charlie", "action_type": "call"},
                {"player_name": "David", "action_type": "fold"}
            ],
            "small_blind": 1.0,
            "big_blind": 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                   data=json.dumps(hand_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that players were created with correct Position enum values
        with app.app_context():
            players = Player.query.order_by(Player.position).all()
            self.assertEqual(len(players), 4)
            
            # Verify positions match enum values
            expected_positions = [Position.SB, Position.BB, Position.UTG, Position.UTG1]
            for i, (player, expected_pos) in enumerate(zip(players, expected_positions)):
                self.assertEqual(player.position, expected_pos)
                self.assertEqual(player.position, i)
    
    def test_position_display_name_functionality(self):
        """Test Position.get_display_name method with database data"""
        # Create a sample hand
        response = self.client.post('/api/create-sample')
        self.assertEqual(response.status_code, 200)
        
        with app.app_context():
            players = Player.query.all()
            
            for player in players:
                # Test that get_display_name works for all saved positions
                display_name = Position.get_display_name(player.position)
                
                # Verify it returns expected names
                if player.position == Position.SB:
                    self.assertEqual(display_name, 'SB')
                elif player.position == Position.BB:
                    self.assertEqual(display_name, 'BB')
                elif player.position == Position.UTG:
                    self.assertEqual(display_name, 'UTG')
                else:
                    # Should not happen with sample hand, but test anyway
                    self.assertIsInstance(display_name, str)
    
    def test_position_enum_with_many_players(self):
        """Test Position enum handling with maximum number of players"""
        # Create hand with 9 players (all position enum values)
        players_data = []
        for i in range(9):
            players_data.append({"name": f"Player{i+1}", "stack": 100.0})
        
        hand_data = {
            "players": players_data,
            "actions": [
                {"player_name": "Player1", "action_type": "fold"}
            ],
            "small_blind": 1.0,
            "big_blind": 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                   data=json.dumps(hand_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        with app.app_context():
            players = Player.query.order_by(Player.position).all()
            self.assertEqual(len(players), 9)
            
            # Verify all Position enum values are used correctly
            expected_positions = [
                Position.SB, Position.BB, Position.UTG, Position.UTG1,
                Position.MP, Position.LJ, Position.HJ, Position.CO, Position.BTN
            ]
            
            for player, expected_pos in zip(players, expected_positions):
                self.assertEqual(player.position, expected_pos)
                # Verify display name works
                display_name = Position.get_display_name(player.position)
                self.assertEqual(display_name, expected_pos.name)
    
    def test_position_enum_with_rejected_extra_players(self):
        """Test that hands with 10+ players are rejected"""
        # Create hand with 10 players (should be rejected)
        players_data = []
        for i in range(10):
            players_data.append({"name": f"Player{i+1}", "stack": 100.0})
        
        hand_data = {
            "players": players_data,
            "actions": [
                {"player_name": "Player1", "action_type": "fold"}
            ],
            "small_blind": 1.0,
            "big_blind": 2.0
        }
        
        response = self.client.post('/api/save-hand',
                                   data=json.dumps(hand_data),
                                   content_type='application/json')
        
        # Should be rejected with 400 error
        self.assertEqual(response.status_code, 400)
        result = response.get_json()
        self.assertIn('error', result)
        self.assertIn('Maximum of 9 players allowed', result['error'])


if __name__ == '__main__':
    unittest.main()