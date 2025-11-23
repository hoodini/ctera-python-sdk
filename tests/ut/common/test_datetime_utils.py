"""Unit tests for the datetime_utils module"""
import unittest
import datetime

from cterasdk.common.datetime_utils import DateTimeUtils


class TestDateTimeUtils(unittest.TestCase):
    """Test cases for DateTimeUtils class"""

    def test_get_expiration_date_with_boolean_true(self):
        """Test get_expiration_date with True (immediate expiration - yesterday)"""
        result = DateTimeUtils.get_expiration_date(True)
        expected = datetime.date.today() - datetime.timedelta(days=1)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_with_positive_integer(self):
        """Test get_expiration_date with positive integer (days from now)"""
        days = 30
        result = DateTimeUtils.get_expiration_date(days)
        expected = datetime.date.today() + datetime.timedelta(days=days)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_with_zero(self):
        """Test get_expiration_date with zero (today)"""
        result = DateTimeUtils.get_expiration_date(0)
        expected = datetime.date.today()
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_with_negative_integer(self):
        """Test get_expiration_date with negative integer (days in the past)"""
        days = -7
        result = DateTimeUtils.get_expiration_date(days)
        expected = datetime.date.today() + datetime.timedelta(days=days)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_with_date_object(self):
        """Test get_expiration_date with datetime.date object"""
        specific_date = datetime.date(2025, 12, 31)
        result = DateTimeUtils.get_expiration_date(specific_date)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, specific_date)

    def test_get_expiration_date_with_future_date(self):
        """Test get_expiration_date with future date object"""
        future_date = datetime.date.today() + datetime.timedelta(days=365)
        result = DateTimeUtils.get_expiration_date(future_date)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, future_date)

    def test_get_expiration_date_with_past_date(self):
        """Test get_expiration_date with past date object"""
        past_date = datetime.date(2020, 1, 1)
        result = DateTimeUtils.get_expiration_date(past_date)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, past_date)

    def test_get_expiration_date_large_integer(self):
        """Test get_expiration_date with large integer"""
        days = 1000
        result = DateTimeUtils.get_expiration_date(days)
        expected = datetime.date.today() + datetime.timedelta(days=days)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_one_day(self):
        """Test get_expiration_date with one day"""
        result = DateTimeUtils.get_expiration_date(1)
        expected = datetime.date.today() + datetime.timedelta(days=1)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_with_boolean_false(self):
        """Test get_expiration_date with False (should still treat as boolean)"""
        # Note: The implementation treats any boolean as True behavior
        # This test documents current behavior
        result = DateTimeUtils.get_expiration_date(False)
        
        # With False, the first condition (isinstance(expiration, bool)) is True
        # So it should return yesterday
        expected = datetime.date.today() - datetime.timedelta(days=1)
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, expected)

    def test_get_expiration_date_consistency(self):
        """Test that multiple calls in same day return consistent results"""
        result1 = DateTimeUtils.get_expiration_date(10)
        result2 = DateTimeUtils.get_expiration_date(10)
        
        self.assertEqual(result1, result2)

    def test_get_expiration_date_with_today(self):
        """Test get_expiration_date with today's date"""
        today = datetime.date.today()
        result = DateTimeUtils.get_expiration_date(today)
        
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, today)


if __name__ == '__main__':
    unittest.main()

