# CTERA Python SDK

[![CI](https://github.com/ctera/ctera-python-sdk/workflows/CI/badge.svg)](https://github.com/ctera/ctera-python-sdk/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/ctera-python-sdk/badge/?version=latest)](https://ctera-python-sdk.readthedocs.io/en/latest)
[![PyPI version](https://img.shields.io/pypi/v/cterasdk)](https://pypi.org/pypi/cterasdk)
[![License](https://img.shields.io/pypi/l/cterasdk)](https://opensource.org/licenses/Apache-2.0)
[![Python Versions](https://img.shields.io/pypi/pyversions/cterasdk)](https://pypi.org/pypi/cterasdk)

A powerful Python SDK for automating and managing CTERA's Global File System. This library makes it easy to control cloud storage, configure edge devices, manage users, and handle file operations programmatically.

## 🎯 What Does This SDK Do?

Think of CTERA as a global file system that works across cloud and edge devices. This SDK is your remote control for that system. With it, you can:

- **Manage Cloud Storage** - Create and configure cloud portals, set up storage, manage users and permissions
- **Control Edge Devices** - Configure CTERA Edge Filers (network storage devices) remotely
- **Handle Files** - Upload, download, browse, and manage files across your global file system
- **Automate Tasks** - Script repetitive operations like user provisioning, device setup, and backup configurations
- **Monitor Systems** - Query logs, check device status, and track system health

## 🏗️ How Is The Code Organized?

The SDK is split into several main components:

### 📁 Core Components

```
cterasdk/
├── core/          # Portal/Cloud management (the brain of the system)
├── edge/          # Edge device management (local storage devices)
├── asynchronous/  # Async versions of core and edge operations
├── direct/        # Direct data access (high-performance file operations)
├── objects/       # High-level interfaces (GlobalAdmin, ServicesPortal, Edge, Drive)
└── clients/       # HTTP clients and communication layers
```

### 🧠 Core Module (Portal Management)

The `core` module manages your CTERA Portal - the central cloud management system:

- **Users & Groups** - Create, modify, delete user accounts and groups
- **Devices** - Register and manage edge devices
- **Cloud Storage** - Configure cloud sync, backups, and storage policies
- **Administration** - System settings, licenses, reports, and monitoring
- **File Operations** - Browse and manage files in the cloud namespace

**Key Files:**
- `users.py` - User account management
- `devices.py` - Edge device registration and control
- `cloudfs.py` - Cloud file system operations
- `portals.py` - Multi-tenant portal management
- `files/` - File browsing and I/O operations

### 🖥️ Edge Module (Device Management)

The `edge` module controls CTERA Edge Filers - physical or virtual appliances at your locations:

- **Network Configuration** - Set up networking, VPN, routing
- **File Sharing** - Configure SMB, NFS, FTP, AFP shares
- **Local Users** - Manage local device users and permissions
- **Backup & Sync** - Configure cloud sync and backup policies
- **Services** - Enable/disable device services (antivirus, deduplication, etc.)

**Key Files:**
- `shares.py` - File share configuration (SMB/NFS)
- `network.py` - Network settings
- `users.py` - Local user management
- `backup.py` - Backup configuration
- `sync.py` - Cloud synchronization settings

### ⚡ Asynchronous Module

Async versions of core and edge operations for high-performance applications:

- Non-blocking API calls
- Concurrent operations
- Better performance for bulk operations
- Same functionality as synchronous versions

### 📦 Direct Module

High-performance direct data access bypassing REST APIs:

- Fast file downloads directly from cloud storage
- Handles compression and encryption
- Streaming support for large files
- Ideal for data migration and backup tools

### 🎭 Objects Module

High-level interfaces that make the SDK easy to use:

- **GlobalAdmin** - Manage the entire CTERA portal as an administrator
- **ServicesPortal** - Manage multi-tenant services
- **Edge** - Control individual edge devices
- **Drive** - Personal cloud drive operations
- **Async versions** - AsyncGlobalAdmin, AsyncServicesPortal, AsyncEdge

These objects wrap the lower-level modules and provide a clean, intuitive API.

## 🚀 Quick Start

### Installation

```bash
pip install cterasdk
```

### Connect to Portal (Cloud)

```python
from cterasdk import GlobalAdmin

# Connect to your CTERA Portal
admin = GlobalAdmin('portal.example.com')
admin.login('admin-user', 'password')

# Create a new user
admin.users.add('john.doe', 'john@example.com', 'John', 'Doe')

# List all devices
devices = admin.devices.list_devices()

# Browse cloud files
files = admin.cloudfs.list_folder('/users/john.doe')

admin.logout()
```

### Connect to Edge Device

```python
from cterasdk import Edge

# Connect to an edge device
edge = Edge('192.168.1.100')
edge.login('admin', 'password')

# Create a network share
edge.shares.add('SharedFolder', '/path/to/folder')

# Configure cloud sync
edge.sync.enable()

# Check device status
status = edge.power.status()

edge.logout()
```

### Async Operations

```python
from cterasdk import AsyncGlobalAdmin
import asyncio

async def manage_portal():
    admin = AsyncGlobalAdmin('portal.example.com')
    await admin.login('admin-user', 'password')
    
    # Concurrent operations
    users, devices = await asyncio.gather(
        admin.users.list_users(),
        admin.devices.list_devices()
    )
    
    await admin.logout()

asyncio.run(manage_portal())
```

## 📚 What Can You Build With This?

### Automation Scripts
- Bulk user provisioning
- Automated device deployment
- Scheduled backup configurations
- User lifecycle management

### Integration Tools
- Connect CTERA with your identity provider (AD, LDAP)
- Integrate with monitoring systems
- Build custom management dashboards
- Create workflow automation

### Data Management
- Automated file migrations
- Backup verification scripts
- Storage reporting tools
- Data governance automation

### DevOps
- Infrastructure as Code (IaC) for CTERA
- CI/CD integration for configuration management
- Automated testing of storage infrastructure

## 🔧 Common Use Cases

### 1. Bulk User Creation

```python
admin = GlobalAdmin('portal.example.com')
admin.login('admin', 'password')

users = [
    {'username': 'user1', 'email': 'user1@example.com', 'first_name': 'User', 'last_name': 'One'},
    {'username': 'user2', 'email': 'user2@example.com', 'first_name': 'User', 'last_name': 'Two'},
]

for user in users:
    admin.users.add(user['username'], user['email'], user['first_name'], user['last_name'])
```

### 2. Device Configuration Backup

```python
edge = Edge('192.168.1.100')
edge.login('admin', 'password')

# Export configuration
config = edge.config.export()

# Save to file
with open('edge-config-backup.xml', 'w') as f:
    f.write(config)
```

### 3. File Migration

```python
from cterasdk import GlobalAdmin

admin = GlobalAdmin('portal.example.com')
admin.login('admin', 'password')

# Download files from cloud
files = admin.cloudfs.list_folder('/source/path')
for file in files:
    admin.cloudfs.download('/source/path/' + file.name, '/local/destination/' + file.name)
```

## 🧪 Testing

The SDK includes comprehensive unit tests:

```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run tests with tox
tox

# Run specific tests
python -m pytest tests/ut/core/
```

## 📖 Documentation

- **Full API Documentation**: [Read the Docs](https://ctera-python-sdk.readthedocs.io/en/latest/)
- **User Guides**: Located in `docs/source/UserGuides/`
  - Portal Management Guide
  - Edge Device Guide
  - Direct Data Services
  - Miscellaneous Topics

## 🛠️ Development

### Project Structure

```
ctera-python-sdk/
├── cterasdk/           # Main SDK code
│   ├── core/           # Portal management
│   ├── edge/           # Edge device management
│   ├── asynchronous/   # Async operations
│   ├── direct/         # Direct data access
│   ├── objects/        # High-level interfaces
│   ├── clients/        # HTTP clients
│   ├── lib/            # Utilities and helpers
│   ├── common/         # Shared code
│   ├── exceptions/     # Custom exceptions
│   └── convert/        # Data serialization
├── docs/               # Documentation
├── tests/              # Unit tests
└── requirements.txt    # Dependencies
```

### Building Documentation

```bash
cd docs
pip install -r requirements.txt
make html
# Open docs/build/html/index.html
```

## 🔐 Authentication & Security

The SDK supports multiple authentication methods:

- **Username/Password** - Basic authentication
- **Session Management** - Automatic session handling
- **SSL/TLS** - Secure communications
- **Token-based Auth** - For service accounts

## 🐛 Error Handling

The SDK provides detailed exception classes:

```python
from cterasdk import exceptions

try:
    admin.users.add('existing-user', 'email@example.com', 'First', 'Last')
except exceptions.CTERAException as e:
    print(f"Error: {e}")
```

Common exception types:
- `CTERAException` - Base exception
- `ObjectNotFoundException` - Resource not found
- `InvalidCredentialsException` - Authentication failed
- `NetworkException` - Connection issues

## 📋 Requirements

- Python 3.10 or higher
- Network access to CTERA Portal or Edge devices
- Valid credentials with appropriate permissions

## 🤝 Contributing

Contributions are welcome! The codebase follows standard Python conventions:

- PEP 8 style guide
- Type hints where applicable
- Comprehensive unit tests
- Clear documentation

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details

## 🔗 Useful Links

- [PyPI Package](https://pypi.org/project/cterasdk/)
- [Official Documentation](https://ctera-python-sdk.readthedocs.io/)
- [Issue Tracker](https://github.com/ctera/ctera-python-sdk/issues)
- [CTERA Website](https://www.ctera.com/)

## 💡 Tips & Best Practices

1. **Always logout** - Use `try/finally` or context managers to ensure clean disconnections
2. **Use async for bulk operations** - Better performance when handling many devices or users
3. **Enable logging** - The SDK uses Python's logging module for debugging
4. **Test in dev first** - Always test scripts in a development environment
5. **Handle exceptions** - Network issues and API errors can happen, plan accordingly

## 🎓 Learning Path

1. **Start with Objects** - Use `GlobalAdmin` and `Edge` classes for simple scripts
2. **Explore Modules** - Dive into specific modules (users, devices, shares) for advanced features
3. **Try Async** - Use asynchronous operations for performance-critical applications
4. **Read the Docs** - Check the full API documentation for detailed information

## 🌟 Why Use This SDK?

- **Comprehensive** - Complete coverage of CTERA Portal and Edge APIs
- **Well-Documented** - Extensive documentation and examples
- **Production-Ready** - Used in real-world deployments
- **Actively Maintained** - Regular updates and bug fixes
- **Type-Safe** - Type hints for better IDE support
- **Tested** - Comprehensive test suite

---

**Made with ❤️ by CTERA Networks**

For questions, issues, or contributions, visit the [GitHub repository](https://github.com/ctera/ctera-python-sdk)

