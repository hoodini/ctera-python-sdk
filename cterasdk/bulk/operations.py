"""
Core bulk operations framework.
"""

import asyncio
import logging
from typing import List, Optional, Callable, Any, Dict
from enum import Enum
from datetime import datetime


logger = logging.getLogger('cterasdk.bulk')


class OperationStatus(str, Enum):
    """Operation status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class OperationResult:
    """Result of a bulk operation"""
    
    def __init__(self, operation_id: str, status: OperationStatus, data: Any = None, error: Optional[str] = None):
        self.operation_id = operation_id
        self.status = status
        self.data = data
        self.error = error
        self.timestamp = datetime.now()


class BulkOperation:
    """Represents a single operation in a bulk set"""
    
    def __init__(self, operation_id: str, func: Callable, args: tuple, kwargs: dict, rollback_func: Optional[Callable] = None):
        self.operation_id = operation_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.rollback_func = rollback_func
        self.result: Optional[OperationResult] = None


class BulkOperationManager:
    """
    Manages bulk operations with parallel execution, progress tracking, and rollback.
    """
    
    def __init__(self, max_concurrent: int = 10, enable_rollback: bool = True):
        """
        Initialize bulk operation manager.
        
        :param int max_concurrent: Maximum concurrent operations
        :param bool enable_rollback: Whether to enable rollback on failure
        """
        self.max_concurrent = max_concurrent
        self.enable_rollback = enable_rollback
        self.operations: List[BulkOperation] = []
        self.completed_operations: List[BulkOperation] = []
    
    def add_operation(
        self,
        operation_id: str,
        func: Callable,
        *args,
        rollback_func: Optional[Callable] = None,
        **kwargs
    ):
        """
        Add an operation to the bulk set.
        
        :param str operation_id: Unique operation identifier
        :param callable func: Function to execute
        :param args: Function arguments
        :param callable rollback_func: Optional rollback function
        :param kwargs: Function keyword arguments
        """
        operation = BulkOperation(operation_id, func, args, kwargs, rollback_func)
        self.operations.append(operation)
    
    async def execute_async(self, on_progress: Optional[Callable] = None) -> List[OperationResult]:
        """
        Execute all operations asynchronously.
        
        :param callable on_progress: Optional progress callback
        :return: List of operation results
        """
        logger.info("Starting bulk execution of %d operations", len(self.operations))
        
        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_with_semaphore(operation: BulkOperation):
            async with semaphore:
                return await self._execute_single(operation, on_progress)
        
        tasks = [execute_with_semaphore(op) for op in self.operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        failed_ops = [r for r in results if isinstance(r, OperationResult) and r.status == OperationStatus.FAILED]
        
        if failed_ops and self.enable_rollback:
            logger.warning("%d operations failed, initiating rollback", len(failed_ops))
            await self._rollback()
        
        return results
    
    def execute_sync(self, on_progress: Optional[Callable] = None) -> List[OperationResult]:
        """
        Execute all operations synchronously.
        
        :param callable on_progress: Optional progress callback
        :return: List of operation results
        """
        logger.info("Starting bulk execution of %d operations", len(self.operations))
        
        results = []
        
        for operation in self.operations:
            try:
                result = operation.func(*operation.args, **operation.kwargs)
                operation.result = OperationResult(operation.operation_id, OperationStatus.SUCCESS, result)
                self.completed_operations.append(operation)
                
                if on_progress:
                    on_progress(len(self.completed_operations), len(self.operations))
            except Exception as e:
                logger.error("Operation %s failed: %s", operation.operation_id, str(e))
                operation.result = OperationResult(operation.operation_id, OperationStatus.FAILED, error=str(e))
                
                if self.enable_rollback:
                    self._rollback_sync()
                    break
            
            results.append(operation.result)
        
        return results
    
    async def _execute_single(self, operation: BulkOperation, on_progress: Optional[Callable]) -> OperationResult:
        """Execute a single operation"""
        try:
            if asyncio.iscoroutinefunction(operation.func):
                result = await operation.func(*operation.args, **operation.kwargs)
            else:
                result = operation.func(*operation.args, **operation.kwargs)
            
            operation.result = OperationResult(operation.operation_id, OperationStatus.SUCCESS, result)
            self.completed_operations.append(operation)
            
            if on_progress:
                if asyncio.iscoroutinefunction(on_progress):
                    await on_progress(len(self.completed_operations), len(self.operations))
                else:
                    on_progress(len(self.completed_operations), len(self.operations))
            
            return operation.result
        except Exception as e:
            logger.error("Operation %s failed: %s", operation.operation_id, str(e))
            return OperationResult(operation.operation_id, OperationStatus.FAILED, error=str(e))
    
    async def _rollback(self):
        """Rollback completed operations"""
        logger.info("Rolling back %d operations", len(self.completed_operations))
        
        for operation in reversed(self.completed_operations):
            if operation.rollback_func:
                try:
                    if asyncio.iscoroutinefunction(operation.rollback_func):
                        await operation.rollback_func(*operation.args, **operation.kwargs)
                    else:
                        operation.rollback_func(*operation.args, **operation.kwargs)
                    
                    operation.result.status = OperationStatus.ROLLED_BACK
                    logger.debug("Rolled back operation: %s", operation.operation_id)
                except Exception as e:
                    logger.error("Failed to rollback operation %s: %s", operation.operation_id, str(e))
    
    def _rollback_sync(self):
        """Rollback completed operations synchronously"""
        logger.info("Rolling back %d operations", len(self.completed_operations))
        
        for operation in reversed(self.completed_operations):
            if operation.rollback_func:
                try:
                    operation.rollback_func(*operation.args, **operation.kwargs)
                    operation.result.status = OperationStatus.ROLLED_BACK
                    logger.debug("Rolled back operation: %s", operation.operation_id)
                except Exception as e:
                    logger.error("Failed to rollback operation %s: %s", operation.operation_id, str(e))
    
    def clear(self):
        """Clear all operations"""
        self.operations.clear()
        self.completed_operations.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        results = [op.result for op in self.operations if op.result]
        
        return {
            'total': len(self.operations),
            'completed': len(self.completed_operations),
            'success': sum(1 for r in results if r.status == OperationStatus.SUCCESS),
            'failed': sum(1 for r in results if r.status == OperationStatus.FAILED),
            'rolled_back': sum(1 for r in results if r.status == OperationStatus.ROLLED_BACK),
        }

