import unittest
import tempfile
import os
from datetime import datetime
from flask import Flask
from models import db, Hand, Player, Action


class TestModels(unittest.TestCase):
    """Test cases for database models"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test Flask app
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['TESTING'] = True
        
        # Initialize database
        db.init_app(self.app)
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
    
    def tearDown(self):
        """Clean up after each test method"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_hand_creation(self):
        """Test Hand model creation and basic attributes"""
        hand = Hand(
            play_id='test-hand-001',
            game_type='No Limit Texas Holdem',
            board='AhKd5c',
            small_blind=1.0,
            big_blind=2.0,
            phh_content='variant = "NLHE"'
        )
        
        db.session.add(hand)
        db.session.commit()
        
        # Retrieve and verify
        saved_hand = Hand.query.filter_by(play_id='test-hand-001').first()
        self.assertIsNotNone(saved_hand)
        self.assertEqual(saved_hand.play_id, 'test-hand-001')
        self.assertEqual(saved_hand.game_type, 'No Limit Texas Holdem')
        self.assertEqual(saved_hand.board, 'AhKd5c')
        self.assertEqual(saved_hand.small_blind, 1.0)
        self.assertEqual(saved_hand.big_blind, 2.0)
        self.assertEqual(saved_hand.phh_content, 'variant = "NLHE"')
        self.assertIsNotNone(saved_hand.created_at)
    
    def test_hand_defaults(self):
        """Test Hand model default values"""
        hand = Hand(play_id='test-hand-002')
        
        db.session.add(hand)
        db.session.commit()
        
        saved_hand = Hand.query.filter_by(play_id='test-hand-002').first()
        self.assertEqual(saved_hand.game_type, 'No Limit Texas Holdem')
        self.assertEqual(saved_hand.small_blind, 1.0)
        self.assertEqual(saved_hand.big_blind, 2.0)
    
    def test_hand_unique_play_id(self):
        """Test that play_id must be unique"""
        hand1 = Hand(play_id='duplicate-id')
        hand2 = Hand(play_id='duplicate-id')
        
        db.session.add(hand1)
        db.session.commit()
        
        db.session.add(hand2)
        
        with self.assertRaises(Exception):  # IntegrityError
            db.session.commit()
    
    def test_hand_repr(self):
        """Test Hand model string representation"""
        hand = Hand(play_id='repr-test')
        self.assertEqual(repr(hand), '<Hand repr-test>')
    
    def test_player_creation(self):
        """Test Player model creation"""
        # Create a hand first
        hand = Hand(play_id='player-test-hand')
        db.session.add(hand)
        db.session.commit()
        
        # Create player
        player = Player(
            hand_id=hand.id,
            name='Alice',
            stack=100.0,
            hole_cards='AsKh',
            position=0
        )
        
        db.session.add(player)
        db.session.commit()
        
        # Retrieve and verify
        saved_player = Player.query.filter_by(name='Alice').first()
        self.assertIsNotNone(saved_player)
        self.assertEqual(saved_player.hand_id, hand.id)
        self.assertEqual(saved_player.name, 'Alice')
        self.assertEqual(saved_player.stack, 100.0)
        self.assertEqual(saved_player.hole_cards, 'AsKh')
        self.assertEqual(saved_player.position, 0)
    
    def test_player_repr(self):
        """Test Player model string representation"""
        player = Player(name='Bob')
        self.assertEqual(repr(player), '<Player Bob>')
    
    def test_action_creation(self):
        """Test Action model creation"""
        # Create a hand first
        hand = Hand(play_id='action-test-hand')
        db.session.add(hand)
        db.session.commit()
        
        # Create action
        action = Action(
            hand_id=hand.id,
            street='preflop',
            player_name='Alice',
            action_type='bet',
            amount=5.0,
            action_order=1
        )
        
        db.session.add(action)
        db.session.commit()
        
        # Retrieve and verify
        saved_action = Action.query.filter_by(player_name='Alice').first()
        self.assertIsNotNone(saved_action)
        self.assertEqual(saved_action.hand_id, hand.id)
        self.assertEqual(saved_action.street, 'preflop')
        self.assertEqual(saved_action.player_name, 'Alice')
        self.assertEqual(saved_action.action_type, 'bet')
        self.assertEqual(saved_action.amount, 5.0)
        self.assertEqual(saved_action.action_order, 1)
    
    def test_action_default_amount(self):
        """Test Action model default amount"""
        hand = Hand(play_id='action-default-test')
        db.session.add(hand)
        db.session.commit()
        
        action = Action(
            hand_id=hand.id,
            street='preflop',
            player_name='Bob',
            action_type='fold',
            action_order=0
        )
        
        db.session.add(action)
        db.session.commit()
        
        saved_action = Action.query.filter_by(player_name='Bob').first()
        self.assertEqual(saved_action.amount, 0.0)
    
    def test_action_repr(self):
        """Test Action model string representation"""
        action = Action(player_name='Charlie', action_type='call')
        self.assertEqual(repr(action), '<Action Charlie call>')
    
    def test_hand_player_relationship(self):
        """Test relationship between Hand and Player models"""
        # Create hand
        hand = Hand(play_id='relationship-test')
        db.session.add(hand)
        db.session.commit()
        
        # Create players
        player1 = Player(hand_id=hand.id, name='Alice', stack=100.0, position=0)
        player2 = Player(hand_id=hand.id, name='Bob', stack=150.0, position=1)
        
        db.session.add_all([player1, player2])
        db.session.commit()
        
        # Test forward relationship (hand.players)
        saved_hand = Hand.query.filter_by(play_id='relationship-test').first()
        self.assertEqual(len(saved_hand.players), 2)
        player_names = [p.name for p in saved_hand.players]
        self.assertIn('Alice', player_names)
        self.assertIn('Bob', player_names)
        
        # Test backward relationship (player.hand)
        saved_player = Player.query.filter_by(name='Alice').first()
        self.assertEqual(saved_player.hand.play_id, 'relationship-test')
    
    def test_hand_action_relationship(self):
        """Test relationship between Hand and Action models"""
        # Create hand
        hand = Hand(play_id='action-relationship-test')
        db.session.add(hand)
        db.session.commit()
        
        # Create actions
        action1 = Action(
            hand_id=hand.id, 
            street='preflop', 
            player_name='Alice', 
            action_type='bet', 
            amount=5.0, 
            action_order=0
        )
        action2 = Action(
            hand_id=hand.id, 
            street='preflop', 
            player_name='Bob', 
            action_type='call', 
            action_order=1
        )
        
        db.session.add_all([action1, action2])
        db.session.commit()
        
        # Test forward relationship (hand.actions)
        saved_hand = Hand.query.filter_by(play_id='action-relationship-test').first()
        self.assertEqual(len(saved_hand.actions), 2)
        
        # Test actions are ordered correctly
        actions = sorted(saved_hand.actions, key=lambda a: a.action_order)
        self.assertEqual(actions[0].player_name, 'Alice')
        self.assertEqual(actions[0].action_type, 'bet')
        self.assertEqual(actions[1].player_name, 'Bob')
        self.assertEqual(actions[1].action_type, 'call')
        
        # Test backward relationship (action.hand)
        saved_action = Action.query.filter_by(player_name='Alice').first()
        self.assertEqual(saved_action.hand.play_id, 'action-relationship-test')
    
    def test_cascade_delete(self):
        """Test that deleting a hand cascades to players and actions"""
        # Create hand with players and actions
        hand = Hand(play_id='cascade-test')
        db.session.add(hand)
        db.session.commit()
        
        player = Player(hand_id=hand.id, name='Alice', stack=100.0)
        action = Action(
            hand_id=hand.id,
            street='preflop',
            player_name='Alice',
            action_type='fold',
            action_order=0
        )
        
        db.session.add_all([player, action])
        db.session.commit()
        
        # Verify they exist
        self.assertEqual(Player.query.count(), 1)
        self.assertEqual(Action.query.count(), 1)
        
        # Delete the hand
        db.session.delete(hand)
        db.session.commit()
        
        # Verify cascade delete worked
        self.assertEqual(Hand.query.count(), 0)
        self.assertEqual(Player.query.count(), 0)
        self.assertEqual(Action.query.count(), 0)
    
    def test_complex_hand_scenario(self):
        """Test a complete hand scenario with multiple players and actions"""
        # Create hand
        hand = Hand(
            play_id='complex-scenario',
            game_type='No Limit Texas Holdem',
            board='AhKd5c9s3d',
            small_blind=1.0,
            big_blind=2.0,
            phh_content='variant = "NLHE"'
        )
        db.session.add(hand)
        db.session.commit()
        
        # Create players
        players_data = [
            {'name': 'Alice', 'stack': 100.0, 'hole_cards': 'AsKh', 'position': 0},
            {'name': 'Bob', 'stack': 150.0, 'hole_cards': 'QdQc', 'position': 1},
            {'name': 'Charlie', 'stack': 200.0, 'hole_cards': '7s2h', 'position': 2}
        ]
        
        for player_data in players_data:
            player = Player(hand_id=hand.id, **player_data)
            db.session.add(player)
        
        # Create actions
        actions_data = [
            {'street': 'preflop', 'player_name': 'Charlie', 'action_type': 'fold', 'amount': 0, 'action_order': 0},
            {'street': 'preflop', 'player_name': 'Alice', 'action_type': 'raise', 'amount': 6, 'action_order': 1},
            {'street': 'preflop', 'player_name': 'Bob', 'action_type': 'call', 'amount': 0, 'action_order': 2},
            {'street': 'flop', 'player_name': 'Alice', 'action_type': 'bet', 'amount': 8, 'action_order': 3},
            {'street': 'flop', 'player_name': 'Bob', 'action_type': 'fold', 'amount': 0, 'action_order': 4}
        ]
        
        for action_data in actions_data:
            action = Action(hand_id=hand.id, **action_data)
            db.session.add(action)
        
        db.session.commit()
        
        # Verify the complete scenario
        saved_hand = Hand.query.filter_by(play_id='complex-scenario').first()
        
        # Check hand
        self.assertEqual(saved_hand.board, 'AhKd5c9s3d')
        
        # Check players
        self.assertEqual(len(saved_hand.players), 3)
        alice = next(p for p in saved_hand.players if p.name == 'Alice')
        self.assertEqual(alice.hole_cards, 'AsKh')
        self.assertEqual(alice.stack, 100.0)
        
        # Check actions
        self.assertEqual(len(saved_hand.actions), 5)
        actions = sorted(saved_hand.actions, key=lambda a: a.action_order)
        
        # Verify action sequence
        self.assertEqual(actions[0].player_name, 'Charlie')
        self.assertEqual(actions[0].action_type, 'fold')
        self.assertEqual(actions[1].player_name, 'Alice')
        self.assertEqual(actions[1].action_type, 'raise')
        self.assertEqual(actions[1].amount, 6)
        
        # Check street progression
        preflop_actions = [a for a in actions if a.street == 'preflop']
        flop_actions = [a for a in actions if a.street == 'flop']
        self.assertEqual(len(preflop_actions), 3)
        self.assertEqual(len(flop_actions), 2)


if __name__ == '__main__':
    unittest.main()