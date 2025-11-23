"""Output formatters for CLI."""
import json
from enum import Enum
from typing import Any, Dict


class OutputFormat(str, Enum):
    """Output format types."""
    JSON = "json"
    YAML = "yaml"
    TABLE = "table"
    CSV = "csv"


class OutputFormatter:
    """Format CLI output in various formats."""
    
    def __init__(self, format: OutputFormat):
        self.format = format
    
    def format(self, data: Any) -> str:
        """Format data according to specified format."""
        if self.format == OutputFormat.JSON:
            return self._format_json(data)
        elif self.format == OutputFormat.YAML:
            return self._format_yaml(data)
        elif self.format == OutputFormat.TABLE:
            return self._format_table(data)
        elif self.format == OutputFormat.CSV:
            return self._format_csv(data)
        return str(data)
    
    def _format_json(self, data: Any) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2)
    
    def _format_yaml(self, data: Any) -> str:
        """Format as YAML."""
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False)
        except ImportError:
            return self._format_json(data)
    
    def _format_table(self, data: Any) -> str:
        """Format as table."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Tabular data
            keys = data[0].keys()
            lines = [" | ".join(keys)]
            lines.append("-" * len(lines[0]))
            for item in data:
                lines.append(" | ".join(str(item.get(k, '')) for k in keys))
            return "\n".join(lines)
        return str(data)
    
    def _format_csv(self, data: Any) -> str:
        """Format as CSV."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        return self._format_json(data)

