# TestZeus FastMCP Server

A modern FastMCP server that exposes TestZeus SDK functionality to MCP clients like Claude Desktop.

## Features

- **FastMCP Integration**: Built with the modern FastMCP framework for clean, efficient MCP server implementation
- **Core TestZeus Operations**: Authenticate, manage tests, test runs, and environments
- **Resource Browsing**: Browse TestZeus entities as MCP resources
- **Context Logging**: Built-in logging and error handling with FastMCP Context

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the server
uv run testzeus-mcp-server
```

## Usage

### Authentication

First, authenticate with your TestZeus account:

```python
# Use the authenticate_testzeus tool
{
  "email": "your-email@example.com",
  "password": "your-password",
  "base_url": "https://api.testzeus.com"  # optional
}
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

```bash
# Install development dependencies
uv sync --dev

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
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

## Example Workflows

### Natural Test Discovery
```
User: "What tests do I have?"
Claude: [Lists all test resources with descriptions]

User: "Show me details of my login test"
Claude: [Reads and displays test://login-test-id content]
```

### Intelligent Test Creation
```
User: "Create a test for user registration flow"
Claude: [Uses create_test tool with appropriate parameters]

User: "Tag it with 'authentication' and 'critical'"
Claude: [Applies tags during creation or updates existing test]
```

### Test Execution Management
```
User: "Run all tests tagged with 'smoke'"
Claude: [Discovers tests with smoke tag, runs each one]

User: "Check the status of recent test runs"
Claude: [Lists test-run resources with status information]
```

## Error Handling

The server provides detailed error messages for common issues:
- Authentication failures
- Missing required parameters
- TestZeus API errors
- Network connectivity issues

## Development

### Project Structure
```
testzeus-mcp-server/
├── testzeus_mcp_server/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
├── examples/
│   └── usage_examples.md  # Detailed usage examples
├── docs/
│   └── ARCHITECTURE.md    # Technical architecture
├── requirements.txt       # Python dependencies
└── README.md
```

### Dependencies

- **testzeus-sdk**: Official TestZeus Python SDK
- **mcp**: Model Context Protocol implementation
- **aiohttp**: Async HTTP client
- **pydantic**: Data validation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

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