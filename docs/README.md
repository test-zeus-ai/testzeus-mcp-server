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

The server provides these tools for TestZeus operations:

| Tool | Description | Usage |
|------|-------------|-------|
| `authenticate_testzeus` | Authenticate with TestZeus | Initial setup |
| `list_tests` | List all tests | Browse available tests |
| `get_test` | Get test details | View specific test |
| `create_test` | Create new test | Add test to suite |
| `update_test` | Update existing test | Modify test configuration |
| `delete_test` | Delete test | Remove test from suite |
| `run_test` | Execute test | Run individual test |
| `list_test_runs` | List test executions | Browse test history |
| `get_test_run` | Get run details | View execution results |
| `create_test_run` | Start test execution | Run tests manually |
| `list_environments` | List test environments | Browse environments |
| `get_environment` | Get environment details | View environment config |
| `create_environment` | Create new environment | Add test environment |

## 🌐 Available MCP Resources

Browse TestZeus entities through these resource URIs:

| Resource Type | URI Pattern | Description |
|---------------|-------------|-------------|
| Tests | `test://id` | Test configurations |
| Test Runs | `test-run://id` | Test execution instances |
| Environments | `environment://id` | Test environment configs |
| All Tests | `tests://` | Browse all tests |
| All Test Runs | `test-runs://` | Browse all test runs |
| All Environments | `environments://` | Browse all environments |

## 🎯 Common Use Cases

### Quality Assurance Teams
- **Test Management**: Create, update, and organize test suites
- **Execution Monitoring**: Track test runs and analyze results
- **Environment Management**: Configure and maintain test environments
- **Reporting**: Generate test reports and share with teams

### Development Teams
- **CI/CD Integration**: Automated testing in pipelines
- **Pre-commit Testing**: Validate changes before deployment
- **Feature Testing**: Test new features during development
- **Regression Testing**: Ensure existing functionality works

### DevOps Teams
- **Infrastructure Testing**: Validate deployment environments
- **Performance Monitoring**: Track application performance
- **Automated Workflows**: Set up testing automation
- **Environment Provisioning**: Manage test infrastructure

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