from datetime import datetime
from enum import IntEnum

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Position(IntEnum):
    """Poker position enumeration"""

    SB = 0  # Small Blind
    BB = 1  # Big Blind
    UTG = 2  # Under The Gun
    UTG1 = 3  # Under The Gun + 1
    MP = 4  # Middle Position
    LJ = 5  # Lojack
    HJ = 6  # Hijack
    CO = 7  # Cutoff
    BTN = 8  # Button

    @classmethod
    def get_display_name(cls, position_value: int) -> str:
        """Get human-readable position name"""
        try:
            return cls(position_value).name
        except ValueError:
            return f"P{position_value}"


class Hand(db.Model):
    """Main poker hand information"""

    __tablename__ = "hands"

    id = db.Column(db.Integer, primary_key=True)
    play_id = db.Column(db.String(100), unique=True, nullable=False)
    game_type = db.Column(
        db.String(50), nullable=False, default="No Limit Texas Holdem"
    )
    board = db.Column(db.String(20))  # Flop, turn, river cards
    small_blind = db.Column(db.Float, nullable=False, default=1.0)
    big_blind = db.Column(db.Float, nullable=False, default=2.0)
    phh_content = db.Column(db.Text)  # Generated PHH file content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    players = db.relationship(
        "Player", backref="hand", lazy=True, cascade="all, delete-orphan"
    )
    actions = db.relationship(
        "Action", backref="hand", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Hand {self.play_id}>"


class Player(db.Model):
    """Player information for each hand"""

    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(db.Integer, db.ForeignKey("hands.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    stack = db.Column(db.Float, nullable=False)
    hole_cards = db.Column(db.String(10))  # "AsKh" format
    position = db.Column(db.String(10))  # "SB", "BB", "UTG", etc.

    def __repr__(self):
        return f"<Player {self.name}>"


class Action(db.Model):
    """Action details for each hand"""

    __tablename__ = "actions"

    id = db.Column(db.Integer, primary_key=True)
    hand_id = db.Column(db.Integer, db.ForeignKey("hands.id"), nullable=False)
    street = db.Column(
        db.String(20), nullable=False
    )  # 'preflop', 'flop', 'turn', 'river'
    player_name = db.Column(db.String(50), nullable=False)
    action_type = db.Column(
        db.String(20), nullable=False
    )  # 'fold', 'call', 'bet', 'raise', 'check'
    amount = db.Column(db.Float, default=0.0)
    pot_size = db.Column(db.Float, default=0.0)  # Pot size after this action
    remaining_stack = db.Column(
        db.Float, default=0.0
    )  # Player's remaining stack after this action
    action_order = db.Column(db.Integer, nullable=False)  # Action sequence order

    def __repr__(self):
        return f"<Action {self.player_name} {self.action_type}>"
