"""Unit tests for the retries module"""
import unittest
import asyncio
from unittest import mock

from cterasdk.lib.retries import execute_with_retries


class TestExecuteWithRetries(unittest.TestCase):
    """Test cases for execute_with_retries decorator"""

    def test_successful_execution_first_try(self):
        """Test function succeeds on first try"""
        @execute_with_retries(retries=3, backoff=0.01, max_backoff=1)
        async def successful_function():
            return 'success'
        
        result = asyncio.run(successful_function())
        self.assertEqual(result, 'success')

    def test_successful_execution_after_retries(self):
        """Test function succeeds after some retries"""
        call_count = 0
        
        @execute_with_retries(retries=3, backoff=0.01, max_backoff=1)
        async def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError('Temporary failure')
            return 'success'
        
        result = asyncio.run(sometimes_failing_function())
        self.assertEqual(result, 'success')
        self.assertEqual(call_count, 3)

    def test_failure_after_all_retries(self):
        """Test function fails after all retries exhausted"""
        @execute_with_retries(retries=3, backoff=0.01, max_backoff=1)
        async def always_failing_function():
            raise ValueError('Persistent failure')
        
        with self.assertRaises(ValueError) as context:
            asyncio.run(always_failing_function())
        
        self.assertEqual(str(context.exception), 'Persistent failure')

    def test_retry_count_respected(self):
        """Test that retry count is respected"""
        call_count = 0
        
        @execute_with_retries(retries=5, backoff=0.01, max_backoff=1)
        async def counting_function():
            nonlocal call_count
            call_count += 1
            raise RuntimeError('Always fails')
        
        with self.assertRaises(RuntimeError):
            asyncio.run(counting_function())
        
        self.assertEqual(call_count, 5)

    def test_exponential_backoff(self):
        """Test that exponential backoff is applied"""
        sleep_times = []
        
        @execute_with_retries(retries=4, backoff=0.1, max_backoff=1.0)
        async def failing_function():
            raise ValueError('Test failure')
        
        with mock.patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda t: sleep_times.append(t)
            
            with self.assertRaises(ValueError):
                asyncio.run(failing_function())
        
        # Should have backoff times: 0.1, 0.2, 0.4
        self.assertEqual(len(sleep_times), 3)
        self.assertAlmostEqual(sleep_times[0], 0.1, places=5)
        self.assertAlmostEqual(sleep_times[1], 0.2, places=5)
        self.assertAlmostEqual(sleep_times[2], 0.4, places=5)

    def test_max_backoff_limit(self):
        """Test that max_backoff limit is respected"""
        sleep_times = []
        
        @execute_with_retries(retries=10, backoff=1, max_backoff=5)
        async def failing_function():
            raise ValueError('Test failure')
        
        with mock.patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda t: sleep_times.append(t)
            
            with self.assertRaises(ValueError):
                asyncio.run(failing_function())
        
        # All backoff times should be capped at max_backoff
        for sleep_time in sleep_times:
            self.assertLessEqual(sleep_time, 5)

    def test_async_function_with_return_value(self):
        """Test async function returns correct value"""
        @execute_with_retries(retries=3, backoff=0.01, max_backoff=1)
        async def async_function_with_value():
            await asyncio.sleep(0.001)
            return {'status': 'ok', 'data': [1, 2, 3]}
        
        result = asyncio.run(async_function_with_value())
        self.assertEqual(result, {'status': 'ok', 'data': [1, 2, 3]})

    def test_async_function_with_args(self):
        """Test decorated function with arguments"""
        @execute_with_retries(retries=3, backoff=0.01, max_backoff=1)
        async def function_with_args(a, b, c=None):
            return a + b + (c or 0)
        
        result = asyncio.run(function_with_args(1, 2, c=3))
        self.assertEqual(result, 6)

    def test_different_exception_types(self):
        """Test retries work with different exception types"""
        call_count = 0
        exceptions = [TypeError('Type error'), ValueError('Value error'), KeyError('Key error')]
        
        @execute_with_retries(retries=4, backoff=0.01, max_backoff=1)
        async def multi_exception_function():
            nonlocal call_count
            if call_count < len(exceptions):
                exception = exceptions[call_count]
                call_count += 1
                raise exception
            call_count += 1
            return 'success'
        
        result = asyncio.run(multi_exception_function())
        self.assertEqual(result, 'success')
        self.assertEqual(call_count, 4)

    def test_single_retry(self):
        """Test function with single retry"""
        call_count = 0
        
        @execute_with_retries(retries=1, backoff=0.01, max_backoff=1)
        async def single_retry_function():
            nonlocal call_count
            call_count += 1
            raise ValueError('Always fails')
        
        with self.assertRaises(ValueError):
            asyncio.run(single_retry_function())
        
        self.assertEqual(call_count, 1)

    def test_no_sleep_on_last_attempt(self):
        """Test that no sleep occurs after the last failed attempt"""
        sleep_count = 0
        
        @execute_with_retries(retries=3, backoff=0.1, max_backoff=1)
        async def failing_function():
            raise ValueError('Always fails')
        
        with mock.patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda t: sleep_count or None
            
            with self.assertRaises(ValueError):
                asyncio.run(failing_function())
            
            # Should sleep only between attempts, not after last attempt
            # 3 retries = 2 sleeps (after 1st and 2nd attempt, not after 3rd)
            self.assertEqual(mock_sleep.call_count, 2)

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""
        @execute_with_retries(retries=3, backoff=0.1, max_backoff=1)
        async def documented_function():
            """This is a documented function"""
            return 'result'
        
        self.assertEqual(documented_function.__name__, 'documented_function')
        self.assertEqual(documented_function.__doc__, 'This is a documented function')


if __name__ == '__main__':
    unittest.main()

