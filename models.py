from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Hand(db.Model):
    """Main poker hand information"""
    __tablename__ = 'hands'
    
    id = db.Column(db.Integer, primary_key=True)
    play_id = db.Column(db.String(100), unique=True, nullable=False)
    game_type = db.Column(db.String(50), nullable=False, default='No Limit Texas Holdem')
    board = db.Column(db.String(20))  # Flop, turn, river cards
    small_blind = db.Column(db.Float, nullable=False, default=1.0)
    big_blind = db.Column(db.Float, nullable=False, default=2.0)
    phh_content = db.Column(db.Text)  # Generated PHH file content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    players = db.relationship('Player', backref='hand', lazy=True, cascade='all, delete-orphan')
    actions = db.relationship('Action', backref='hand', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hand {self.play_id}>'

class Player(db.Model):
    """Player information for each hand"""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(db.Integer, db.ForeignKey('hands.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    stack = db.Column(db.Float, nullable=False)
    hole_cards = db.Column(db.String(10))  # "AsKh" format
    position = db.Column(db.Integer)  # 0=SB, 1=BB, 2=UTG, etc.
    
    def __repr__(self):
        return f'<Player {self.name}>'

class Action(db.Model):
    """Action details for each hand"""
    __tablename__ = 'actions'
    
    id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(db.Integer, db.ForeignKey('hands.id'), nullable=False)
    street = db.Column(db.String(20), nullable=False)  # 'preflop', 'flop', 'turn', 'river'
    player_name = db.Column(db.String(50), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # 'fold', 'call', 'bet', 'raise', 'check'
    amount = db.Column(db.Float, default=0.0)
    action_order = db.Column(db.Integer, nullable=False)  # Action sequence order
    
    def __repr__(self):
        return f'<Action {self.player_name} {self.action_type}>'