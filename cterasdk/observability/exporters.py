"""
Metrics exporters for various monitoring backends.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List
from .metrics import Metric, MetricsCollector


logger = logging.getLogger('cterasdk.observability')


class MetricsExporter(ABC):
    """Base class for metrics exporters"""
    
    @abstractmethod
    def export(self, metrics: List[Metric]) -> bool:
        """
        Export metrics.
        
        :param list metrics: List of metrics to export
        :return: True if successful, False otherwise
        """
        pass


class ConsoleExporter(MetricsExporter):
    """
    Exports metrics to console/logs.
    """
    
    def __init__(self, pretty_print: bool = True):
        """
        Initialize console exporter.
        
        :param bool pretty_print: Whether to pretty-print JSON
        """
        self.pretty_print = pretty_print
    
    def export(self, metrics: List[Metric]) -> bool:
        """Export metrics to console"""
        try:
            metrics_data = [m.to_dict() for m in metrics]
            
            if self.pretty_print:
                output = json.dumps(metrics_data, indent=2)
            else:
                output = json.dumps(metrics_data)
            
            logger.info("Metrics Export:\n%s", output)
            return True
        except Exception as e:
            logger.error("Failed to export metrics to console: %s", str(e))
            return False


class PrometheusExporter(MetricsExporter):
    """
    Exports metrics in Prometheus format.
    """
    
    def export(self, metrics: List[Metric]) -> bool:
        """Export metrics in Prometheus format"""
        try:
            lines = []
            
            for metric in metrics:
                # Convert to Prometheus naming convention
                name = metric.name.replace('.', '_')
                
                # Add tags
                if metric.tags:
                    tag_str = ','.join(f'{k}="{v}"' for k, v in metric.tags.items())
                    metric_line = f'{name}{{{tag_str}}} {metric.value}'
                else:
                    metric_line = f'{name} {metric.value}'
                
                lines.append(metric_line)
            
            prometheus_output = '\n'.join(lines)
            logger.debug("Prometheus Metrics:\n%s", prometheus_output)
            return True
        except Exception as e:
            logger.error("Failed to export metrics to Prometheus format: %s", str(e))
            return False


class FileExporter(MetricsExporter):
    """
    Exports metrics to a file.
    """
    
    def __init__(self, file_path: str, format: str = 'json'):
        """
        Initialize file exporter.
        
        :param str file_path: Path to output file
        :param str format: Output format (json or prometheus)
        """
        self.file_path = file_path
        self.format = format.lower()
    
    def export(self, metrics: List[Metric]) -> bool:
        """Export metrics to file"""
        try:
            with open(self.file_path, 'w') as f:
                if self.format == 'json':
                    metrics_data = [m.to_dict() for m in metrics]
                    json.dump(metrics_data, f, indent=2)
                elif self.format == 'prometheus':
                    for metric in metrics:
                        name = metric.name.replace('.', '_')
                        if metric.tags:
                            tag_str = ','.join(f'{k}="{v}"' for k, v in metric.tags.items())
                            f.write(f'{name}{{{tag_str}}} {metric.value}\n')
                        else:
                            f.write(f'{name} {metric.value}\n')
            
            logger.debug("Metrics exported to file: %s", self.file_path)
            return True
        except Exception as e:
            logger.error("Failed to export metrics to file: %s", str(e))
            return False


class HTTPExporter(MetricsExporter):
    """
    Exports metrics to an HTTP endpoint.
    """
    
    def __init__(self, url: str, headers: dict = None):
        """
        Initialize HTTP exporter.
        
        :param str url: Target URL
        :param dict headers: HTTP headers
        """
        self.url = url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    def export(self, metrics: List[Metric]) -> bool:
        """Export metrics via HTTP POST"""
        try:
            import aiohttp
            import asyncio
            
            async def post_metrics():
                metrics_data = [m.to_dict() for m in metrics]
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.url,
                        json=metrics_data,
                        headers=self.headers
                    ) as response:
                        return response.status < 400
            
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(post_metrics())
            return success
        except Exception as e:
            logger.error("Failed to export metrics via HTTP: %s", str(e))
            return False

