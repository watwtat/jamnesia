#!/usr/bin/env python3
"""
Test cases for Position enum in template rendering
"""

import unittest
import tempfile
import os
from app import app, db
from models import Hand, Player, Action, Position

class TestPositionTemplateRendering(unittest.TestCase):
    """Test Position enum functionality in template rendering"""
    
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
    
    def test_position_display_in_hand_details_template(self):
        """Test that Position enum names are displayed correctly in hand details template"""
        # Create a sample hand first
        sample_response = self.client.post('/api/create-sample')
        self.assertEqual(sample_response.status_code, 200)
        
        # Get the play_id from the response
        import json
        sample_data = json.loads(sample_response.data)
        play_id = sample_data['play_id']
        
        # Request the hand details HTML template
        response = self.client.get(f'/api/hands/{play_id}/details')
        self.assertEqual(response.status_code, 200)
        
        # Check that position names are rendered correctly in HTML
        html_content = response.data.decode('utf-8')
        
        # Should contain position names instead of numbers
        self.assertIn('SB', html_content)  # Small Blind
        self.assertIn('BB', html_content)  # Big Blind  
        self.assertIn('UTG', html_content) # Under The Gun
        
        # Should NOT contain raw position numbers like "Position 0"
        self.assertNotIn('Position 0', html_content)
        self.assertNotIn('Position 1', html_content)
        self.assertNotIn('Position 2', html_content)
    
    def test_position_display_with_all_positions(self):
        """Test position display with all possible enum positions"""
        # Create a hand with all 9 positions
        with app.app_context():
            # Create hand
            hand = Hand(
                play_id='test-all-positions',
                game_type='No Limit Texas Holdem',
                board='',
                small_blind=1.0,
                big_blind=2.0,
                phh_content='test'
            )
            db.session.add(hand)
            db.session.flush()
            
            # Create players with all position enum values
            position_names = ['Player_SB', 'Player_BB', 'Player_UTG', 'Player_UTG1', 
                            'Player_MP', 'Player_LJ', 'Player_HJ', 'Player_CO', 'Player_BTN']
            positions = [Position.SB, Position.BB, Position.UTG, Position.UTG1,
                        Position.MP, Position.LJ, Position.HJ, Position.CO, Position.BTN]
            
            for name, pos in zip(position_names, positions):
                player = Player(
                    hand_id=hand.id,
                    name=name,
                    stack=100.0,
                    hole_cards='AsKh',
                    position=pos
                )
                db.session.add(player)
            
            db.session.commit()
        
        # Request the hand details template
        response = self.client.get('/api/hands/test-all-positions/details')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check that all position names are displayed
        expected_positions = ['SB', 'BB', 'UTG', 'UTG1', 'MP', 'LJ', 'HJ', 'CO', 'BTN']
        for pos_name in expected_positions:
            self.assertIn(pos_name, html_content)
    
    def test_position_display_with_extra_positions(self):
        """Test position display with positions beyond enum range"""
        with app.app_context():
            # Create hand
            hand = Hand(
                play_id='test-extra-positions',
                game_type='No Limit Texas Holdem',
                board='',
                small_blind=1.0,
                big_blind=2.0,
                phh_content='test'
            )
            db.session.add(hand)
            db.session.flush()
            
            # Create players including some beyond enum range
            players_data = [
                ('Player1', Position.SB),
                ('Player2', Position.BB),
                ('Player3', 9),  # Beyond enum range
                ('Player4', 10), # Beyond enum range
            ]
            
            for name, pos in players_data:
                player = Player(
                    hand_id=hand.id,
                    name=name,
                    stack=100.0,
                    hole_cards='AsKh',
                    position=pos
                )
                db.session.add(player)
            
            db.session.commit()
        
        # Request the hand details template
        response = self.client.get('/api/hands/test-extra-positions/details')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check that enum positions show names
        self.assertIn('SB', html_content)
        self.assertIn('BB', html_content)
        
        # Check that extra positions show fallback format
        self.assertIn('P9', html_content)
        self.assertIn('P10', html_content)
    
    def test_position_enum_accessibility_in_template(self):
        """Test that Position enum is accessible in template context"""
        # Create a sample hand
        sample_response = self.client.post('/api/create-sample')
        self.assertEqual(sample_response.status_code, 200)
        
        import json
        sample_data = json.loads(sample_response.data)
        play_id = sample_data['play_id']
        
        # Request hand details
        response = self.client.get(f'/api/hands/{play_id}/details')
        self.assertEqual(response.status_code, 200)
        
        # The fact that we get a successful response with position names
        # means the Position enum is properly accessible in the template
        html_content = response.data.decode('utf-8')
        
        # Verify the template can call Position.get_display_name
        # This is confirmed by the presence of position names instead of numbers
        position_names = ['SB', 'BB', 'UTG', 'UTG1', 'MP', 'LJ', 'HJ', 'CO', 'BTN']
        found_positions = [name for name in position_names if name in html_content]
        
        # Should find at least the positions used in sample hand (SB, BB, UTG)
        self.assertGreaterEqual(len(found_positions), 3)

if __name__ == '__main__':
    unittest.main()