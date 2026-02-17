# TestZeus MCP Server Documentation

Welcome to the TestZeus MCP Server documentation! This directory contains comprehensive guides for both users and developers.

## 📚 Documentation Structure

### User Documentation
- **[Main README](../README.md)** - Installation, configuration, and basic usage
- **[Usage Examples](examples/USAGE_EXAMPLES.md)** - Real-world examples with Claude Desktop and Cursor IDE

### Developer Documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete development setup and contribution guide
- **[Architecture Overview](../README.md#architecture)** - Technical architecture details

## 🚀 Quick Start

### For End Users

1. **Install the package:**
   ```bash
   pip install testzeus-mcp-server
   ```

2. **Configure your MCP client** (Claude Desktop or Cursor)
3. **Start using TestZeus conversationally!**

See the [Usage Examples](examples/USAGE_EXAMPLES.md) for detailed configuration steps and real-world scenarios.

### For Developers

1. **Clone and setup:**
   ```bash
   git clone https://github.com/testzeus/testzeus-mcp-server.git
   cd testzeus-mcp-server
   uv sync --dev
   ```

2. **Read the [Developer Guide](DEVELOPER_GUIDE.md)** for complete setup instructions

## 📖 Key Documentation Sections

### Installation & Configuration
- [PyPI Installation](../README.md#option-1-install-from-pypi-recommended)
- [Source Installation](../README.md#option-2-install-from-source)
- [Claude Desktop Setup](../README.md#claude-desktop)
- [Cursor IDE Setup](../README.md#cursor-ide)

### Usage & Examples
- [Basic Operations](../README.md#basic-operations)
- [Available Tools](../README.md#available-tools)
- [Resource Browsing](../README.md#available-resources)
- [Real-World Examples](examples/USAGE_EXAMPLES.md#real-world-usage-examples)

### Development & Contributing
- [Development Setup](DEVELOPER_GUIDE.md#development-setup)
- [Code Quality](DEVELOPER_GUIDE.md#code-quality)
- [Adding Features](DEVELOPER_GUIDE.md#adding-new-features)
- [Release Process](DEVELOPER_GUIDE.md#release-process)

### Troubleshooting
- [Common Issues](../README.md#common-issues)
- [Debug Mode](../README.md#debug-mode)
- [Troubleshooting Examples](examples/USAGE_EXAMPLES.md#troubleshooting-examples)

## 🔧 Development Commands

Quick reference for developers:

```bash
# Setup
make install           # Install dependencies
make dev-install       # Install with dev dependencies

# Code Quality
make fmt              # Format code
make lint             # Run linting
make type-check       # Run type checking

# Development
make run              # Run the server
make test             # Run tests
make build            # Build package

# Release
make release-patch    # Create patch release
make release-minor    # Create minor release
make release-major    # Create major release
```

## 📋 Available MCP Tools

The server provides 67 tools for TestZeus operations:

| Tool Category | Count | Key Tools |
|--------------|-------|-----------|
| **Test Management** | 6 | `list_tests`, `create_test`, `update_test` |
| **Test Run Management** | 3 | `list_test_runs`, `get_test_run` |
| **Test Run Groups** | 6 | `create_test_run_group`, `download_test_run_group_report` |
| **Environment Management** | 6 | `list_environments`, `create_environment` |
| **Test Data Management** | 7 | `list_test_data`, `create_test_data` |
| **Connected Environments** 🆕 | 5 | `list_connected_environments`, `create_connected_environment` |
| **Hypermind Code Blocks** 🆕 | 8 | `list_hypermind_code_blocks`, `create_hypermind_code_block` |
| **User Integrations** 🆕 | 2 | `list_user_integrations`, `get_user_integration` |
| **Tag Management** | 5 | `list_tags`, `create_tags` |
| **Test Report Schedules** | 4 | `list_test_report_schedules`, `create_test_report_schedule` |
| **Notification Channels** | 5 | `list_notification_channels`, `create_notification_channel` |
| **Test Report Runs** | 4 | `list_test_report_runs`, `download_test_report` |

### New Features

#### Connected Environments 🆕
Link external integrations (databases, APIs, cloud services) to your tests and environments:
- Create and manage external service connections
- Link connections to multiple tests
- Centralize configuration management

#### Hypermind Code Blocks 🆕
Reusable code snippets for tests:
- Store Python and text files
- Share code across multiple tests
- Version control for test helpers

#### User Integrations 🆕
Access external service configurations (read-only):
- View GitHub, Jira, Slack integrations
- Check connection status
- Retrieve configuration details

## 🌐 Available MCP Resources

Browse TestZeus entities through 24 resource URIs:

| Resource Type | URI Pattern | Description |
|---------------|-------------|-------------|
| Tests | `test://id` | Test configurations |
| Test Runs | `test-run://id` | Test execution instances |
| Test Run Groups | `test-run-group://id` | Grouped executions |
| Environments | `environment://id` | Test environment configs |
| Test Data | `test-data://id` | Test datasets |
| **Connected Environments** 🆕 | `connected-environment://id` | External service connections |
| **Hypermind Code Blocks** 🆕 | `hypermind-code-block://id` | Reusable code snippets |
| **User Integrations** 🆕 | `user-integration://id` | External integration configs |
| Tags | `tag://id` | Organization tags |
| Test Report Schedules | `test-report-schedule://id` | Automated schedules |
| Notification Channels | `notification-channel://id` | Notification configs |
| Test Report Runs | `test-report-run://id` | Generated reports |
| All Tests | `tests://` | Browse all tests |
| All Test Runs | `test-runs://` | Browse all test runs |
| All Test Run Groups | `test-run-groups://list` | Browse all groups |
| All Environments | `environments://` | Browse all environments |
| All Test Data | `test-data://` | Browse all test data |
| **All Connected Environments** 🆕 | `connected-environments://` | Browse all connections |
| **All Code Blocks** 🆕 | `hypermind-code-blocks://` | Browse all code blocks |
| **All Integrations** 🆕 | `user-integrations://` | Browse all integrations |
| All Tags | `tags://` | Browse all tags |
| All Schedules | `test-report-schedules://list` | Browse all schedules |
| All Channels | `notification-channels://list` | Browse all channels |
| All Reports | `test-report-runs://list` | Browse all reports |

## 🎯 Common Use Cases

### Quality Assurance Teams
- **Test Management**: Create, update, and organize test suites
- **Execution Monitoring**: Track test runs and analyze results
- **Environment Management**: Configure and maintain test environments
- **Code Reusability**: Share test helpers using Hypermind Code Blocks 🆕
- **External Integrations**: Link tests to databases and APIs via Connected Environments 🆕
- **Reporting**: Generate test reports and share with teams

### Development Teams
- **CI/CD Integration**: Automated testing in pipelines
- **Pre-commit Testing**: Validate changes before deployment
- **Feature Testing**: Test new features during development
- **Regression Testing**: Ensure existing functionality works
- **Integration Testing**: Use Connected Environments for external service testing 🆕

### DevOps Teams
- **Infrastructure Testing**: Validate deployment environments
- **Performance Monitoring**: Track application performance
- **Automated Workflows**: Set up testing automation
- **Environment Provisioning**: Manage test infrastructure
- **Service Management**: Monitor and manage external integrations 🆕

## 🔗 External Resources

- **[TestZeus Platform](https://testzeus.com)** - Main TestZeus website
- **[TestZeus SDK](https://github.com/testzeus/testzeus-sdk)** - Python SDK documentation
- **[FastMCP Framework](https://github.com/patchwork-mc/fastmcp)** - MCP server framework
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - MCP specification

## 💬 Community & Support

- **[GitHub Issues](https://github.com/testzeus/testzeus-mcp-server/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/testzeus/testzeus-mcp-server/discussions)** - General questions and ideas
- **[TestZeus Discord](https://discord.gg/testzeus)** - Community support
- **[Documentation](https://docs.testzeus.com)** - Official TestZeus docs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Need help?** Check the [troubleshooting section](../README.md#troubleshooting) or create an issue on GitHub! 