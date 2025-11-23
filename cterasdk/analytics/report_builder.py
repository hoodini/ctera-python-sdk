"""
Custom report builder with filters and aggregations.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum


logger = logging.getLogger('cterasdk.analytics')


class ReportFormat(str, Enum):
    """Report output formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"


class AggregationType(str, Enum):
    """Aggregation types"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


class ReportFilter:
    """
    Filter for report data.
    """
    
    def __init__(self):
        """Initialize report filter"""
        self.filters: List[Dict[str, Any]] = []
    
    def add_equals(self, field: str, value: Any) -> 'ReportFilter':
        """Add equals filter"""
        self.filters.append({
            'field': field,
            'operator': '==',
            'value': value
        })
        return self
    
    def add_greater_than(self, field: str, value: Any) -> 'ReportFilter':
        """Add greater than filter"""
        self.filters.append({
            'field': field,
            'operator': '>',
            'value': value
        })
        return self
    
    def add_less_than(self, field: str, value: Any) -> 'ReportFilter':
        """Add less than filter"""
        self.filters.append({
            'field': field,
            'operator': '<',
            'value': value
        })
        return self
    
    def add_in(self, field: str, values: List[Any]) -> 'ReportFilter':
        """Add in filter"""
        self.filters.append({
            'field': field,
            'operator': 'in',
            'value': values
        })
        return self
    
    def add_contains(self, field: str, value: str) -> 'ReportFilter':
        """Add contains filter"""
        self.filters.append({
            'field': field,
            'operator': 'contains',
            'value': value
        })
        return self
    
    def add_custom(self, filter_func: Callable) -> 'ReportFilter':
        """Add custom filter function"""
        self.filters.append({
            'field': '_custom',
            'operator': 'custom',
            'value': filter_func
        })
        return self
    
    def apply(self, data: List[Dict]) -> List[Dict]:
        """Apply filters to data"""
        filtered_data = data
        
        for filter_def in self.filters:
            if filter_def['operator'] == 'custom':
                filtered_data = [item for item in filtered_data if filter_def['value'](item)]
            else:
                filtered_data = self._apply_standard_filter(filtered_data, filter_def)
        
        return filtered_data
    
    def _apply_standard_filter(self, data: List[Dict], filter_def: Dict) -> List[Dict]:
        """Apply standard filter"""
        field = filter_def['field']
        operator = filter_def['operator']
        value = filter_def['value']
        
        filtered = []
        for item in data:
            item_value = self._get_nested_value(item, field)
            
            if operator == '==' and item_value == value:
                filtered.append(item)
            elif operator == '>' and item_value > value:
                filtered.append(item)
            elif operator == '<' and item_value < value:
                filtered.append(item)
            elif operator == 'in' and item_value in value:
                filtered.append(item)
            elif operator == 'contains' and isinstance(item_value, str) and value in item_value:
                filtered.append(item)
        
        return filtered
    
    @staticmethod
    def _get_nested_value(data: Dict, field: str) -> Any:
        """Get nested field value using dot notation"""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


class ReportBuilder:
    """
    Custom report builder with filters and aggregations.
    """
    
    def __init__(self, portal):
        """
        Initialize report builder.
        
        :param portal: Portal client instance
        """
        self.portal = portal
        self.title = "Custom Report"
        self.description = ""
        self.data_sources: List[Dict[str, Any]] = []
        self.filters: List[ReportFilter] = []
        self.aggregations: List[Dict[str, Any]] = []
        self.sort_by: Optional[str] = None
        self.sort_descending: bool = False
        self.limit: Optional[int] = None
    
    def set_title(self, title: str) -> 'ReportBuilder':
        """Set report title"""
        self.title = title
        return self
    
    def set_description(self, description: str) -> 'ReportBuilder':
        """Set report description"""
        self.description = description
        return self
    
    def add_data_source(
        self,
        source_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> 'ReportBuilder':
        """
        Add a data source to the report.
        
        :param str source_type: Type of data source (users, devices, files, logs, etc.)
        :param dict params: Parameters for fetching data
        """
        self.data_sources.append({
            'type': source_type,
            'params': params or {}
        })
        return self
    
    def add_filter(self, report_filter: ReportFilter) -> 'ReportBuilder':
        """Add filter to report"""
        self.filters.append(report_filter)
        return self
    
    def add_aggregation(
        self,
        field: str,
        aggregation_type: AggregationType,
        group_by: Optional[str] = None
    ) -> 'ReportBuilder':
        """
        Add aggregation to report.
        
        :param str field: Field to aggregate
        :param AggregationType aggregation_type: Type of aggregation
        :param str group_by: Optional field to group by
        """
        self.aggregations.append({
            'field': field,
            'type': aggregation_type,
            'group_by': group_by
        })
        return self
    
    def sort(self, field: str, descending: bool = False) -> 'ReportBuilder':
        """
        Set sort order for report.
        
        :param str field: Field to sort by
        :param bool descending: Sort in descending order
        """
        self.sort_by = field
        self.sort_descending = descending
        return self
    
    def set_limit(self, limit: int) -> 'ReportBuilder':
        """Set maximum number of records to return"""
        self.limit = limit
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Build and execute the report.
        
        :return: Report data
        """
        logger.info("Building report: %s", self.title)
        
        report = {
            'title': self.title,
            'description': self.description,
            'generated_at': datetime.now().isoformat(),
            'data': [],
            'summary': {}
        }
        
        try:
            # Fetch data from sources
            all_data = []
            for source in self.data_sources:
                data = self._fetch_data_source(source)
                all_data.extend(data)
            
            # Apply filters
            for filter_obj in self.filters:
                all_data = filter_obj.apply(all_data)
            
            # Apply aggregations
            if self.aggregations:
                aggregated_data = self._apply_aggregations(all_data)
                report['data'] = aggregated_data
            else:
                report['data'] = all_data
            
            # Sort data
            if self.sort_by:
                report['data'] = self._sort_data(report['data'], self.sort_by, self.sort_descending)
            
            # Apply limit
            if self.limit:
                report['data'] = report['data'][:self.limit]
            
            # Generate summary
            report['summary'] = self._generate_summary(report['data'])
        except Exception as e:
            logger.error("Failed to build report: %s", str(e))
            report['error'] = str(e)
        
        return report
    
    def export(self, format: ReportFormat, output_path: str) -> bool:
        """
        Export report to file.
        
        :param ReportFormat format: Output format
        :param str output_path: Path to output file
        :return: True if successful
        """
        report = self.build()
        
        try:
            if format == ReportFormat.JSON:
                return self._export_json(report, output_path)
            elif format == ReportFormat.CSV:
                return self._export_csv(report, output_path)
            elif format == ReportFormat.HTML:
                return self._export_html(report, output_path)
            elif format == ReportFormat.PDF:
                return self._export_pdf(report, output_path)
        except Exception as e:
            logger.error("Failed to export report: %s", str(e))
            return False
    
    def _fetch_data_source(self, source: Dict[str, Any]) -> List[Dict]:
        """Fetch data from source (placeholder)"""
        # Would implement actual data fetching from portal API
        return []
    
    def _apply_aggregations(self, data: List[Dict]) -> List[Dict]:
        """Apply aggregations to data"""
        if not self.aggregations:
            return data
        
        aggregated = []
        
        for agg in self.aggregations:
            if agg['group_by']:
                # Group by aggregation
                from collections import defaultdict
                groups = defaultdict(list)
                
                for item in data:
                    group_key = ReportFilter._get_nested_value(item, agg['group_by'])
                    groups[group_key].append(item)
                
                for group_key, group_items in groups.items():
                    values = [ReportFilter._get_nested_value(item, agg['field']) for item in group_items]
                    values = [v for v in values if v is not None]
                    
                    aggregated.append({
                        agg['group_by']: group_key,
                        f"{agg['type']}_{agg['field']}": self._calculate_aggregation(values, agg['type'])
                    })
            else:
                # Simple aggregation
                values = [ReportFilter._get_nested_value(item, agg['field']) for item in data]
                values = [v for v in values if v is not None]
                
                aggregated.append({
                    'field': agg['field'],
                    'aggregation': agg['type'].value,
                    'result': self._calculate_aggregation(values, agg['type'])
                })
        
        return aggregated if aggregated else data
    
    @staticmethod
    def _calculate_aggregation(values: List[Any], agg_type: AggregationType) -> Any:
        """Calculate aggregation"""
        if not values:
            return None
        
        if agg_type == AggregationType.SUM:
            return sum(values)
        elif agg_type == AggregationType.AVG:
            return sum(values) / len(values)
        elif agg_type == AggregationType.MIN:
            return min(values)
        elif agg_type == AggregationType.MAX:
            return max(values)
        elif agg_type == AggregationType.COUNT:
            return len(values)
    
    @staticmethod
    def _sort_data(data: List[Dict], sort_by: str, descending: bool) -> List[Dict]:
        """Sort data"""
        return sorted(
            data,
            key=lambda x: ReportFilter._get_nested_value(x, sort_by) or '',
            reverse=descending
        )
    
    @staticmethod
    def _generate_summary(data: List[Dict]) -> Dict[str, Any]:
        """Generate report summary"""
        return {
            'total_records': len(data),
            'fields': list(data[0].keys()) if data else []
        }
    
    @staticmethod
    def _export_json(report: Dict, output_path: str) -> bool:
        """Export to JSON"""
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return True
    
    @staticmethod
    def _export_csv(report: Dict, output_path: str) -> bool:
        """Export to CSV"""
        import csv
        if not report['data']:
            return False
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=report['data'][0].keys())
            writer.writeheader()
            writer.writerows(report['data'])
        return True
    
    @staticmethod
    def _export_html(report: Dict, output_path: str) -> bool:
        """Export to HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report['title']}</title>
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <h1>{report['title']}</h1>
            <p>{report['description']}</p>
            <p>Generated: {report['generated_at']}</p>
            <p>Total Records: {report['summary']['total_records']}</p>
        </body>
        </html>
        """
        with open(output_path, 'w') as f:
            f.write(html)
        return True
    
    @staticmethod
    def _export_pdf(report: Dict, output_path: str) -> bool:
        """Export to PDF (placeholder - would require additional library)"""
        logger.warning("PDF export not yet implemented")
        return False

