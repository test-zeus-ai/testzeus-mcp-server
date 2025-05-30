# TestZeus FastMCP Server

A modern FastMCP server that exposes TestZeus SDK functionality to MCP clients like Claude Desktop and Cursor.

## Features

- **FastMCP Integration**: Built with the modern FastMCP framework for clean, efficient MCP server implementation
- **Core TestZeus Operations**: Authenticate, manage tests, test runs, and environments
- **Resource Browsing**: Browse TestZeus entities as MCP resources
- **Context Logging**: Built-in logging and error handling with FastMCP Context

## Quick Start

### For End Users

#### Option 1: Install from PyPI (Recommended)

```bash
# Install the package
pip install testzeus-mcp-server

# Or using uv (faster)
uv tool install testzeus-mcp-server
```

#### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/testzeus/testzeus-mcp-server.git
cd testzeus-mcp-server

# Install using uv
uv sync
```

### Configuration

#### Claude Desktop

1. **Edit your Claude Desktop configuration file:**

   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

2. **Add the TestZeus MCP server configuration:**

   ```json
   {
     "mcpServers": {
       "testzeus": {
         "command": "testzeus-mcp-server",
         "args": [],
         "env": {
           "TESTZEUS_EMAIL": "your-email@example.com",
           "TESTZEUS_PASSWORD": "your-password",
           "TESTZEUS_BASE_URL": "https://api.testzeus.com"
         }
       }
     }
   }
   ```

   **If installed from source:**
   ```json
   {
     "mcpServers": {
       "testzeus": {
         "command": "uv",
         "args": ["run", "testzeus-mcp-server"],
         "cwd": "/path/to/testzeus-mcp-server",
         "env": {
           "TESTZEUS_EMAIL": "your-email@example.com",
           "TESTZEUS_PASSWORD": "your-password",
           "TESTZEUS_BASE_URL": "https://api.testzeus.com"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

#### Cursor IDE

1. **Open Cursor Settings** (`Cmd/Ctrl + ,`)

2. **Navigate to Extensions → Model Context Protocol**

3. **Add a new MCP server with these settings:**

   **From PyPI:**
   ```json
   {
     "name": "TestZeus",
     "command": "testzeus-mcp-server",
     "args": [],
     "env": {
       "TESTZEUS_EMAIL": "your-email@example.com",
       "TESTZEUS_PASSWORD": "your-password",
       "TESTZEUS_BASE_URL": "https://api.testzeus.com"
     }
   }
   ```

   **From Source:**
   ```json
   {
     "name": "TestZeus",
     "command": "uv",
     "args": ["run", "testzeus-mcp-server"],
     "cwd": "/path/to/testzeus-mcp-server",
     "env": {
       "TESTZEUS_EMAIL": "your-email@example.com",
       "TESTZEUS_PASSWORD": "your-password",
       "TESTZEUS_BASE_URL": "https://api.testzeus.com"
     }
   }
   ```

4. **Save and restart Cursor**

## Usage

### Authentication

The server will automatically authenticate using the environment variables you provided. You can also manually authenticate:

```
User: "Authenticate with TestZeus"
Assistant: I'll authenticate you with TestZeus using your credentials.
```

### Basic Operations

#### Viewing Tests
```
User: "What tests do I have?"
Assistant: [Lists all available tests with descriptions]

User: "Show me details of my login test"
Assistant: [Displays comprehensive test information]
```

#### Creating Tests
```
User: "Create a test for user registration flow"
Assistant: [Creates a new test with appropriate parameters]

User: "Tag it with 'authentication' and 'critical'"
Assistant: [Applies tags to the test]
```

#### Running Tests
```
User: "Run all tests tagged with 'smoke'"
Assistant: [Discovers and runs smoke tests]

User: "Check the status of recent test runs"
Assistant: [Shows test run statuses and results]
```

### Available Tools

- **Test Management**: `list_tests`, `get_test`, `create_test`, `update_test`, `delete_test`, `run_test`
- **Test Run Management**: `list_test_runs`, `get_test_run`, `create_test_run`
- **Environment Management**: `list_environments`, `get_environment`, `create_environment`

### Available Resources

- `tests://` - Browse all tests
- `test://{test_id}` - View specific test details
- `test-runs://` - Browse all test runs
- `test-run://{test_run_id}` - View specific test run details
- `environments://` - Browse all environments
- `environment://{environment_id}` - View specific environment details

## Development

### For Developers

#### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/testzeus/testzeus-mcp-server.git
cd testzeus-mcp-server

# Install development dependencies
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

#### Development Commands

```bash
# Install dependencies
make install

# Run linting
make lint

# Run type checking
make type-check

# Run tests (when available)
make test

# Run the server locally
make run

# Clean build artifacts
make clean

# Build package
make build
```

#### Running from Source

```bash
# Run directly
uv run testzeus-mcp-server

# Or with make
make run

# With custom environment
TESTZEUS_EMAIL=test@example.com uv run testzeus-mcp-server
```

#### Testing Your Changes

1. **Configure your MCP client to use the local version**
2. **Make your changes**
3. **Test with your MCP client**
4. **Run linting and type checking**

#### Project Structure

```
testzeus-mcp-server/
├── testzeus_mcp_server/
│   ├── __init__.py
│   ├── __main__.py        # Entry point
│   └── server.py          # Main MCP server implementation
├── .github/
│   └── workflows/         # CI/CD workflows
├── docs/                  # Documentation
├── examples/              # Usage examples
├── tests/                 # Test files (when added)
├── pyproject.toml         # Project configuration
├── uv.lock               # Dependency lock file
├── Makefile              # Development commands
└── README.md
```

#### Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests if applicable**
5. **Run linting and type checking**
6. **Submit a pull request**

### Release Process

```bash
# Create a patch release (2.0.0 -> 2.0.1)
make release-patch

# Create a minor release (2.0.0 -> 2.1.0)
make release-minor

# Create a major release (2.0.0 -> 3.0.0)
make release-major

# Create a custom release
make release-custom
```

## Architecture

This server is built with FastMCP, providing:

- **Decorative Tools**: Simple `@mcp.tool()` decorators for clean function definitions
- **Resource Templates**: Dynamic resource URIs with `@mcp.resource()` decorators
- **Context Integration**: Built-in logging and error handling via FastMCP Context
- **Modern Python**: Type hints, async/await, and clean code structure

The implementation focuses purely on TestZeus business logic without MCP protocol boilerplate.

## Resource URI Schemes

| Resource Type | URI Format | Description |
|---------------|------------|-------------|
| Tests | `test://id` | Test configurations and metadata |
| Test Runs | `test-run://id` | Test execution instances |
| Environments | `environment://id` | Test environment configurations |
| Tags | `tag://id` | Test organization tags |
| Test Data | `test-data://id` | Test datasets and fixtures |
| Users | `user://id` | TestZeus user accounts |
| Agent Configs | `agent-config://id` | AI agent configurations |
| Test Designs | `test-design://id` | Test templates and patterns |

## Troubleshooting

### Common Issues

#### Authentication Failed
- Verify your email and password in the configuration
- Check if TESTZEUS_BASE_URL is correct
- Ensure your TestZeus account is active

#### MCP Server Not Found
```bash
# Check if the package is installed
pip list | grep testzeus-mcp-server

# Reinstall if needed
pip install --upgrade testzeus-mcp-server
```

#### Permission Denied
```bash
# On macOS/Linux, you might need to make the script executable
chmod +x $(which testzeus-mcp-server)
```

#### Environment Variables Not Set
Make sure environment variables are properly set in your MCP client configuration.

### Debug Mode

```bash
# Run with debug logging
TESTZEUS_DEBUG=true uv run testzeus-mcp-server

# Or set in your MCP client configuration
"env": {
  "TESTZEUS_DEBUG": "true",
  "TESTZEUS_EMAIL": "your-email@example.com",
  "TESTZEUS_PASSWORD": "your-password"
}
```

## Error Handling

The server provides detailed error messages for common issues:
- Authentication failures
- Missing required parameters
- TestZeus API errors
- Network connectivity issues

## Dependencies

- **testzeus-sdk**: Official TestZeus Python SDK
- **fastmcp**: Modern MCP server framework
- **aiohttp**: Async HTTP client
- **pydantic**: Data validation

## License

MIT License - see LICENSE file for details.

## Support

- 📖 Documentation: [TestZeus Docs](https://docs.testzeus.com)
- 💬 Community: [TestZeus Discord](https://discord.gg/testzeus)
- 🐛 Issues: [GitHub Issues](https://github.com/testzeus/testzeus-mcp-server/issues)
- 📧 Contact: support@testzeus.com

## Why MCP Resources?

Traditional tool-only approaches require users to know exactly what tools to call. With MCP resources:

- **Discoverable**: Browse available tests like files in a directory
- **Contextual**: See test details before deciding what to do
- **Natural**: "Show me my tests" instead of "call list_tests tool"
- **Rich**: Complete entity information, not just IDs
- **Real-time**: Always current with your TestZeus account

This makes TestZeus truly conversational and intuitive to use with AI assistants. 