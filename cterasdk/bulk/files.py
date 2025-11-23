"""Bulk file operations."""
import logging
from typing import List
from .operations import BulkOperationManager

logger = logging.getLogger('cterasdk.bulk')

class BulkFileOperations:
    """Bulk operations for file management."""
    
    def __init__(self, portal):
        self.portal = portal
        self.manager = BulkOperationManager()
    
    def delete_files(self, file_paths: List[str], max_concurrent: int = 10):
        """Bulk delete files."""
        self.manager.max_concurrent = max_concurrent
        
        for path in file_paths:
            self.manager.add_operation(
                f"delete_file_{path}",
                self.portal.cloudfs.delete,
                path
            )
        
        return self.manager.execute_async()

