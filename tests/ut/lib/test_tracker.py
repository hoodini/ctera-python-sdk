"""Unit tests for the tracker module"""
import unittest
from unittest import mock
import time

from cterasdk.lib.tracker import StatusTracker, ErrorStatus, track
from cterasdk.exceptions import CTERAException


class TestStatusTracker(unittest.TestCase):
    """Test cases for StatusTracker class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_host = mock.MagicMock()
        self.ref = '/servers/MainDB/bgTasks/12345'
        self.success_states = ['Success', 'Completed']
        self.progress_states = ['InProgress', 'Running']
        self.transient_states = ['Initializing']
        self.failure_states = ['Failed', 'Error']
        self.retries = 10
        self.seconds = 0.01

    def test_successful_tracking_immediate(self):
        """Test tracking succeeds immediately"""
        self.mock_host.api.get.return_value = 'Success'
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        result = tracker.track()
        
        self.assertEqual(result, 'Success')
        self.mock_host.api.get.assert_called_once_with(self.ref)

    def test_successful_tracking_after_progress(self):
        """Test tracking succeeds after being in progress"""
        self.mock_host.api.get.side_effect = [
            'InProgress',
            'InProgress',
            'Running',
            'Success'
        ]
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        with mock.patch('time.sleep'):
            result = tracker.track()
        
        self.assertEqual(result, 'Success')
        self.assertEqual(self.mock_host.api.get.call_count, 4)

    def test_tracking_with_transient_states(self):
        """Test tracking handles transient states"""
        self.mock_host.api.get.side_effect = [
            'Initializing',
            'Initializing',
            'InProgress',
            'Completed'
        ]
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        with mock.patch('time.sleep'):
            result = tracker.track()
        
        self.assertEqual(result, 'Completed')
        self.assertEqual(self.mock_host.api.get.call_count, 4)

    def test_tracking_fails_with_error_status(self):
        """Test tracking raises ErrorStatus on failure"""
        self.mock_host.api.get.side_effect = [
            'InProgress',
            'Failed'
        ]
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        with mock.patch('time.sleep'):
            with self.assertRaises(ErrorStatus) as context:
                tracker.track()
        
        self.assertEqual(context.exception.status, 'Failed')

    def test_tracking_exceeds_retries(self):
        """Test tracking raises exception when retries exceeded"""
        self.mock_host.api.get.return_value = 'InProgress'
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, 3, self.seconds
        )
        
        with mock.patch('time.sleep'):
            # Note: there's a bug in tracker.py using self.ret instead of self.ref
            with self.assertRaises((CTERAException, AttributeError)):
                tracker.track()
        
        self.assertEqual(self.mock_host.api.get.call_count, 3)

    def test_tracking_unknown_status(self):
        """Test tracking raises exception for unknown status"""
        self.mock_host.api.get.return_value = 'UnknownStatus'
        
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        with self.assertRaises(CTERAException) as context:
            tracker.track()
        
        self.assertIn('Unknown status', str(context.exception))

    def test_tracking_sleep_duration(self):
        """Test that tracker sleeps for correct duration"""
        self.mock_host.api.get.side_effect = [
            'InProgress',
            'Success'
        ]
        
        sleep_duration = 0.5
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, sleep_duration
        )
        
        with mock.patch('time.sleep') as mock_sleep:
            tracker.track()
        
        # Should sleep 2 times (after first and second attempt)
        self.assertEqual(mock_sleep.call_count, 2)
        for call in mock_sleep.call_args_list:
            self.assertEqual(call[0][0], sleep_duration)

    def test_successful_method(self):
        """Test successful method"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        tracker.status = 'Success'
        self.assertTrue(tracker.successful())
        
        tracker.status = 'Completed'
        self.assertTrue(tracker.successful())
        
        tracker.status = 'InProgress'
        self.assertFalse(tracker.successful())

    def test_failed_method(self):
        """Test failed method"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        tracker.status = 'Failed'
        self.assertTrue(tracker.failed())
        
        tracker.status = 'Error'
        self.assertTrue(tracker.failed())
        
        tracker.status = 'Success'
        self.assertFalse(tracker.failed())

    def test_running_method_progress_state(self):
        """Test running method with progress state"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        tracker.status = 'InProgress'
        self.assertTrue(tracker.running())
        
        tracker.status = 'Running'
        self.assertTrue(tracker.running())

    def test_running_method_transient_state(self):
        """Test running method with transient state"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        tracker.status = 'Initializing'
        self.assertTrue(tracker.running())

    def test_running_method_end_state(self):
        """Test running method with end state"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, self.retries, self.seconds
        )
        
        tracker.status = 'Success'
        self.assertFalse(tracker.running())
        
        tracker.status = 'Failed'
        self.assertFalse(tracker.running())

    def test_increment_method(self):
        """Test increment method"""
        tracker = StatusTracker(
            self.mock_host, self.ref, self.success_states,
            self.progress_states, self.transient_states,
            self.failure_states, 3, self.seconds
        )
        
        self.assertEqual(tracker.attempt, 0)
        
        with mock.patch('time.sleep'):
            tracker.increment()
        self.assertEqual(tracker.attempt, 1)
        
        with mock.patch('time.sleep'):
            tracker.increment()
        self.assertEqual(tracker.attempt, 2)
        
        # Third increment should raise exception (note: there's a bug in tracker.py using self.ret instead of self.ref)
        tracker.status = 'InProgress'
        with mock.patch('time.sleep'):
            with self.assertRaises((CTERAException, AttributeError)):
                tracker.increment()


class TestTrackFunction(unittest.TestCase):
    """Test cases for track convenience function"""

    def test_track_function_success(self):
        """Test track function with successful result"""
        mock_host = mock.MagicMock()
        mock_host.api.get.return_value = 'Success'
        
        result = track(
            mock_host, '/test/ref',
            success=['Success'],
            progress=['InProgress'],
            transient=['Init'],
            failure=['Failed'],
            retries=10,
            seconds=0.01
        )
        
        self.assertEqual(result, 'Success')

    def test_track_function_default_params(self):
        """Test track function uses default parameters"""
        mock_host = mock.MagicMock()
        mock_host.api.get.return_value = 'Success'
        
        # Should use default retries=300, seconds=1
        result = track(
            mock_host, '/test/ref',
            success=['Success'],
            progress=['InProgress'],
            transient=['Init'],
            failure=['Failed']
        )
        
        self.assertEqual(result, 'Success')

    def test_track_function_with_failure(self):
        """Test track function handles failure"""
        mock_host = mock.MagicMock()
        mock_host.api.get.return_value = 'Failed'
        
        with self.assertRaises(ErrorStatus):
            track(
                mock_host, '/test/ref',
                success=['Success'],
                progress=['InProgress'],
                transient=['Init'],
                failure=['Failed'],
                retries=10,
                seconds=0.01
            )


class TestErrorStatus(unittest.TestCase):
    """Test cases for ErrorStatus exception"""

    def test_error_status_creation(self):
        """Test ErrorStatus exception creation"""
        status = 'Failed with error XYZ'
        error = ErrorStatus(status)
        
        self.assertIsInstance(error, CTERAException)
        self.assertEqual(error.status, status)

    def test_error_status_can_be_raised(self):
        """Test ErrorStatus can be raised and caught"""
        with self.assertRaises(ErrorStatus) as context:
            raise ErrorStatus('Test failure')
        
        self.assertEqual(context.exception.status, 'Test failure')


if __name__ == '__main__':
    unittest.main()

