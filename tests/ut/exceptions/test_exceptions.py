"""Unit tests for exceptions module"""
import unittest
from unittest import mock

from cterasdk.exceptions.base import CTERAException
from cterasdk.exceptions.auth import AuthenticationError
from cterasdk.exceptions.common import (
    AwaitableTaskException, TaskException, TaskWaitTimeoutError
)
from cterasdk.exceptions.transport import HTTPError, TLSError
from cterasdk.exceptions.session import SessionExpired, NotLoggedIn
from cterasdk.common import Object


class TestCTERAException(unittest.TestCase):
    """Test cases for CTERAException base class"""

    def test_ctera_exception_creation(self):
        """Test creating CTERAException"""
        message = "Test error message"
        exception = CTERAException(message)
        
        self.assertEqual(str(exception), message)
        self.assertIsInstance(exception, Exception)

    def test_ctera_exception_inheritance(self):
        """Test CTERAException inherits from Exception"""
        exception = CTERAException("Test")
        self.assertIsInstance(exception, Exception)

    def test_ctera_exception_can_be_raised(self):
        """Test CTERAException can be raised and caught"""
        with self.assertRaises(CTERAException) as context:
            raise CTERAException("Test exception")
        
        self.assertEqual(str(context.exception), "Test exception")

    def test_ctera_exception_empty_message(self):
        """Test CTERAException with empty message"""
        exception = CTERAException("")
        self.assertEqual(str(exception), "")


class TestAuthenticationError(unittest.TestCase):
    """Test cases for AuthenticationError"""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError"""
        exception = AuthenticationError()
        
        self.assertIsInstance(exception, CTERAException)
        self.assertIn("Authentication failed", str(exception))
        self.assertIn("Invalid username or password", str(exception))

    def test_authentication_error_can_be_raised(self):
        """Test AuthenticationError can be raised and caught"""
        with self.assertRaises(AuthenticationError):
            raise AuthenticationError()

    def test_authentication_error_caught_as_ctera_exception(self):
        """Test AuthenticationError can be caught as CTERAException"""
        with self.assertRaises(CTERAException):
            raise AuthenticationError()


class TestAwaitableTaskException(unittest.TestCase):
    """Test cases for AwaitableTaskException"""

    def test_awaitable_task_exception_creation(self):
        """Test creating AwaitableTaskException"""
        message = "Task execution failed"
        mock_task = mock.MagicMock()
        
        exception = AwaitableTaskException(message, mock_task)
        
        self.assertEqual(str(exception), message)
        self.assertEqual(exception.awaitable_task, mock_task)
        self.assertIsInstance(exception, CTERAException)

    def test_awaitable_task_exception_preserves_task(self):
        """Test AwaitableTaskException preserves awaitable_task"""
        mock_task = mock.MagicMock()
        mock_task.id = 12345
        mock_task.status = 'Failed'
        
        exception = AwaitableTaskException("Error", mock_task)
        
        self.assertEqual(exception.awaitable_task.id, 12345)
        self.assertEqual(exception.awaitable_task.status, 'Failed')

    def test_awaitable_task_exception_can_be_raised(self):
        """Test AwaitableTaskException can be raised and caught"""
        mock_task = mock.MagicMock()
        
        with self.assertRaises(AwaitableTaskException) as context:
            raise AwaitableTaskException("Task failed", mock_task)
        
        self.assertEqual(context.exception.awaitable_task, mock_task)


class TestTaskException(unittest.TestCase):
    """Test cases for TaskException"""

    def test_task_exception_creation(self):
        """Test creating TaskException"""
        message = "Task error"
        task = Object()
        task.id = 999
        task.status = 'Error'
        
        exception = TaskException(message, task)
        
        self.assertEqual(str(exception), message)
        self.assertEqual(exception.task, task)
        self.assertIsInstance(exception, CTERAException)

    def test_task_exception_preserves_task_object(self):
        """Test TaskException preserves task object"""
        task = Object()
        task.id = 123
        task.name = "TestTask"
        task.description = "Test task description"
        
        exception = TaskException("Error occurred", task)
        
        self.assertEqual(exception.task.id, 123)
        self.assertEqual(exception.task.name, "TestTask")
        self.assertEqual(exception.task.description, "Test task description")

    def test_task_exception_can_be_raised(self):
        """Test TaskException can be raised and caught"""
        task = Object()
        
        with self.assertRaises(TaskException) as context:
            raise TaskException("Task execution failed", task)
        
        self.assertEqual(str(context.exception), "Task execution failed")


class TestTaskWaitTimeoutError(unittest.TestCase):
    """Test cases for TaskWaitTimeoutError"""

    def test_task_wait_timeout_error_creation(self):
        """Test creating TaskWaitTimeoutError"""
        task = Object()
        task.id = 456
        duration = 300
        
        exception = TaskWaitTimeoutError(duration, task)
        
        self.assertIsInstance(exception, TaskException)
        self.assertEqual(exception.task, task)
        self.assertIn(str(task.id), str(exception))
        self.assertIn(str(duration), str(exception))

    def test_task_wait_timeout_error_message(self):
        """Test TaskWaitTimeoutError generates correct message"""
        task = Object()
        task.id = 789
        duration = 600
        
        exception = TaskWaitTimeoutError(duration, task)
        
        expected_message = f"Task {task.id} remains pending completion after {duration} second(s)."
        self.assertEqual(str(exception), expected_message)

    def test_task_wait_timeout_error_can_be_raised(self):
        """Test TaskWaitTimeoutError can be raised and caught"""
        task = Object()
        task.id = 111
        
        with self.assertRaises(TaskWaitTimeoutError) as context:
            raise TaskWaitTimeoutError(120, task)
        
        self.assertIn("120 second(s)", str(context.exception))
        self.assertIn("111", str(context.exception))

    def test_task_wait_timeout_error_caught_as_task_exception(self):
        """Test TaskWaitTimeoutError can be caught as TaskException"""
        task = Object()
        task.id = 222
        
        with self.assertRaises(TaskException):
            raise TaskWaitTimeoutError(60, task)


class TestTLSError(unittest.TestCase):
    """Test cases for TLSError"""

    def test_tls_error_creation(self):
        """Test creating TLSError"""
        exception = TLSError("example.com", 443)
        
        self.assertIsInstance(exception, CTERAException)
        self.assertEqual(exception.host, "example.com")
        self.assertEqual(exception.port, 443)
        self.assertIn("TLS handshake", str(exception))

    def test_tls_error_message(self):
        """Test TLSError message format"""
        exception = TLSError("localhost", 8443)
        
        self.assertIn("localhost:8443", str(exception))


class TestSessionExceptions(unittest.TestCase):
    """Test cases for session exceptions"""

    def test_session_expired_creation(self):
        """Test creating SessionExpired"""
        exception = SessionExpired()
        
        self.assertIsInstance(exception, CTERAException)
        self.assertIn("Session expired", str(exception))

    def test_not_logged_in_creation(self):
        """Test creating NotLoggedIn"""
        exception = NotLoggedIn()
        
        self.assertIsInstance(exception, CTERAException)
        self.assertIn("Not logged in", str(exception))


class TestExceptionInheritanceHierarchy(unittest.TestCase):
    """Test cases for exception inheritance hierarchy"""

    def test_all_custom_exceptions_inherit_from_ctera_exception(self):
        """Test all custom exceptions inherit from CTERAException"""
        task = Object()
        task.id = 1
        
        exceptions_to_test = [
            AuthenticationError(),
            AwaitableTaskException("msg", mock.MagicMock()),
            TaskException("msg", task),
            TaskWaitTimeoutError(60, task),
        ]
        
        for exc in exceptions_to_test:
            self.assertIsInstance(exc, CTERAException)
            self.assertIsInstance(exc, Exception)

    def test_exception_catch_hierarchy(self):
        """Test catching specific exceptions as base exception"""
        task = Object()
        task.id = 1
        
        # TaskWaitTimeoutError should be catchable as TaskException
        with self.assertRaises(TaskException):
            raise TaskWaitTimeoutError(60, task)
        
        # TaskWaitTimeoutError should be catchable as CTERAException
        with self.assertRaises(CTERAException):
            raise TaskWaitTimeoutError(60, task)


if __name__ == '__main__':
    unittest.main()

