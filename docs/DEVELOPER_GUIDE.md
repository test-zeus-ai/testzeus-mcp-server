# TestZeus MCP Server - Developer Guide

This guide provides detailed instructions for developers who want to contribute to or extend the TestZeus MCP Server.

## Prerequisites

- **Python 3.11+**
- **Git**
- **uv** (recommended) or pip
- **A TestZeus account** for testing

### Installing uv (Recommended)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

## Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/testzeus/testzeus-mcp-server.git
cd testzeus-mcp-server

# Install dependencies
uv sync --dev

# Verify installation
uv run testzeus-mcp-server --help
```

### 2. Environment Configuration

Create a `.env` file for development:

```bash
# .env
TESTZEUS_EMAIL=your-dev-email@example.com
TESTZEUS_PASSWORD=your-dev-password
TESTZEUS_BASE_URL=https://api.testzeus.com
TESTZEUS_DEBUG=true
```

Load environment variables:

```bash
# Load .env file
set -a && source .env && set +a
```

## Development Workflow

### Code Quality

```bash
# Format code
make fmt

# Run linting
make lint

# Run type checking
make type-check

# Run all checks
make lint
```

### Testing

```bash
# Run tests (when available)
make test

# Run with coverage
uv run pytest --cov=testzeus_mcp_server
```

### Running the Server

```bash
# Run from source
make run

# Or directly
uv run testzeus-mcp-server

# With debug logging
TESTZEUS_DEBUG=true uv run testzeus-mcp-server

# Test specific functionality
uv run python -c "from testzeus_mcp_server.server import app; print('Server loaded successfully')"
```

## Project Structure

```
testzeus-mcp-server/
├── testzeus_mcp_server/          # Main package
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # CLI entry point
│   └── server.py                # MCP server implementation
├── .github/                     # GitHub workflows
│   └── workflows/
│       ├── ci.yml              # Continuous integration
│       └── publish.yml         # PyPI publishing
├── docs/                        # Documentation
│   ├── DEVELOPER_GUIDE.md      # This file
│   └── examples/               # Usage examples
├── tests/                       # Test files (when added)
├── pyproject.toml              # Project configuration
├── uv.lock                     # Dependency lock file
├── Makefile                    # Development commands
├── README.md                   # User documentation
└── LICENSE                     # MIT license
```

## Architecture Overview

### FastMCP Framework

The server is built using FastMCP, which provides:

- **Decorative Tools**: Use `@mcp.tool()` for clean function definitions
- **Resource Templates**: Dynamic resources with `@mcp.resource()`
- **Context Integration**: Built-in logging and error handling
- **Type Safety**: Full type hints and validation

### Core Components

#### 1. Server Module (`server.py`)

- **MCP App Instance**: Main FastMCP application
- **Tool Definitions**: TestZeus operation implementations
- **Resource Handlers**: Dynamic resource browsing
- **Authentication**: TestZeus SDK integration

#### 2. Entry Point (`__main__.py`)

- **CLI Interface**: Command-line argument parsing
- **Server Startup**: FastMCP server initialization
- **Environment Configuration**: Environment variable handling

#### 3. Package Initialization (`__init__.py`)

- **Version Information**: Package metadata
- **Public API**: Exposed functions and classes

### TestZeus SDK Integration

```python
from testzeus_sdk import TestZeusSDK

# Initialize SDK with authentication
sdk = TestZeusSDK(
    email=os.getenv("TESTZEUS_EMAIL"),
    password=os.getenv("TESTZEUS_PASSWORD"),
    base_url=os.getenv("TESTZEUS_BASE_URL", "https://api.testzeus.com")
)

# Use SDK in MCP tools
@mcp.tool()
async def list_tests() -> List[Dict[str, Any]]:
    return await sdk.list_tests()
```

## Adding New Features

### 1. Adding New Tools

Tools are functions decorated with `@mcp.tool()`:

```python
@mcp.tool()
async def new_operation(
    parameter: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """
    Description of what this tool does.
    
    Args:
        parameter: Description of required parameter
        optional_param: Description of optional parameter
    
    Returns:
        Dictionary containing operation results
    """
    try:
        # Implementation using TestZeus SDK
        result = await sdk.some_operation(parameter, optional_param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Adding New Resources

Resources provide browsable content:

```python
@mcp.resource("resource-type://{resource_id}")
async def get_resource(resource_id: str) -> str:
    """
    Fetch and return resource content.
    """
    try:
        data = await sdk.get_resource(resource_id)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.resource("resource-type://")
async def list_resources() -> str:
    """
    List all available resources of this type.
    """
    try:
        resources = await sdk.list_resources()
        return "\n".join(f"resource-type://{r['id']} - {r['name']}" for r in resources)
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. Error Handling

Use consistent error handling patterns:

```python
from typing import Union, Dict, Any

async def safe_operation() -> Union[Dict[str, Any], Dict[str, str]]:
    try:
        result = await sdk.operation()
        return {"success": True, "data": result}
    except AuthenticationError:
        return {"success": False, "error": "Authentication failed. Please check credentials."}
    except ValidationError as e:
        return {"success": False, "error": f"Invalid parameters: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

## Testing Your Changes

### 1. Unit Testing

When adding tests, follow this structure:

```python
# tests/test_server.py
import pytest
from testzeus_mcp_server.server import app

@pytest.mark.asyncio
async def test_tool_functionality():
    # Test implementation
    pass
```

### 2. Integration Testing

Test with actual MCP clients:

#### Claude Desktop Testing

1. Update your `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "testzeus-dev": {
         "command": "uv",
         "args": ["run", "testzeus-mcp-server"],
         "cwd": "/path/to/your/dev/testzeus-mcp-server",
         "env": {
           "TESTZEUS_EMAIL": "your-dev-email@example.com",
           "TESTZEUS_PASSWORD": "your-dev-password",
           "TESTZEUS_DEBUG": "true"
         }
       }
     }
   }
   ```

2. Restart Claude Desktop
3. Test your changes in conversation

#### Cursor Testing

1. Configure MCP server in Cursor settings
2. Test functionality in Cursor chat

### 3. Manual Testing

```bash
# Test server startup
uv run testzeus-mcp-server

# Test with different environments
TESTZEUS_DEBUG=true uv run testzeus-mcp-server

# Test CLI help
uv run testzeus-mcp-server --help
```

## Debugging

### Debug Logging

Enable detailed logging:

```python
import logging

# In your development environment
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export TESTZEUS_DEBUG=true
```

### Common Issues

#### Import Errors

```bash
# Check package installation
uv run python -c "import testzeus_mcp_server; print('OK')"

# Reinstall in development mode
uv sync --dev
```

#### Authentication Issues

```bash
# Test SDK authentication separately
uv run python -c "
from testzeus_sdk import TestZeusSDK
import os
sdk = TestZeusSDK(
    email=os.getenv('TESTZEUS_EMAIL'),
    password=os.getenv('TESTZEUS_PASSWORD')
)
print('Auth successful')
"
```

#### MCP Protocol Issues

Check FastMCP documentation for protocol-specific debugging.

## Code Style and Standards

### Formatting

- Use **Ruff** for formatting and linting
- Line length: 100 characters (configured in `pyproject.toml`)
- Use type hints for all functions

### Documentation

- Document all public functions and classes
- Use Google-style docstrings
- Include examples in docstrings when helpful

### Git Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes with good commit messages**
3. **Run quality checks**: `make lint`
4. **Create pull request**

### Commit Messages

Follow conventional commits:

```
feat: add new test management tool
fix: resolve authentication timeout issue
docs: update installation instructions
refactor: improve error handling patterns
test: add unit tests for resource handlers
```

## Release Process

### Version Management

Versions are managed in `pyproject.toml`:

```toml
[project]
version = "2.0.0"
```

### Creating Releases

```bash
# Patch release (2.0.0 -> 2.0.1)
make release-patch

# Minor release (2.0.0 -> 2.1.0)
make release-minor

# Major release (2.0.0 -> 3.0.0)
make release-major

# Custom version
make release-custom
```

### CI/CD Pipeline

GitHub Actions automatically:

1. **Run tests and linting** on every PR
2. **Build and publish** to PyPI on tag creation
3. **Test multiple Python versions** (3.11, 3.12)

## Contributing Guidelines

### Before Contributing

1. **Check existing issues** for similar requests
2. **Create an issue** to discuss major changes
3. **Fork the repository**

### Pull Request Process

1. **Create feature branch** from `main`
2. **Make your changes** with tests
3. **Update documentation** if needed
4. **Run all quality checks**
5. **Submit pull request** with clear description

### Code Review

- All changes require review
- Address feedback promptly
- Ensure CI passes
- Keep changes focused and atomic

## Getting Help

### Documentation

- **README.md**: User documentation
- **This guide**: Developer information
- **FastMCP docs**: Framework documentation
- **TestZeus SDK docs**: API reference

### Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Discord**: Real-time community support

### Support

- Create detailed issues with reproduction steps
- Include environment information
- Provide error logs when applicable

## Advanced Topics

### Custom Resource Types

Implement custom resource patterns:

```python
@mcp.resource("custom://complex/{type}/{id}")
async def complex_resource(type: str, id: str) -> str:
    # Implementation for complex resource patterns
    pass
```

### Performance Optimization

- Use async/await properly
- Cache frequently accessed data
- Implement efficient error handling
- Monitor resource usage

### Security Considerations

- Never log sensitive information
- Validate all inputs
- Use secure authentication methods
- Follow TestZeus security guidelines

This developer guide provides the foundation for contributing to the TestZeus MCP Server. For specific questions or advanced use cases, please refer to the community resources or create an issue on GitHub. 