"""Main CLI entry point."""
import sys
import argparse
import logging
from typing import Optional
from .commands import CommandRegistry
from .formatters import OutputFormatter, OutputFormat

logger = logging.getLogger('cterasdk.cli')


def main(args: Optional[list] = None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='ctera',
        description='CTERA SDK Command Line Interface'
    )
    
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--profile', default='default', help='Configuration profile')
    parser.add_argument('--format', choices=['json', 'yaml', 'table', 'csv'], default='table', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Users commands
    users_parser = subparsers.add_parser('users', help='User management')
    users_subparsers = users_parser.add_subparsers(dest='users_command')
    
    list_users = users_subparsers.add_parser('list', help='List users')
    list_users.add_argument('--limit', type=int, default=100, help='Max users to list')
    
    create_user = users_subparsers.add_parser('create', help='Create user')
    create_user.add_argument('username', help='Username')
    create_user.add_argument('email', help='Email address')
    create_user.add_argument('--first-name', required=True, help='First name')
    create_user.add_argument('--last-name', required=True, help='Last name')
    
    delete_user = users_subparsers.add_parser('delete', help='Delete user')
    delete_user.add_argument('username', help='Username to delete')
    
    # Files commands
    files_parser = subparsers.add_parser('files', help='File operations')
    files_subparsers = files_parser.add_subparsers(dest='files_command')
    
    list_files = files_subparsers.add_parser('list', help='List files')
    list_files.add_argument('path', help='Folder path')
    
    upload_file = files_subparsers.add_parser('upload', help='Upload file')
    upload_file.add_argument('local_path', help='Local file path')
    upload_file.add_argument('remote_path', help='Remote destination path')
    
    download_file = files_subparsers.add_parser('download', help='Download file')
    download_file.add_argument('remote_path', help='Remote file path')
    download_file.add_argument('local_path', help='Local destination path')
    
    # Devices commands
    devices_parser = subparsers.add_parser('devices', help='Device management')
    devices_subparsers = devices_parser.add_subparsers(dest='devices_command')
    
    list_devices = devices_subparsers.add_parser('list', help='List devices')
    
    # Reports commands
    reports_parser = subparsers.add_parser('reports', help='Generate reports')
    reports_parser.add_argument('--type', choices=['storage', 'users', 'activity'], default='storage')
    reports_parser.add_argument('--output', help='Output file path')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Start interactive mode')
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if parsed_args.version:
        print("CTERA SDK CLI v1.0.0")
        return 0
    
    # Setup logging
    if parsed_args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Execute command
    registry = CommandRegistry()
    formatter = OutputFormatter(OutputFormat(parsed_args.format))
    
    try:
        result = registry.execute(parsed_args)
        formatted_output = formatter.format(result)
        print(formatted_output)
        return 0
    except Exception as e:
        logger.error("Command failed: %s", str(e))
        return 1


if __name__ == '__main__':
    sys.exit(main())

