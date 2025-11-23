# pylint: disable=protected-access
"""Unit tests for the iterator module"""
import unittest
from unittest import mock

from cterasdk.lib.iterator import (
    BaseIterator,
    KeyValueQueryIterator,
    QueryIterator,
    DefaultResponse,
    QueryLogsResponse,
    CursorResponse
)
from cterasdk.common import Object


class TestKeyValueQueryIterator(unittest.TestCase):
    """Test cases for KeyValueQueryIterator"""

    def test_iteration_single_batch(self):
        """Test iterating over a single batch of items"""
        items = ['item1', 'item2', 'item3']
        callback = mock.MagicMock(return_value=items)
        parameter = 'test_param'
        
        iterator = KeyValueQueryIterator(callback, parameter)
        result = list(iterator)
        
        callback.assert_called_once_with(parameter)
        self.assertEqual(result, items)

    def test_iteration_empty_result(self):
        """Test iterating when callback returns empty list"""
        callback = mock.MagicMock(return_value=[])
        parameter = 'test_param'
        
        iterator = KeyValueQueryIterator(callback, parameter)
        result = list(iterator)
        
        callback.assert_called_once_with(parameter)
        self.assertEqual(result, [])

    def test_multiple_iterations(self):
        """Test iterating multiple times over the same iterator"""
        items = ['item1', 'item2']
        callback = mock.MagicMock(return_value=items)
        
        iterator = KeyValueQueryIterator(callback, 'param')
        first_result = list(iterator)
        second_result = list(iterator)
        
        # Iterator should be exhausted after first iteration
        self.assertEqual(first_result, items)
        self.assertEqual(second_result, [])


class TestQueryIterator(unittest.TestCase):
    """Test cases for QueryIterator"""

    def test_single_page_iteration(self):
        """Test iterating over a single page"""
        response = Object()
        response.hasMore = False
        response.objects = ['obj1', 'obj2', 'obj3']
        
        mock_response = DefaultResponse(response)
        callback = mock.MagicMock(return_value=mock_response)
        
        parameter = mock.MagicMock()
        iterator = QueryIterator(callback, parameter)
        result = list(iterator)
        
        self.assertEqual(result, ['obj1', 'obj2', 'obj3'])
        parameter.increment.assert_called_once()

    def test_multi_page_iteration(self):
        """Test iterating over multiple pages"""
        # First page
        response1 = Object()
        response1.hasMore = True
        response1.objects = ['obj1', 'obj2']
        
        # Second page
        response2 = Object()
        response2.hasMore = False
        response2.objects = ['obj3', 'obj4']
        
        mock_response1 = DefaultResponse(response1)
        mock_response2 = DefaultResponse(response2)
        
        callback = mock.MagicMock(side_effect=[mock_response1, mock_response2])
        parameter = mock.MagicMock()
        
        iterator = QueryIterator(callback, parameter)
        result = list(iterator)
        
        self.assertEqual(result, ['obj1', 'obj2', 'obj3', 'obj4'])
        self.assertEqual(callback.call_count, 2)
        self.assertEqual(parameter.increment.call_count, 2)

    def test_empty_page_iteration(self):
        """Test iterating when response has no objects"""
        response = Object()
        response.hasMore = False
        response.objects = []
        
        mock_response = DefaultResponse(response)
        callback = mock.MagicMock(return_value=mock_response)
        parameter = mock.MagicMock()
        
        iterator = QueryIterator(callback, parameter)
        result = list(iterator)
        
        self.assertEqual(result, [])

    def test_many_pages_iteration(self):
        """Test iterating over many pages"""
        responses = []
        for i in range(5):
            response = Object()
            response.hasMore = (i < 4)  # Last page has hasMore=False
            response.objects = [f'obj{i}1', f'obj{i}2']
            responses.append(DefaultResponse(response))
        
        callback = mock.MagicMock(side_effect=responses)
        parameter = mock.MagicMock()
        
        iterator = QueryIterator(callback, parameter)
        result = list(iterator)
        
        expected = ['obj01', 'obj02', 'obj11', 'obj12', 'obj21', 'obj22', 
                    'obj31', 'obj32', 'obj41', 'obj42']
        self.assertEqual(result, expected)
        self.assertEqual(callback.call_count, 5)


class TestDefaultResponse(unittest.TestCase):
    """Test cases for DefaultResponse"""

    def test_more_property(self):
        """Test the more property"""
        response = Object()
        response.hasMore = True
        response.objects = ['obj1']
        
        default_response = DefaultResponse(response)
        self.assertTrue(default_response.more)

    def test_objects_property(self):
        """Test the objects property"""
        response = Object()
        response.hasMore = False
        response.objects = ['obj1', 'obj2', 'obj3']
        
        default_response = DefaultResponse(response)
        self.assertEqual(default_response.objects, ['obj1', 'obj2', 'obj3'])

    def test_no_more_data(self):
        """Test when there is no more data"""
        response = Object()
        response.hasMore = False
        response.objects = []
        
        default_response = DefaultResponse(response)
        self.assertFalse(default_response.more)
        self.assertEqual(default_response.objects, [])


class TestQueryLogsResponse(unittest.TestCase):
    """Test cases for QueryLogsResponse"""

    def test_objects_property_returns_logs(self):
        """Test that objects property returns logs instead of objects"""
        response = Object()
        response.hasMore = True
        response.logs = ['log1', 'log2', 'log3']
        response.objects = ['obj1', 'obj2']  # This should be ignored
        
        logs_response = QueryLogsResponse(response)
        self.assertEqual(logs_response.objects, ['log1', 'log2', 'log3'])
        self.assertTrue(logs_response.more)

    def test_empty_logs(self):
        """Test with empty logs"""
        response = Object()
        response.hasMore = False
        response.logs = []
        
        logs_response = QueryLogsResponse(response)
        self.assertEqual(logs_response.objects, [])
        self.assertFalse(logs_response.more)


class TestCursorResponse(unittest.TestCase):
    """Test cases for CursorResponse"""

    def test_cursor_response_properties(self):
        """Test all properties of CursorResponse"""
        response = Object()
        response.has_more = True
        response.entries = ['entry1', 'entry2', 'entry3']
        response.cursor = 'abc123cursor'
        
        cursor_response = CursorResponse(response)
        self.assertTrue(cursor_response.more)
        self.assertEqual(cursor_response.objects, ['entry1', 'entry2', 'entry3'])
        self.assertEqual(cursor_response.cursor, 'abc123cursor')

    def test_cursor_response_no_more_data(self):
        """Test cursor response when no more data"""
        response = Object()
        response.has_more = False
        response.entries = []
        response.cursor = None
        
        cursor_response = CursorResponse(response)
        self.assertFalse(cursor_response.more)
        self.assertEqual(cursor_response.objects, [])
        self.assertIsNone(cursor_response.cursor)

    def test_cursor_response_with_data_and_cursor(self):
        """Test cursor response with data and cursor for pagination"""
        response = Object()
        response.has_more = True
        response.entries = ['data1', 'data2']
        response.cursor = 'next_page_cursor_xyz'
        
        cursor_response = CursorResponse(response)
        self.assertTrue(cursor_response.more)
        self.assertEqual(len(cursor_response.objects), 2)
        self.assertEqual(cursor_response.cursor, 'next_page_cursor_xyz')


class TestBaseIterator(unittest.TestCase):
    """Test cases for BaseIterator base class"""

    def test_base_iterator_cannot_be_instantiated_directly(self):
        """Test that BaseIterator requires page method implementation"""
        callback = mock.MagicMock()
        parameter = 'test'
        
        iterator = BaseIterator(callback, parameter)
        
        # Should raise NotImplementedError when trying to iterate
        with self.assertRaises(NotImplementedError):
            next(iterator)

    def test_iterator_protocol(self):
        """Test that iterator implements the iterator protocol"""
        callback = mock.MagicMock()
        parameter = 'test'
        
        iterator = KeyValueQueryIterator(callback, parameter)
        self.assertIs(iter(iterator), iterator)


if __name__ == '__main__':
    unittest.main()

