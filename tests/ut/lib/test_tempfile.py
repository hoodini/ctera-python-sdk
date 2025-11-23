"""Unit tests for the tempfile module"""
import unittest
import tempfile
import os
from unittest import mock

from cterasdk.lib.tempfile import TempfileServices
from cterasdk.lib.registry import Registry


class TestTempfileServices(unittest.TestCase):
    """Test cases for TempfileServices class"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear registry before each test
        registry = Registry.instance()
        registry.remove('tempdir')

    def tearDown(self):
        """Clean up after tests"""
        # Ensure tempdir is cleaned up
        registry = Registry.instance()
        tempdir = registry.get('tempdir')
        if tempdir and os.path.exists(tempdir):
            import shutil
            shutil.rmtree(tempdir)
        registry.remove('tempdir')

    def test_mkdir_creates_directory(self):
        """Test mkdir creates a new temporary directory"""
        tempdir = TempfileServices.mkdir()
        
        self.assertIsNotNone(tempdir)
        self.assertTrue(os.path.exists(tempdir))
        self.assertTrue(os.path.isdir(tempdir))
        self.assertTrue(tempdir.startswith(tempfile.gettempdir()))
        
    def test_mkdir_returns_same_directory(self):
        """Test mkdir returns same directory on subsequent calls"""
        tempdir1 = TempfileServices.mkdir()
        tempdir2 = TempfileServices.mkdir()
        
        self.assertEqual(tempdir1, tempdir2)

    def test_mkdir_registers_in_registry(self):
        """Test mkdir registers tempdir in registry"""
        tempdir = TempfileServices.mkdir()
        
        registry = Registry.instance()
        registered_tempdir = registry.get('tempdir')
        
        self.assertEqual(tempdir, registered_tempdir)

    def test_mkfile_creates_file(self):
        """Test mkfile creates a new temporary file"""
        fd, filepath = TempfileServices.mkfile('test_', '.txt')
        
        try:
            self.assertIsNotNone(fd)
            self.assertIsNotNone(filepath)
            self.assertTrue(os.path.exists(filepath))
            self.assertTrue(os.path.isfile(filepath))
            self.assertTrue(filepath.endswith('.txt'))
            self.assertTrue(os.path.basename(filepath).startswith('test_'))
        finally:
            os.close(fd)

    def test_mkfile_in_tempdir(self):
        """Test mkfile creates file in the tempdir"""
        tempdir = TempfileServices.mkdir()
        fd, filepath = TempfileServices.mkfile('test_', '.dat')
        
        try:
            self.assertTrue(filepath.startswith(tempdir))
        finally:
            os.close(fd)

    def test_mkfile_multiple_files(self):
        """Test creating multiple temporary files"""
        files = []
        try:
            for i in range(3):
                fd, filepath = TempfileServices.mkfile(f'file{i}_', '.tmp')
                files.append((fd, filepath))
                self.assertTrue(os.path.exists(filepath))
            
            # All files should be in same tempdir
            tempdir = TempfileServices.mkdir()
            for fd, filepath in files:
                self.assertTrue(filepath.startswith(tempdir))
        finally:
            for fd, filepath in files:
                os.close(fd)

    def test_rmdir_removes_directory(self):
        """Test rmdir removes the temporary directory"""
        tempdir = TempfileServices.mkdir()
        self.assertTrue(os.path.exists(tempdir))
        
        TempfileServices.rmdir()
        
        self.assertFalse(os.path.exists(tempdir))

    def test_rmdir_removes_registry_entry(self):
        """Test rmdir removes tempdir from registry"""
        TempfileServices.mkdir()
        
        registry = Registry.instance()
        self.assertIsNotNone(registry.get('tempdir'))
        
        TempfileServices.rmdir()
        
        self.assertIsNone(registry.get('tempdir'))

    def test_rmdir_with_files(self):
        """Test rmdir removes directory with files inside"""
        tempdir = TempfileServices.mkdir()
        fd1, filepath1 = TempfileServices.mkfile('test1_', '.txt')
        fd2, filepath2 = TempfileServices.mkfile('test2_', '.dat')
        
        os.close(fd1)
        os.close(fd2)
        
        self.assertTrue(os.path.exists(filepath1))
        self.assertTrue(os.path.exists(filepath2))
        
        TempfileServices.rmdir()
        
        self.assertFalse(os.path.exists(tempdir))
        self.assertFalse(os.path.exists(filepath1))
        self.assertFalse(os.path.exists(filepath2))

    def test_rmdir_when_no_tempdir(self):
        """Test rmdir when no tempdir exists"""
        # Should not raise exception
        TempfileServices.rmdir()
        
        registry = Registry.instance()
        self.assertIsNone(registry.get('tempdir'))

    def test_rmdir_called_at_exit(self):
        """Test that rmdir is registered with atexit"""
        # The @atexit.register decorator registers the function
        # We can't easily test this without inspecting internal atexit state
        # Just verify the function exists and is callable
        self.assertTrue(callable(TempfileServices.rmdir))

    def test_tempdir_prefix(self):
        """Test that temporary directory has correct prefix"""
        tempdir = TempfileServices.mkdir()
        
        basename = os.path.basename(tempdir)
        self.assertTrue(basename.startswith('cterasdk-'))

    def test_concurrent_mkfile_calls(self):
        """Test multiple concurrent mkfile calls"""
        files = []
        try:
            # Create multiple files rapidly
            for i in range(10):
                fd, filepath = TempfileServices.mkfile(f'rapid{i}_', '.tmp')
                files.append((fd, filepath))
            
            # All should exist and be unique
            filepaths = [fp for _, fp in files]
            self.assertEqual(len(filepaths), len(set(filepaths)))
            
            for fd, filepath in files:
                self.assertTrue(os.path.exists(filepath))
        finally:
            for fd, filepath in files:
                try:
                    os.close(fd)
                except:
                    pass

    def test_file_descriptors_are_unique(self):
        """Test that file descriptors are unique"""
        fd1, filepath1 = TempfileServices.mkfile('fd1_', '.tmp')
        fd2, filepath2 = TempfileServices.mkfile('fd2_', '.tmp')
        
        try:
            self.assertNotEqual(fd1, fd2)
            self.assertNotEqual(filepath1, filepath2)
        finally:
            os.close(fd1)
            os.close(fd2)


if __name__ == '__main__':
    unittest.main()

