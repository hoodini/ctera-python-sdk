"""Bulk user operations."""
import logging
from typing import List, Dict, Any
from .operations import BulkOperationManager

logger = logging.getLogger('cterasdk.bulk')

class BulkUserOperations:
    """Bulk operations for user management."""
    
    def __init__(self, portal):
        self.portal = portal
        self.manager = BulkOperationManager()
    
    def create_users(self, users: List[Dict[str, Any]], max_concurrent: int = 10):
        """Bulk create users."""
        self.manager.max_concurrent = max_concurrent
        
        for user in users:
            self.manager.add_operation(
                f"create_user_{user['username']}",
                self.portal.users.add,
                user['username'], user['email'], user['first_name'], user['last_name']
            )
        
        return self.manager.execute_async()
    
    def delete_users(self, usernames: List[str], max_concurrent: int = 10):
        """Bulk delete users."""
        self.manager.max_concurrent = max_concurrent
        
        for username in usernames:
            self.manager.add_operation(
                f"delete_user_{username}",
                self.portal.users.delete,
                username
            )
        
        return self.manager.execute_async()

