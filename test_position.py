#!/usr/bin/env python3
"""
Test cases for Position enum functionality
"""

import unittest

from models import Position


class TestPosition(unittest.TestCase):
    """Test Position enum basic functionality"""

    def test_position_values(self):
        """Test that Position enum has correct values"""
        self.assertEqual(Position.SB, 0)
        self.assertEqual(Position.BB, 1)
        self.assertEqual(Position.UTG, 2)
        self.assertEqual(Position.UTG1, 3)
        self.assertEqual(Position.MP, 4)
        self.assertEqual(Position.LJ, 5)
        self.assertEqual(Position.HJ, 6)
        self.assertEqual(Position.CO, 7)
        self.assertEqual(Position.BTN, 8)

    def test_position_names(self):
        """Test that Position enum has correct names"""
        self.assertEqual(Position.SB.name, "SB")
        self.assertEqual(Position.BB.name, "BB")
        self.assertEqual(Position.UTG.name, "UTG")
        self.assertEqual(Position.UTG1.name, "UTG1")
        self.assertEqual(Position.MP.name, "MP")
        self.assertEqual(Position.LJ.name, "LJ")
        self.assertEqual(Position.HJ.name, "HJ")
        self.assertEqual(Position.CO.name, "CO")
        self.assertEqual(Position.BTN.name, "BTN")

    def test_position_count(self):
        """Test that we have the expected number of positions"""
        self.assertEqual(len(Position), 9)

    def test_position_iteration(self):
        """Test that Position enum can be iterated"""
        positions = list(Position)
        expected_names = ["SB", "BB", "UTG", "UTG1", "MP", "LJ", "HJ", "CO", "BTN"]
        actual_names = [pos.name for pos in positions]
        self.assertEqual(actual_names, expected_names)

    def test_position_from_value(self):
        """Test creating Position from integer values"""
        self.assertEqual(Position(0), Position.SB)
        self.assertEqual(Position(1), Position.BB)
        self.assertEqual(Position(8), Position.BTN)

    def test_invalid_position_value(self):
        """Test that invalid values raise ValueError"""
        with self.assertRaises(ValueError):
            Position(99)
        with self.assertRaises(ValueError):
            Position(-1)


class TestPositionDisplayName(unittest.TestCase):
    """Test Position.get_display_name method"""

    def test_get_display_name_valid_positions(self):
        """Test get_display_name for valid position values"""
        self.assertEqual(Position.get_display_name(0), "SB")
        self.assertEqual(Position.get_display_name(1), "BB")
        self.assertEqual(Position.get_display_name(2), "UTG")
        self.assertEqual(Position.get_display_name(3), "UTG1")
        self.assertEqual(Position.get_display_name(4), "MP")
        self.assertEqual(Position.get_display_name(5), "LJ")
        self.assertEqual(Position.get_display_name(6), "HJ")
        self.assertEqual(Position.get_display_name(7), "CO")
        self.assertEqual(Position.get_display_name(8), "BTN")

    def test_get_display_name_invalid_positions(self):
        """Test get_display_name for invalid position values"""
        self.assertEqual(Position.get_display_name(9), "P9")
        self.assertEqual(Position.get_display_name(10), "P10")
        self.assertEqual(Position.get_display_name(99), "P99")
        self.assertEqual(Position.get_display_name(-1), "P-1")

    def test_get_display_name_all_enum_values(self):
        """Test get_display_name for all enum values"""
        for position in Position:
            display_name = Position.get_display_name(position.value)
            self.assertEqual(display_name, position.name)


class TestPositionComparison(unittest.TestCase):
    """Test Position enum comparison operations"""

    def test_position_ordering(self):
        """Test that positions are ordered correctly"""
        self.assertTrue(Position.SB < Position.BB)
        self.assertTrue(Position.BB < Position.UTG)
        self.assertTrue(Position.UTG < Position.UTG1)
        self.assertTrue(Position.UTG1 < Position.MP)
        self.assertTrue(Position.MP < Position.LJ)
        self.assertTrue(Position.LJ < Position.HJ)
        self.assertTrue(Position.HJ < Position.CO)
        self.assertTrue(Position.CO < Position.BTN)

    def test_position_equality(self):
        """Test position equality"""
        self.assertEqual(Position.SB, Position.SB)
        self.assertEqual(Position.BTN, Position.BTN)
        self.assertNotEqual(Position.SB, Position.BB)

    def test_position_integer_comparison(self):
        """Test comparison with integers"""
        self.assertEqual(Position.SB, 0)
        self.assertEqual(Position.BTN, 8)
        self.assertTrue(Position.SB < 1)
        self.assertTrue(Position.BTN > 7)


class TestPositionIntEnum(unittest.TestCase):
    """Test that Position works as IntEnum"""

    def test_position_arithmetic(self):
        """Test arithmetic operations on Position"""
        self.assertEqual(Position.SB + 1, 1)
        self.assertEqual(Position.BB - 1, 0)
        self.assertEqual(Position.BTN * 2, 16)

    def test_position_as_int(self):
        """Test using Position as integer"""
        positions = [Position.SB, Position.BB, Position.UTG]
        values = [int(pos) for pos in positions]
        self.assertEqual(values, [0, 1, 2])

    def test_position_in_range(self):
        """Test Position values in range operations"""
        for i in range(9):
            position = Position(i)
            self.assertIn(position.value, range(9))


if __name__ == "__main__":
    unittest.main()
