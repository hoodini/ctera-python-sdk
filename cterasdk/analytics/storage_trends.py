"""
Storage utilization trends and capacity planning analytics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict


logger = logging.getLogger('cterasdk.analytics')


class StorageTrendsAnalytics:
    """
    Provides analytics for storage utilization and capacity planning.
    """
    
    def __init__(self, portal):
        """
        Initialize storage trends analytics.
        
        :param portal: Portal client instance
        """
        self.portal = portal
    
    def get_storage_growth_trend(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get storage growth trend over time.
        
        :param datetime start_date: Start date
        :param datetime end_date: End date
        :param str granularity: Data granularity (hourly, daily, weekly, monthly)
        :return: List of storage data points over time
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        logger.info("Analyzing storage growth from %s to %s", start_date, end_date)
        
        trend_data = []
        
        try:
            # Would fetch historical storage data from portal
            storage_snapshots = self._fetch_storage_snapshots(start_date, end_date, granularity)
            
            for snapshot in storage_snapshots:
                trend_data.append({
                    'timestamp': snapshot['timestamp'].isoformat(),
                    'total_used_gb': snapshot['used_bytes'] / (1024 ** 3),
                    'total_capacity_gb': snapshot['capacity_bytes'] / (1024 ** 3),
                    'utilization_percent': (snapshot['used_bytes'] / snapshot['capacity_bytes']) * 100,
                    'growth_rate_gb_per_day': snapshot.get('growth_rate', 0),
                })
        except Exception as e:
            logger.error("Failed to get storage growth trend: %s", str(e))
        
        return trend_data
    
    def predict_capacity_needs(
        self,
        forecast_days: int = 90,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Predict future storage capacity needs using trend analysis.
        
        :param int forecast_days: Number of days to forecast
        :param float confidence_level: Confidence level for prediction
        :return: Capacity prediction data
        """
        logger.info("Predicting capacity needs for next %d days", forecast_days)
        
        prediction = {
            'forecast_days': forecast_days,
            'confidence_level': confidence_level,
            'current_usage_gb': 0,
            'current_capacity_gb': 0,
            'predicted_usage_gb': 0,
            'predicted_capacity_needed_gb': 0,
            'days_until_full': None,
            'recommended_action': '',
        }
        
        try:
            # Fetch historical data
            historical_data = self.get_storage_growth_trend(
                start_date=datetime.now() - timedelta(days=180),
                end_date=datetime.now()
            )
            
            if historical_data:
                # Simple linear regression for prediction
                prediction = self._perform_capacity_forecast(
                    historical_data,
                    forecast_days,
                    confidence_level
                )
        except Exception as e:
            logger.error("Failed to predict capacity needs: %s", str(e))
        
        return prediction
    
    def get_storage_by_user(
        self,
        top_n: int = 20,
        include_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get storage usage by user.
        
        :param int top_n: Number of top users to return
        :param bool include_details: Whether to include detailed breakdowns
        :return: List of user storage data
        """
        logger.info("Analyzing storage usage by user (top %d)", top_n)
        
        user_storage = []
        
        try:
            # Would query user storage quotas and usage from portal
            users = self._fetch_user_storage_data()
            
            sorted_users = sorted(
                users,
                key=lambda x: x.get('used_bytes', 0),
                reverse=True
            )[:top_n]
            
            for user in sorted_users:
                user_data = {
                    'username': user['username'],
                    'used_gb': user['used_bytes'] / (1024 ** 3),
                    'quota_gb': user['quota_bytes'] / (1024 ** 3),
                    'utilization_percent': (user['used_bytes'] / user['quota_bytes']) * 100 if user['quota_bytes'] > 0 else 0,
                }
                
                if include_details:
                    user_data['file_count'] = user.get('file_count', 0)
                    user_data['folder_count'] = user.get('folder_count', 0)
                    user_data['largest_files'] = user.get('largest_files', [])
                
                user_storage.append(user_data)
        except Exception as e:
            logger.error("Failed to get storage by user: %s", str(e))
        
        return user_storage
    
    def get_storage_by_file_type(self) -> Dict[str, Any]:
        """
        Get storage distribution by file type.
        
        :return: File type distribution data
        """
        logger.info("Analyzing storage by file type")
        
        file_type_data = {
            'total_size_gb': 0,
            'file_types': defaultdict(lambda: {'size_gb': 0, 'count': 0, 'percentage': 0}),
        }
        
        try:
            # Would query file metadata from portal
            file_stats = self._fetch_file_type_statistics()
            
            total_bytes = sum(stat['size_bytes'] for stat in file_stats)
            file_type_data['total_size_gb'] = total_bytes / (1024 ** 3)
            
            for stat in file_stats:
                file_type = stat['extension'] or 'no_extension'
                size_gb = stat['size_bytes'] / (1024 ** 3)
                percentage = (stat['size_bytes'] / total_bytes) * 100 if total_bytes > 0 else 0
                
                file_type_data['file_types'][file_type] = {
                    'size_gb': size_gb,
                    'count': stat['count'],
                    'percentage': percentage,
                }
        except Exception as e:
            logger.error("Failed to get storage by file type: %s", str(e))
        
        return file_type_data
    
    def identify_storage_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify opportunities for storage optimization.
        
        :return: List of optimization recommendations
        """
        logger.info("Identifying storage optimization opportunities")
        
        opportunities = []
        
        try:
            # Analyze various aspects for optimization
            
            # Check for duplicate files
            duplicates = self._find_duplicate_files()
            if duplicates:
                total_wasted = sum(d['size_bytes'] for d in duplicates) / (1024 ** 3)
                opportunities.append({
                    'type': 'duplicate_files',
                    'description': f'Found {len(duplicates)} duplicate files',
                    'potential_savings_gb': total_wasted,
                    'priority': 'high' if total_wasted > 100 else 'medium'
                })
            
            # Check for old unused files
            old_files = self._find_old_unused_files(days=365)
            if old_files:
                total_old = sum(f['size_bytes'] for f in old_files) / (1024 ** 3)
                opportunities.append({
                    'type': 'old_unused_files',
                    'description': f'Found {len(old_files)} files not accessed in 1 year',
                    'potential_savings_gb': total_old,
                    'priority': 'medium'
                })
            
            # Check for temp/cache files
            temp_files = self._find_temporary_files()
            if temp_files:
                total_temp = sum(f['size_bytes'] for f in temp_files) / (1024 ** 3)
                opportunities.append({
                    'type': 'temporary_files',
                    'description': f'Found {len(temp_files)} temporary/cache files',
                    'potential_savings_gb': total_temp,
                    'priority': 'low'
                })
        except Exception as e:
            logger.error("Failed to identify optimization opportunities: %s", str(e))
        
        return sorted(opportunities, key=lambda x: x['potential_savings_gb'], reverse=True)
    
    def _fetch_storage_snapshots(self, start_date: datetime, end_date: datetime, granularity: str) -> List[Dict]:
        """Fetch storage snapshots (placeholder)"""
        return []
    
    def _fetch_user_storage_data(self) -> List[Dict]:
        """Fetch user storage data (placeholder)"""
        return []
    
    def _fetch_file_type_statistics(self) -> List[Dict]:
        """Fetch file type statistics (placeholder)"""
        return []
    
    def _perform_capacity_forecast(self, historical_data: List[Dict], forecast_days: int, confidence: float) -> Dict:
        """Perform capacity forecasting using trend analysis"""
        # Would implement linear regression or more sophisticated forecasting
        return {}
    
    def _find_duplicate_files(self) -> List[Dict]:
        """Find duplicate files (placeholder)"""
        return []
    
    def _find_old_unused_files(self, days: int) -> List[Dict]:
        """Find old unused files (placeholder)"""
        return []
    
    def _find_temporary_files(self) -> List[Dict]:
        """Find temporary files (placeholder)"""
        return []

