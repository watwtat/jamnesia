#!/usr/bin/env python3
"""
Suggested improvements for edge case handling
"""

# 1. JSON Validation Decorator
from functools import wraps

from flask import jsonify, request

from models import Position


def validate_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON format"}), 400
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"JSON parsing error: {str(e)}"}), 400

    return wrapper


# 2. Stack Validation
def validate_stack(stack_value):
    """Validate stack amounts"""
    if not isinstance(stack_value, (int, float)):
        raise ValueError("Stack must be a number")
    if stack_value < 0:
        raise ValueError("Stack cannot be negative")
    if stack_value > 1_000_000:  # Reasonable upper limit
        raise ValueError("Stack amount too large")
    return float(stack_value)


# 3. Enhanced Position Handling
class PositionManager:
    @staticmethod
    def assign_positions(players_count: int) -> list:
        """Assign positions based on player count with game type awareness"""
        if players_count == 0:
            return []
        elif players_count == 1:
            return [0]  # Heads-up special case
        elif players_count == 2:
            return [Position.SB, Position.BB]
        elif players_count <= 6:
            # 6-max positions
            positions = [
                Position.SB,
                Position.BB,
                Position.UTG,
                Position.MP,
                Position.CO,
                Position.BTN,
            ]
            return positions[:players_count]
        elif players_count <= 9:
            # Full ring positions
            positions = [
                Position.SB,
                Position.BB,
                Position.UTG,
                Position.UTG1,
                Position.MP,
                Position.LJ,
                Position.HJ,
                Position.CO,
                Position.BTN,
            ]
            return positions[:players_count]
        else:
            # 10+ players - use enum for first 9, then integers
            positions = list(Position)
            positions.extend(range(9, players_count))
            return positions


# 4. Robust Amount Validation
def validate_amount(amount, context="amount"):
    """Validate monetary amounts"""
    if amount is None:
        return 0.0

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {context}: must be a number")

    if amount < 0:
        raise ValueError(f"{context} cannot be negative")

    if amount > 1_000_000:
        raise ValueError(f"{context} too large")

    # Round to 2 decimal places for currency
    return round(amount, 2)


# 5. Action Validation
def validate_action(action, players):
    """Validate individual action"""
    required_fields = ["player_name", "action_type"]
    for field in required_fields:
        if field not in action:
            raise ValueError(f"Action missing required field: {field}")

    # Validate player exists
    player_names = [p["name"] for p in players]
    if action["player_name"] not in player_names:
        raise ValueError(f"Player {action['player_name']} not found")

    # Validate action type
    valid_actions = ["fold", "check", "call", "bet", "raise"]
    if action["action_type"] not in valid_actions:
        raise ValueError(f"Invalid action type: {action['action_type']}")

    # Validate amount for betting actions
    if action["action_type"] in ["bet", "raise"]:
        if "amount" not in action or action["amount"] <= 0:
            raise ValueError(f"{action['action_type']} requires positive amount")


# 6. PHH Generation with Better Precision
def generate_phh_with_precision(stacks):
    """Generate PHH while preserving precision where possible"""
    # Use integers for whole numbers, preserve decimals for fractional
    formatted_stacks = []
    for stack in stacks:
        if stack == int(stack):
            formatted_stacks.append(str(int(stack)))
        else:
            formatted_stacks.append(f"{stack:.2f}")
    return formatted_stacks


if __name__ == "__main__":
    print("Edge case improvement suggestions:")
    print("1. Add JSON validation decorator to all API endpoints")
    print("2. Implement stack amount validation")
    print("3. Add position assignment logic for different game types")
    print("4. Validate all monetary amounts")
    print("5. Comprehensive action validation")
    print("6. Preserve precision in PHH generation")
