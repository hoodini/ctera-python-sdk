"""Unit tests for the common utils module"""
import unittest
import datetime
import socket
from unittest import mock

from cterasdk.common.utils import (
    union, merge, convert_size, DataUnit, df_military_time,
    day_of_week, BaseObjectRef, parse_base_object_ref,
    Version, utf8_decode, utf8_encode, tcp_connect
)
from cterasdk.common.enum import DayOfWeek


class TestUnionFunction(unittest.TestCase):
    """Test cases for union function"""

    def test_union_no_duplicates(self):
        """Test union with no duplicate elements"""
        g1 = [1, 2, 3]
        g2 = [4, 5, 6]
        result = union(g1, g2)
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])

    def test_union_with_duplicates(self):
        """Test union removes duplicates from second list"""
        g1 = [1, 2, 3]
        g2 = [3, 4, 5]
        result = union(g1, g2)
        self.assertEqual(result, [1, 2, 3, 4, 5])

    def test_union_all_duplicates(self):
        """Test union when all elements are duplicates"""
        g1 = [1, 2, 3]
        g2 = [1, 2, 3]
        result = union(g1, g2)
        self.assertEqual(result, [1, 2, 3])

    def test_union_empty_lists(self):
        """Test union with empty lists"""
        self.assertEqual(union([], []), [])
        self.assertEqual(union([1, 2], []), [1, 2])
        self.assertEqual(union([], [3, 4]), [3, 4])

    def test_union_order_preserved(self):
        """Test union preserves order from first list"""
        g1 = ['a', 'b', 'c']
        g2 = ['d', 'a', 'e']
        result = union(g1, g2)
        self.assertEqual(result, ['a', 'b', 'c', 'd', 'e'])


class TestMergeFunction(unittest.TestCase):
    """Test cases for merge function"""

    def test_merge_no_overlap(self):
        """Test merge with no overlapping keys"""
        d1 = {'a': 1, 'b': 2}
        d2 = {'c': 3, 'd': 4}
        result = merge(d1, d2)
        self.assertEqual(result, {'a': 1, 'b': 2, 'c': 3, 'd': 4})

    def test_merge_with_overlap(self):
        """Test merge with overlapping keys (d2 values take precedence)"""
        d1 = {'a': 1, 'b': 2}
        d2 = {'b': 3, 'c': 4}
        result = merge(d1, d2)
        self.assertEqual(result, {'a': 1, 'b': 3, 'c': 4})

    def test_merge_none_values(self):
        """Test merge with None values"""
        self.assertEqual(merge(None, None), {})
        self.assertEqual(merge({'a': 1}, None), {'a': 1})
        self.assertEqual(merge(None, {'b': 2}), {'b': 2})

    def test_merge_empty_dicts(self):
        """Test merge with empty dictionaries"""
        self.assertEqual(merge({}, {}), {})
        self.assertEqual(merge({'a': 1}, {}), {'a': 1})
        self.assertEqual(merge({}, {'b': 2}), {'b': 2})


class TestDataUnitConversion(unittest.TestCase):
    """Test cases for convert_size function"""

    def test_convert_same_unit(self):
        """Test converting to same unit"""
        self.assertEqual(convert_size(100, DataUnit.MB, DataUnit.MB), 100)
        self.assertEqual(convert_size(50, DataUnit.GB, DataUnit.GB), 50)

    def test_convert_bytes_to_kilobytes(self):
        """Test converting bytes to kilobytes"""
        self.assertEqual(convert_size(1024, DataUnit.B, DataUnit.KB), 1)
        self.assertEqual(convert_size(2048, DataUnit.B, DataUnit.KB), 2)

    def test_convert_kilobytes_to_bytes(self):
        """Test converting kilobytes to bytes"""
        self.assertEqual(convert_size(1, DataUnit.KB, DataUnit.B), 1024)
        self.assertEqual(convert_size(2, DataUnit.KB, DataUnit.B), 2048)

    def test_convert_mb_to_gb(self):
        """Test converting megabytes to gigabytes"""
        self.assertEqual(convert_size(1024, DataUnit.MB, DataUnit.GB), 1)
        self.assertEqual(convert_size(2048, DataUnit.MB, DataUnit.GB), 2)

    def test_convert_gb_to_mb(self):
        """Test converting gigabytes to megabytes"""
        self.assertEqual(convert_size(1, DataUnit.GB, DataUnit.MB), 1024)
        self.assertEqual(convert_size(2, DataUnit.GB, DataUnit.MB), 2048)

    def test_convert_gb_to_tb(self):
        """Test converting gigabytes to terabytes"""
        self.assertEqual(convert_size(1024, DataUnit.GB, DataUnit.TB), 1)

    def test_convert_tb_to_pb(self):
        """Test converting terabytes to petabytes"""
        self.assertEqual(convert_size(1024, DataUnit.TB, DataUnit.PB), 1)

    def test_convert_bytes_to_gb(self):
        """Test converting bytes to gigabytes"""
        self.assertEqual(convert_size(1073741824, DataUnit.B, DataUnit.GB), 1)

    def test_convert_invalid_source_unit(self):
        """Test converting with invalid source unit"""
        with self.assertRaises(ValueError) as context:
            convert_size(100, 'INVALID', DataUnit.GB)
        self.assertIn('Invalid current unit type', str(context.exception))

    def test_convert_invalid_target_unit(self):
        """Test converting with invalid target unit"""
        with self.assertRaises(ValueError) as context:
            convert_size(100, DataUnit.GB, 'INVALID')
        self.assertIn('Invalid target unit type', str(context.exception))

    def test_convert_fractional_result(self):
        """Test conversion that results in fractional value"""
        result = convert_size(512, DataUnit.MB, DataUnit.GB)
        self.assertEqual(result, 0.5)


class TestMilitaryTime(unittest.TestCase):
    """Test cases for df_military_time function"""

    def test_military_time_midnight(self):
        """Test converting midnight to military time"""
        time = datetime.datetime(2025, 1, 1, 0, 0, 0)
        result = df_military_time(time)
        self.assertEqual(result, '00:00:00')

    def test_military_time_noon(self):
        """Test converting noon to military time"""
        time = datetime.datetime(2025, 1, 1, 12, 0, 0)
        result = df_military_time(time)
        self.assertEqual(result, '12:00:00')

    def test_military_time_afternoon(self):
        """Test converting afternoon time to military time"""
        time = datetime.datetime(2025, 1, 1, 15, 30, 45)
        result = df_military_time(time)
        self.assertEqual(result, '15:30:45')

    def test_military_time_invalid_type(self):
        """Test military time with invalid type"""
        with self.assertRaises(ValueError) as context:
            df_military_time("12:00:00")
        self.assertIn('Invalid type', str(context.exception))


class TestDayOfWeek(unittest.TestCase):
    """Test cases for day_of_week function"""

    def test_day_of_week_valid_values(self):
        """Test day_of_week with valid day numbers"""
        # Assuming DayOfWeek enum has these values
        if hasattr(DayOfWeek, 'Sunday'):
            result = day_of_week(DayOfWeek.Sunday)
            self.assertEqual(result, 'Sunday')

    def test_day_of_week_invalid_value(self):
        """Test day_of_week with invalid day number"""
        with self.assertRaises(ValueError) as context:
            day_of_week(999)
        self.assertIn('Invalid day of week', str(context.exception))


class TestBaseObjectRef(unittest.TestCase):
    """Test cases for BaseObjectRef class"""

    def test_create_base_object_ref_minimal(self):
        """Test creating BaseObjectRef with minimal parameters"""
        ref = BaseObjectRef('uid123')
        self.assertEqual(ref.uid, 'uid123')
        self.assertIsNone(ref.tenant)
        self.assertIsNone(ref.classname)
        self.assertIsNone(ref.name)
        self.assertIsNone(ref.more)

    def test_create_base_object_ref_full(self):
        """Test creating BaseObjectRef with all parameters"""
        ref = BaseObjectRef('uid123', tenant='tenant1', classname='User', 
                          name='john', more='info')
        self.assertEqual(ref.uid, 'uid123')
        self.assertEqual(ref.tenant, 'tenant1')
        self.assertEqual(ref.classname, 'User')
        self.assertEqual(ref.name, 'john')
        self.assertEqual(ref.more, 'info')

    def test_in_tenant_context_true(self):
        """Test in_tenant_context returns True when tenant is set"""
        ref = BaseObjectRef('uid123', tenant='tenant1')
        self.assertTrue(ref.in_tenant_context())

    def test_in_tenant_context_false(self):
        """Test in_tenant_context returns False when tenant is None"""
        ref = BaseObjectRef('uid123')
        self.assertFalse(ref.in_tenant_context())

    def test_base_object_ref_str_minimal(self):
        """Test string representation with minimal parameters"""
        ref = BaseObjectRef('uid123')
        self.assertEqual(str(ref), 'objs/uid123////')

    def test_base_object_ref_str_full(self):
        """Test string representation with all parameters"""
        ref = BaseObjectRef('uid123', tenant='tenant1', classname='User',
                          name='john', more='info')
        self.assertEqual(str(ref), 'objs/uid123/tenant1/User/john/info')


class TestParseBaseObjectRef(unittest.TestCase):
    """Test cases for parse_base_object_ref function"""

    def test_parse_valid_minimal_ref(self):
        """Test parsing minimal base object reference"""
        ref_str = 'objs/uid123////'
        result = parse_base_object_ref(ref_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, 'uid123')

    def test_parse_valid_full_ref(self):
        """Test parsing full base object reference"""
        ref_str = 'objs/uid123/tenant1/User/john/info'
        result = parse_base_object_ref(ref_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.uid, 'uid123')
        self.assertEqual(result.tenant, 'tenant1')
        self.assertEqual(result.classname, 'User')
        self.assertEqual(result.name, 'john')
        self.assertEqual(result.more, 'info')

    def test_parse_invalid_ref(self):
        """Test parsing invalid base object reference"""
        ref_str = 'invalid/uid123'
        result = parse_base_object_ref(ref_str)
        self.assertIsNone(result)


class TestVersion(unittest.TestCase):
    """Test cases for Version class"""

    def test_version_equality(self):
        """Test version equality comparison"""
        v = Version('1.0.0')
        self.assertTrue(v == '1.0.0')
        self.assertFalse(v == '1.0.1')

    def test_version_greater_than(self):
        """Test version greater than comparison"""
        v = Version('2.0.0')
        self.assertTrue(v > '1.0.0')
        self.assertFalse(v > '2.0.0')
        self.assertFalse(v > '3.0.0')

    def test_version_less_than(self):
        """Test version less than comparison"""
        v = Version('1.0.0')
        self.assertTrue(v < '2.0.0')
        self.assertFalse(v < '1.0.0')
        self.assertFalse(v < '0.9.0')

    def test_version_greater_or_equal(self):
        """Test version greater than or equal comparison"""
        v = Version('1.5.0')
        self.assertTrue(v >= '1.5.0')
        self.assertTrue(v >= '1.0.0')
        self.assertFalse(v >= '2.0.0')

    def test_version_less_or_equal(self):
        """Test version less than or equal comparison"""
        v = Version('1.5.0')
        self.assertTrue(v <= '1.5.0')
        self.assertTrue(v <= '2.0.0')
        self.assertFalse(v <= '1.0.0')

    def test_version_not_equal(self):
        """Test version not equal comparison"""
        v = Version('1.0.0')
        self.assertTrue(v != '1.0.1')
        self.assertFalse(v != '1.0.0')

    def test_version_str(self):
        """Test version string representation"""
        v = Version('1.2.3')
        self.assertEqual(str(v), '1.2.3')

    def test_version_property(self):
        """Test version property"""
        v = Version('1.2.3')
        self.assertEqual(v.version, '1.2.3')


class TestUTF8Functions(unittest.TestCase):
    """Test cases for UTF-8 encode/decode functions"""

    def test_utf8_encode(self):
        """Test UTF-8 encoding"""
        message = 'Hello, World!'
        encoded = utf8_encode(message)
        self.assertIsInstance(encoded, bytes)
        self.assertEqual(encoded, b'Hello, World!')

    def test_utf8_decode(self):
        """Test UTF-8 decoding"""
        message = b'Hello, World!'
        decoded = utf8_decode(message)
        self.assertIsInstance(decoded, str)
        self.assertEqual(decoded, 'Hello, World!')

    def test_utf8_encode_decode_roundtrip(self):
        """Test encoding and decoding roundtrip"""
        original = 'Test message with unicode: ñ, é, ü'
        encoded = utf8_encode(original)
        decoded = utf8_decode(encoded)
        self.assertEqual(decoded, original)

    def test_utf8_encode_special_chars(self):
        """Test UTF-8 encoding with special characters"""
        message = '日本語 中文 한글'
        encoded = utf8_encode(message)
        decoded = utf8_decode(encoded)
        self.assertEqual(decoded, message)


class TestTCPConnect(unittest.TestCase):
    """Test cases for tcp_connect function"""

    def test_tcp_connect_success(self):
        """Test successful TCP connection"""
        with mock.patch('socket.socket') as mock_socket:
            mock_sock_instance = mock.MagicMock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance
            
            # Should not raise exception
            tcp_connect('localhost', 80)
            
            mock_sock_instance.settimeout.assert_called_once()
            mock_sock_instance.connect_ex.assert_called_once_with(('localhost', 80))

    def test_tcp_connect_failure(self):
        """Test failed TCP connection"""
        with mock.patch('socket.socket') as mock_socket:
            mock_sock_instance = mock.MagicMock()
            mock_sock_instance.connect_ex.return_value = 1  # Connection refused
            mock_socket.return_value = mock_sock_instance
            
            with self.assertRaises(ConnectionError) as context:
                tcp_connect('localhost', 9999)
            
            self.assertIn('Connection error', str(context.exception))

    def test_tcp_connect_gaierror(self):
        """Test TCP connection with address resolution error"""
        with mock.patch('socket.socket') as mock_socket:
            mock_sock_instance = mock.MagicMock()
            mock_sock_instance.connect_ex.side_effect = socket.gaierror('Name resolution failed')
            mock_socket.return_value = mock_sock_instance
            
            with self.assertRaises(ConnectionError) as context:
                tcp_connect('invalid.host.example', 80)
            
            self.assertIn('Connection error', str(context.exception))

    def test_tcp_connect_with_timeout(self):
        """Test TCP connection with custom timeout"""
        with mock.patch('socket.socket') as mock_socket:
            mock_sock_instance = mock.MagicMock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance
            
            tcp_connect('localhost', 80, timeout=5)
            
            mock_sock_instance.settimeout.assert_called_once_with(5)


if __name__ == '__main__':
    unittest.main()

