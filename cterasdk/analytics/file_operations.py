"""
File operations analytics for tracking upload/download patterns and file activity.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict


logger = logging.getLogger('cterasdk.analytics')


class FileOperationsAnalytics:
    """
    Provides analytics for file operations and activity patterns.
    """
    
    def __init__(self, portal):
        """
        Initialize file operations analytics.
        
        :param portal: Portal client instance
        """
        self.portal = portal
    
    def get_upload_download_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = 'day'
    ) -> Dict[str, Any]:
        """
        Get upload and download statistics.
        
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :param str group_by: Grouping interval (hour, day, week, month)
        :return: Upload/download statistics
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info("Analyzing upload/download stats from %s to %s", start_date, end_date)
        
        stats = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_uploads': 0,
            'total_downloads': 0,
            'total_upload_bytes': 0,
            'total_download_bytes': 0,
            'avg_upload_size_mb': 0,
            'avg_download_size_mb': 0,
            'peak_upload_time': None,
            'peak_download_time': None,
            'timeline': []
        }
        
        try:
            operations = self._fetch_file_operations(start_date, end_date)
            stats = self._aggregate_operations(operations, group_by, stats)
        except Exception as e:
            logger.error("Failed to get upload/download stats: %s", str(e))
        
        return stats
    
    def get_most_accessed_files(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        operation_type: str = 'all'
    ) -> List[Dict[str, Any]]:
        """
        Get most accessed files.
        
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :param int limit: Number of files to return
        :param str operation_type: Type of operation (all, read, write, delete)
        :return: List of most accessed files
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info("Finding most accessed files (type: %s)", operation_type)
        
        accessed_files = []
        
        try:
            file_access_data = self._fetch_file_access_logs(start_date, end_date, operation_type)
            
            # Count access frequency
            access_counts = defaultdict(lambda: {
                'path': '',
                'access_count': 0,
                'unique_users': set(),
                'total_bytes_transferred': 0,
                'last_accessed': None
            })
            
            for access in file_access_data:
                path = access['file_path']
                access_counts[path]['path'] = path
                access_counts[path]['access_count'] += 1
                access_counts[path]['unique_users'].add(access['username'])
                access_counts[path]['total_bytes_transferred'] += access.get('bytes', 0)
                
                if not access_counts[path]['last_accessed'] or access['timestamp'] > access_counts[path]['last_accessed']:
                    access_counts[path]['last_accessed'] = access['timestamp']
            
            # Sort by access count
            sorted_files = sorted(
                access_counts.values(),
                key=lambda x: x['access_count'],
                reverse=True
            )[:limit]
            
            for file_data in sorted_files:
                accessed_files.append({
                    'path': file_data['path'],
                    'access_count': file_data['access_count'],
                    'unique_users': len(file_data['unique_users']),
                    'total_bytes_transferred_mb': file_data['total_bytes_transferred'] / (1024 ** 2),
                    'last_accessed': file_data['last_accessed'].isoformat() if file_data['last_accessed'] else None
                })
        except Exception as e:
            logger.error("Failed to get most accessed files: %s", str(e))
        
        return accessed_files
    
    def get_file_sharing_activity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get file sharing activity statistics.
        
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :return: File sharing statistics
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info("Analyzing file sharing activity")
        
        sharing_stats = {
            'total_shares_created': 0,
            'total_shares_accessed': 0,
            'most_shared_files': [],
            'share_types': defaultdict(int),
            'top_sharers': [],
        }
        
        try:
            shares_data = self._fetch_sharing_activity(start_date, end_date)
            sharing_stats = self._analyze_sharing_activity(shares_data, sharing_stats)
        except Exception as e:
            logger.error("Failed to get file sharing activity: %s", str(e))
        
        return sharing_stats
    
    def get_file_modification_patterns(
        self,
        folder_path: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get file modification patterns for detecting unusual activity.
        
        :param str folder_path: Optional specific folder to analyze
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :return: Modification pattern data
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        logger.info("Analyzing file modification patterns")
        
        patterns = {
            'avg_modifications_per_day': 0,
            'peak_modification_times': [],
            'modification_velocity': [],  # Changes over time
            'unusual_activity_detected': False,
            'anomalies': []
        }
        
        try:
            modifications = self._fetch_file_modifications(folder_path, start_date, end_date)
            patterns = self._detect_modification_patterns(modifications, patterns)
        except Exception as e:
            logger.error("Failed to analyze modification patterns: %s", str(e))
        
        return patterns
    
    def get_failed_operations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        operation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get failed file operations for troubleshooting.
        
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :param str operation_type: Optional operation type filter
        :return: List of failed operations
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        logger.info("Fetching failed operations")
        
        failed_ops = []
        
        try:
            failures = self._fetch_failed_operations(start_date, end_date, operation_type)
            
            for failure in failures:
                failed_ops.append({
                    'timestamp': failure['timestamp'].isoformat(),
                    'operation': failure['operation_type'],
                    'file_path': failure['file_path'],
                    'username': failure['username'],
                    'error_code': failure['error_code'],
                    'error_message': failure['error_message'],
                })
        except Exception as e:
            logger.error("Failed to get failed operations: %s", str(e))
        
        return failed_ops
    
    def _fetch_file_operations(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch file operations (placeholder)"""
        return []
    
    def _fetch_file_access_logs(self, start_date: datetime, end_date: datetime, operation_type: str) -> List[Dict]:
        """Fetch file access logs (placeholder)"""
        return []
    
    def _fetch_sharing_activity(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch sharing activity (placeholder)"""
        return []
    
    def _fetch_file_modifications(self, folder_path: Optional[str], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch file modifications (placeholder)"""
        return []
    
    def _fetch_failed_operations(self, start_date: datetime, end_date: datetime, operation_type: Optional[str]) -> List[Dict]:
        """Fetch failed operations (placeholder)"""
        return []
    
    def _aggregate_operations(self, operations: List[Dict], group_by: str, stats: Dict) -> Dict:
        """Aggregate file operations"""
        return stats
    
    def _analyze_sharing_activity(self, shares_data: List[Dict], stats: Dict) -> Dict:
        """Analyze sharing activity"""
        return stats
    
    def _detect_modification_patterns(self, modifications: List[Dict], patterns: Dict) -> Dict:
        """Detect modification patterns"""
        return patterns

