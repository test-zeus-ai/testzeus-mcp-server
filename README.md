# TestZeus FastMCP Server

A modern FastMCP server that exposes TestZeus SDK functionality to MCP clients like Claude Desktop and Cursor.

## Features

- **FastMCP Integration**: Built with the modern FastMCP framework for clean, efficient MCP server implementation
- **Comprehensive TestZeus Operations**: Complete test lifecycle management including tests, test runs, test run groups, environments, test data, and tags
- **Connected Environments**: Link external integrations (databases, APIs, cloud services) to tests and environments
- **Hypermind Code Blocks**: Reusable code snippets for tests with Python and text file support
- **Advanced Scheduling**: Test report scheduling with cron expressions and time-based filtering
- **Multi-Channel Notifications**: Email and webhook notification support for test results
- **Report Management**: Generate, download, and manage test reports in multiple formats (CTRF, PDF, CSV, ZIP)
- **Resource Browsing**: Browse all TestZeus entities as MCP resources for easy discovery
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
         "command": "uv",
         "args": ["run", "testzeus-mcp-server"],
         "env": {
           "PATH": "/path/to/testzeus-mcp-server",
           "TESTZEUS_EMAIL": "your-email@example.com",
           "TESTZEUS_PASSWORD": "your-password"
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

   ```json
   {
     "name": "TestZeus",
     "command": "uv",
     "args": ["run", "testzeus-mcp-server"],
     "env": {
       "PATH": "/path/to/testzeus-mcp-server",
       "TESTZEUS_EMAIL": "your-email@example.com",
       "TESTZEUS_PASSWORD": "your-password"
     }
   }
   ```

4. **Save and restart Cursor**

## Usage

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

User: "Set test_params for username and password defaults"
Assistant: [Stores those defaults in the test_params field]
```

#### Running Tests
```
User: "Run all tests tagged with 'smoke'"
Assistant: [Discovers and runs smoke tests]

User: "Check the status of recent test runs"
Assistant: [Shows test run statuses and results]
```

#### Managing Test Suites
```text
User: "Create a test suite for checkout regression using this workflow definition"
Assistant: [Creates the test suite with default_inputs, input_schema, and lenient execution mode]

User: "Show me all test suites that depend on test abc123"
Assistant: [Queries dependent test suites using the test_suites relation]

User: "Update the suite's default inputs for region and tenant"
Assistant: [Updates the test suite defaults]
```

#### Managing Test Suite Runs
```text
User: "Run my checkout regression suite in staging"
Assistant: [Creates a lenient test suite run with a workflow snapshot from the suite]

User: "Pause the active suite run gracefully"
Assistant: [Pauses the run]

User: "List the node runs for the latest suite run"
Assistant: [Shows node-level execution status]
```

#### Managing Test Run Groups
```
User: "Create a test run group for regression testing"
Assistant: [Creates a new test run group with multiple tests]

User: "Execute my smoke test group"
Assistant: [Runs all tests in the specified group]

User: "Download the report for my last test run group"
Assistant: [Downloads the group's test report in specified format]
```

#### Scheduling Test Reports
```
User: "Create a weekly test report schedule"
Assistant: [Sets up automated test report generation]

User: "Schedule daily reports for tests tagged 'critical'"
Assistant: [Creates a schedule with tag-based filtering]

User: "List all my active schedules"
Assistant: [Shows all configured test report schedules]
```

#### Managing Notifications
```
User: "Create a notification channel for the dev team"
Assistant: [Sets up email notifications for test results]

User: "Add webhook notifications to my channel"
Assistant: [Configures webhook integration for real-time alerts]

User: "Show me all notification channels"
Assistant: [Lists all configured notification channels]
```

#### Downloading Test Reports
```
User: "Download the latest test report as PDF"
Assistant: [Downloads the most recent test report in PDF format]

User: "Get the CTRF report for test run group XYZ"
Assistant: [Downloads the Common Test Report Format file]

User: "Show me all available test reports"
Assistant: [Lists all generated test reports with their formats]
```

#### Managing Test Data
```
User: "Show me all test data"
Assistant: [Lists all available test data with details]

User: "Create test data for user signup scenarios"
Assistant: [Creates new test data with appropriate content]

User: "Add a CSV file to my test data"
Assistant: [Adds supporting file to test data]

User: "Remove all files from test data ID 123"
Assistant: [Removes all supporting files from the test data]
```

#### Managing Environment Files
```
User: "Add a configuration file to my staging environment"
Assistant: [Adds the specified file to the environment]

User: "Remove the old config.json from environment"
Assistant: [Removes the specific file from environment]

User: "Clean up all files from my test environment"
Assistant: [Removes all supporting files from the environment]
```

#### Managing Tags
```
User: "List all my tags"
Assistant: [Shows all available tags and their values]

User: "Create a tag for priority with value 'high'"
Assistant: [Creates a new tag for test organization]
```

#### Managing Connected Environments
```text
User: "List all connected environments"
Assistant: [Shows all external service connections]

User: "Create a connected environment for our PostgreSQL database"
Assistant: [Creates a connected environment linking to database integration]

User: "Link the database connection to my API tests"
Assistant: [Updates test to use the connected environment]
```

#### Managing Hypermind Code Blocks
```text
User: "Create a code block for authentication helpers"
Assistant: [Creates a reusable code block]

User: "Add my auth.py file to the code block"
Assistant: [Adds Python file to the code block]

User: "List all my code blocks"
Assistant: [Shows all available hypermind code blocks]
```

#### Viewing User Integrations
```text
User: "Show me all my integrations"
Assistant: [Lists all external service connections]

User: "Get details about my GitHub integration"
Assistant: [Shows GitHub integration configuration and status]
```

### Available Tools (82 Tools)

- **Test Management** (8 tools): `list_tests`, `get_test`, `create_test`, `update_test`, `get_test_input_params`, `get_dependent_test_suites`, `delete_test`, `run_tests`
- **Test Run Management** (3 tools): `list_test_runs`, `get_test_run`, `delete_test_run`
- **Test Run Group Management** (7 tools): `list_test_run_groups`, `get_test_run_group`, `create_test_run_group`, `delete_test_run_group`, `cancel_test_run_group`, `download_test_run_group_report`, `download_test_run_group_attachments`
- **Test Suite Management** (5 tools): `list_test_suites`, `get_test_suite`, `create_test_suite`, `update_test_suite`, `delete_test_suite`
- **Test Suite Run Management** (6 tools): `list_test_suite_runs`, `get_test_suite_run`, `create_test_suite_run`, `pause_test_suite_run`, `resume_test_suite_run`, `cancel_test_suite_run`
- **Test Suite Execution Detail** (2 tools): `list_test_suite_node_runs`, `list_test_suite_schedules`
- **Environment Management** (8 tools): `list_environments`, `get_environment`, `create_environment`, `update_environment`, `delete_environment`, `add_environment_file`, `remove_environment_file`, `remove_all_environment_files`
- **Test Data Management** (8 tools): `list_test_data`, `get_test_data`, `create_test_data`, `update_test_data`, `delete_test_data`, `add_test_data_file`, `remove_test_data_file`, `remove_all_test_data_files`
- **Connected Environment Management** (5 tools): `list_connected_environments`, `get_connected_environment`, `create_connected_environment`, `update_connected_environment`, `delete_connected_environment`
- **Hypermind Code Blocks** (8 tools): `list_hypermind_code_blocks`, `get_hypermind_code_block`, `create_hypermind_code_block`, `update_hypermind_code_block`, `delete_hypermind_code_block`, `add_hypermind_code_block_file`, `remove_hypermind_code_block_file`, `remove_all_hypermind_code_block_files`
- **User Integration** (2 tools): `list_user_integrations`, `get_user_integration`
- **Tag Management** (5 tools): `list_tags`, `get_tag`, `create_tags`, `update_tag`, `delete_tag`
- **Test Report Schedule Management** (5 tools): `list_test_report_schedules`, `get_test_report_schedule`, `create_test_report_schedule`, `update_test_report_schedule`, `delete_test_report_schedule`
- **Notification Channel Management** (6 tools): `list_notification_channels`, `get_notification_channel`, `create_notification_channel`, `update_notification_channel`, `delete_notification_channel`, `remove_notification_config`
- **Test Report Run Management** (4 tools): `list_test_report_runs`, `get_test_report_run`, `delete_test_report_run`, `download_test_report`

### Available Resources (24 Resources)

- `tests://` - Browse all tests
- `test://{test_id}` - View specific test details
- `test-runs://` - Browse all test runs
- `test-run://{test_run_id}` - View specific test run details
- `test-run-groups://list` - Browse all test run groups
- `test-run-group://{test_run_group_id}` - View specific test run group details
- `environments://` - Browse all environments
- `environment://{environment_id}` - View specific environment details
- `test-data://` - Browse all test data
- `test-data://{test_data_id}` - View specific test data details
- `connected-environments://` - Browse all connected environments
- `connected-environment://{connected_env_id}` - View specific connected environment
- `hypermind-code-blocks://` - Browse all hypermind code blocks
- `hypermind-code-block://{code_block_id}` - View specific code block
- `user-integrations://` - Browse all user integrations
- `user-integration://{integration_id}` - View specific integration
- `tags://` - Browse all tags
- `tag://{tag_id}` - View specific tag details
- `test-report-schedules://list` - Browse all test report schedules
- `test-report-schedule://{schedule_id}` - View specific test report schedule details
- `notification-channels://list` - Browse all notification channels
- `notification-channel://{channel_id}` - View specific notification channel details
- `test-report-runs://list` - Browse all test report runs
- `test-report-run://{report_id}` - View specific test report run details

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

# To get mcp server location
uv run mcp dev testzeus_mcp_server/server.py

# With custom environment
TESTZEUS_EMAIL=test@example.com uv run testzeus-mcp-server
```

then copy the servers File and paste it into llm (claude, codex) config file.

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
| Test Data | `test-data://id` | Test datasets and fixtures |
| Connected Environments | `connected-environment://id` | External service connections |
| Hypermind Code Blocks | `hypermind-code-block://id` | Reusable code snippets |
| User Integrations | `user-integration://id` | External integration configs |
| Tags | `tag://id` | Test organization tags |
| Test Run Groups | `test-run-group://id` | Grouped test execution instances |
| Test Report Schedules | `test-report-schedule://id` | Automated test report schedules |
| Notification Channels | `notification-channel://id` | Notification configurations |
| Test Report Runs | `test-report-run://id` | Generated test reports |

## Troubleshooting

### Common Issues

#### Authentication Failed
- Verify your email and password in the configuration
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

Find Path by running mcp inspector, copy the Servers File and paste it in llm (claude, codex, cursor, ...) config.json file.

```uv run mcp dev testzeus_mcp_server/server.py```


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
- **httpx**: HTTP client for file downloads

## License

MIT License - see LICENSE file for details.

## Why MCP Resources?

Traditional tool-only approaches require users to know exactly what tools to call. With MCP resources:

- **Discoverable**: Browse available tests, schedules, reports, and configurations like files in a directory
- **Contextual**: See complete entity details before deciding what actions to take
- **Natural**: "Show me my test reports" instead of "call list_test_report_runs tool"
- **Rich**: Complete entity information including relationships, status, and metadata
- **Real-time**: Always current with your TestZeus account
- **Comprehensive**: Access to the full TestZeus ecosystem including advanced features like scheduling and notifications

This makes TestZeus truly conversational and intuitive to use with AI assistants, enabling complex test management workflows through natural language. 


### Troubleshoots

1. install lib if not working : uv add python-dateutil
2. for dev add sdk file : "testzeus-sdk @ file:///path_to_dir/testzeus-sdk", and add to pyproject 
```bash
[tool.hatch.metadata]
allow-direct-references = true
```
then run 
```bash
rm -rf .venv
uv sync
```
then check `uv run python -c "import testzeus_sdk; print(testzeus_sdk.__file__)"`

3. If you only want local dev linking (editable mode), bypass pyproject dependency altogether
`uv pip install -e /path/to/testzeus-sdk`
