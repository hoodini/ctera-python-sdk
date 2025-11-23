"""Progress tracking for bulk operations."""
import logging
from datetime import datetime

logger = logging.getLogger('cterasdk.bulk')

class ProgressTracker:
    """Tracks progress of bulk operations."""
    
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.start_time = datetime.now()
    
    def update(self, completed: int, total: int):
        """Update progress."""
        self.completed = completed
        self.total = total
        percentage = (completed / total) * 100 if total > 0 else 0
        logger.info("Progress: %d/%d (%.1f%%)", completed, total, percentage)
    
    def get_eta(self) -> float:
        """Get estimated time to completion in seconds."""
        if self.completed == 0:
            return 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.completed / elapsed
        remaining = self.total - self.completed
        return remaining / rate if rate > 0 else 0

