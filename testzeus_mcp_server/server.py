"""
TestZeus FastMCP Server - Modern MCP server implementation for TestZeus SDK.

This module provides a FastMCP-based server that exposes TestZeus SDK
functionality to MCP clients like Claude Desktop in a clean, modern way.

Key Features:
- Test Management: Create, update, delete, and execute tests
- Environment Management: Manage test environments and connected environments
- Test Data Management: Handle test data and supporting files
- Hypermind Code Blocks: Manage reusable code blocks for tests
- User Integrations: Access user integration configurations
- Test Run Groups: Execute and monitor test runs
- Test Report Schedules: Schedule and manage test reports
- Notification Channels: Configure notification channels for test results
- Tags: Organize tests with tags

Execution mode is configurable ('lenient' or 'strict') in create_test, update_test,
create_test_suite, and update_test_suite. Test suite runs and test run groups
still use hardcoded 'lenient' mode for consistent behavior.
Connected environments can be linked to both tests and environments for enhanced integration.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from testzeus_sdk.client import TestZeusClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Create the FastMCP server
mcp = FastMCP("TestZeus MCP Server")

# Global client instance
testzeus_client: TestZeusClient | None = None


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def ensure_authenticated() -> bool:
    """Ensure the TestZeus client is authenticated."""
    global testzeus_client
    if not testzeus_client:
        return False
    try:
        await testzeus_client.ensure_authenticated()
        return True
    except Exception:
        return False


async def authenticate_testzeus(
    email: str | None = None,
    password: str | None = None,
    ctx: Context = None,
) -> str:
    """Authenticate with TestZeus platform using email and password."""
    global testzeus_client

    # Fallback to environment variables if arguments aren’t passed
    email = email or os.getenv("TESTZEUS_EMAIL")
    password = password or os.getenv("TESTZEUS_PASSWORD")

    if not email or not password:
        error_msg = "Missing credentials: email and password are required"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        testzeus_client = TestZeusClient(
            email=email, password=password, base_url=os.getenv("TESTZEUS_BASE_URL")
        )
        await testzeus_client.ensure_authenticated()

        if ctx:
            await ctx.info("Successfully authenticated with TestZeus")

        return f"Successfully authenticated with TestZeus as {email}"
    except Exception as e:
        error_msg = f"Authentication failed: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Test Management Tools
@mcp.tool()
async def list_tests(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all tests in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.tests.get_list(**params)
        tests = result.get("items", [])

        test_list = []
        for test in tests:
            test_list.append(
                {
                    "id": test.id,
                    "name": test.name,
                    "status": test.status,
                    "testing_type": test.testing_type,
                    "test_feature": test.test_feature,
                    "tags": test.tags,
                    "environment": test.environment,
                    "created": str(test.created),
                    "updated": str(test.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(test_list)} tests")

        return f"Found {len(test_list)} tests:\n{json.dumps(test_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing tests: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test(test_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.tests.get_one(test_id_or_name)
        test_data = {
            "id": test.id,
            "name": test.name,
            "status": test.status,
            "testing_type": test.testing_type,
            "test_feature": test.test_feature,
            "tags": test.tags,
            "test_data": test.test_data,
            "environment": test.environment,
            "config": getattr(test, "config", None),
            "metadata": getattr(test, "metadata", None),
            "created": str(test.created),
            "updated": str(test.updated),
            "tenant": test.tenant,
            "modified_by": test.modified_by,
        }

        if ctx:
            await ctx.info(f"Retrieved test: {test.name}")

        return f"Test details:\n{json.dumps(test_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test(
    name: str,
    test_feature: str,
    testing_type: Literal["web", "mobile"] = "web",
    status: str = "draft",
    test_data: list[str] | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    test_params: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    execution_mode: Literal["lenient", "strict"] = "lenient",
    ctx: Context = None,
) -> str:
    """Create a new test in TestZeus.

    testing_type defaults to 'web'. When set to 'mobile', an environment reference is required.
    """
    if testing_type == "mobile" and not environment:
        return "Error: environment is required when testing_type is 'mobile'"

    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.tests.create_test(
            name=name,
            test_feature=test_feature,
            testing_type=testing_type,
            status=status,
            test_params=test_params,
            test_data=test_data,
            tags=tags,
            environment=environment,
            output_schema=output_schema,
            execution_mode=execution_mode,
        )

        if ctx:
            await ctx.info(f"Created test: {name}")

        return f"Successfully created test '{name}' with ID: {test.id}"
    except Exception as e:
        error_msg = f"Error creating test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test(
    test_id_or_name: str,
    name: str | None = None,
    test_feature: str | None = None,
    testing_type: Literal["web", "mobile"] | None = None,
    status: str | None = None,
    test_data: list[str] | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    test_params: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    execution_mode: Literal["lenient", "strict"] | None = None,
    ctx: Context = None,
) -> str:
    """Update an existing test in TestZeus.

    When testing_type is set to 'mobile', an environment reference is required.
    """
    if testing_type == "mobile" and not environment:
        return "Error: environment is required when testing_type is 'mobile'"

    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name is not None:
            data["name"] = name
        if test_feature is not None:
            data["test_feature"] = test_feature
        if testing_type:
            data["testing_type"] = testing_type
        if status is not None:
            data["status"] = status
        if test_data is not None:
            data["test_data"] = test_data
        if tags is not None:
            data["tags"] = tags
        if environment is not None:
            data["environment"] = environment
        if test_params is not None:
            data["test_params"] = test_params
        if output_schema is not None:
            data["output_schema"] = output_schema
        if execution_mode is not None:
            data["execution_mode"] = execution_mode

        test = await testzeus_client.tests.update_test(test_id_or_name, **data)

        if ctx:
            await ctx.info(f"Updated test: {test.name}")

        return f"Successfully updated test '{test.name}' (ID: {test.id})"
    except Exception as e:
        error_msg = f"Error updating test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_input_params(test_id: str, ctx: Context = None) -> str:
    """Get merged input params and defaults for a test."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        result = await testzeus_client.tests.get_input_params(test_id)

        if ctx:
            await ctx.info(f"Retrieved input params for test: {test_id}")

        return f"Test input params:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test input params: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_dependent_test_suites(test_id: str, ctx: Context = None) -> str:
    """Get test suites that reference a test."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        result = await testzeus_client.test_suites.get_list(
            filters={"tests": {"operator": "?=", "value": [test_id]}},
            page=1,
            per_page=50,
        )
        suite_list = [
            {
                "id": suite.id,
                "name": suite.name,
                "display_name": getattr(suite, "display_name", None),
                "status": suite.status,
                "execution_mode": getattr(suite, "execution_mode", None),
            }
            for suite in result.get("items", [])
        ]

        if ctx:
            await ctx.info(f"Retrieved dependent suites for test: {test_id}")

        return f"Dependent test suites:\n{json.dumps(suite_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting dependent test suites: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test(test_id_or_name: str, ctx: Context = None) -> str:
    """Delete a test (sets status to deleted)."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.tests.delete(test_id_or_name)

        if ctx:
            await ctx.info(f"Deleted test: {test_id_or_name}")

        return f"Successfully deleted test '{test_id_or_name}'"
    except Exception as e:
        error_msg = f"Error deleting test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def run_test(
    name: str,
    test_ids: list[str],
    environment: str | None = None,
    tags: list[str] | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Execute tests and start a test run group."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if test_ids and tags:
        return "Error: test_ids and tags cannot be used together, provide one of them."

    try:
        group = await testzeus_client.test_run_groups.create_and_execute(
            name=name,
            test_ids=test_ids,
            execution_mode="lenient",  # Hardcoded to lenient
            environment=environment,
            tags=tags,
            notification_channels=notification_channels,
        )

        if ctx:
            await ctx.info(f"Started test run for test: {name}")

        return f"Successfully started test run '{group.name}' with ID: {group.id}"
    except Exception as e:
        error_msg = f"Error running test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Test Run Management Tools
@mcp.tool()
async def list_test_runs(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test runs in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.test_runs.get_list(**params)
        test_runs = result.get("items", [])

        run_list = []
        for run in test_runs:
            run_list.append(
                {
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "test": run.test,
                    "start_time": str(getattr(run, "start_time", None)),
                    "end_time": str(getattr(run, "end_time", None)),
                    "created": str(run.created),
                    "updated": str(run.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(run_list)} test runs")

        return f"Found {len(run_list)} test runs:\n{json.dumps(run_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing test runs: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_run(test_run_id: str, ctx: Context = None) -> str:
    """Get a specific test run by ID."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        details = await testzeus_client.test_runs.get_expanded(test_run_id)

        if ctx:
            await ctx.info(f"Retrieved test run: {details}")

        return f"Test run details:\n{json.dumps(details, cls=DateTimeEncoder, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_run(test_run_id: str, ctx: Context = None) -> str:
    """Delete a test run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_runs.delete(test_run_id)

        if ctx:
            await ctx.info(f"Deleted test run: {test_run_id}")

        return f"Successfully deleted test run with ID: {test_run_id}"
    except Exception as e:
        error_msg = f"Error deleting test run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Test Suite Management Tools
@mcp.tool()
async def list_test_suites(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test suites in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort

        result = await testzeus_client.test_suites.get_list(**params)
        suites = result.get("items", [])
        suite_list = [
            {
                "id": suite.id,
                "name": suite.name,
                "display_name": getattr(suite, "display_name", None),
                "status": suite.status,
                "execution_mode": getattr(suite, "execution_mode", None),
            }
            for suite in suites
        ]

        if ctx:
            await ctx.info(f"Found {len(suite_list)} test suites")

        return f"Found {len(suite_list)} test suites:\n{json.dumps(suite_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing test suites: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_suite(test_suite_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test suite by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        suite = await testzeus_client.test_suites.get_one(test_suite_id_or_name)
        suite_data = {
            "id": suite.id,
            "name": suite.name,
            "display_name": getattr(suite, "display_name", None),
            "status": suite.status,
            "workflow_definition": getattr(suite, "workflow_definition", None),
            "default_inputs": getattr(suite, "default_inputs", None),
            "execution_mode": getattr(suite, "execution_mode", None),
            "environment": getattr(suite, "environment", None),
            "tags": getattr(suite, "tags", []),
            "notification_channels": getattr(suite, "notification_channels", []),
        }

        if ctx:
            await ctx.info(f"Retrieved test suite: {suite.name}")

        return f"Test suite details:\n{json.dumps(suite_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test suite: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_suite(
    name: str,
    workflow_definition: dict[str, Any],
    default_inputs: dict[str, Any] | None = None,
    input_schema: list[dict[str, Any]] | None = None,
    status: str = "draft",
    execution_mode: Literal["lenient", "strict"] = "lenient",
    environment: str | None = None,
    tags: list[str] | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test suite."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        suite = await testzeus_client.test_suites.create(
            {
                "name": name,
                "workflow_definition": workflow_definition,
                "default_inputs": default_inputs or {},
                "input_schema": input_schema or [],
                "status": status,
                "execution_mode": execution_mode,
                "environment": environment,
                "tags": tags or [],
                "notification_channels": notification_channels or [],
            }
        )

        if ctx:
            await ctx.info(f"Created test suite: {name}")

        return f"Successfully created test suite '{name}' with ID: {suite.id}"
    except Exception as e:
        error_msg = f"Error creating test suite: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test_suite(
    test_suite_id_or_name: str,
    name: str | None = None,
    workflow_definition: dict[str, Any] | None = None,
    default_inputs: dict[str, Any] | None = None,
    input_schema: list[dict[str, Any]] | None = None,
    status: str | None = None,
    execution_mode: Literal["lenient", "strict"] | None = None,
    environment: str | None = None,
    tags: list[str] | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Update an existing test suite."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        data = {}
        if name is not None:
            data["name"] = name
        if workflow_definition is not None:
            data["workflow_definition"] = workflow_definition
        if default_inputs is not None:
            data["default_inputs"] = default_inputs
        if input_schema is not None:
            data["input_schema"] = input_schema
        if status is not None:
            data["status"] = status
        if execution_mode is not None:
            data["execution_mode"] = execution_mode
        if environment is not None:
            data["environment"] = environment
        if tags is not None:
            data["tags"] = tags
        if notification_channels is not None:
            data["notification_channels"] = notification_channels

        suite = await testzeus_client.test_suites.update(test_suite_id_or_name, data)

        if ctx:
            await ctx.info(f"Updated test suite: {suite.name}")

        return f"Successfully updated test suite '{suite.name}' (ID: {suite.id})"
    except Exception as e:
        error_msg = f"Error updating test suite: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_suite(test_suite_id_or_name: str, ctx: Context = None) -> str:
    """Delete a test suite."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        await testzeus_client.test_suites.delete(test_suite_id_or_name)
        if ctx:
            await ctx.info(f"Deleted test suite: {test_suite_id_or_name}")
        return f"Successfully deleted test suite '{test_suite_id_or_name}'"
    except Exception as e:
        error_msg = f"Error deleting test suite: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_test_suite_runs(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test suite runs in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort

        result = await testzeus_client.test_suite_runs.get_list(**params)
        runs = result.get("items", [])
        run_list = [
            {
                "id": run.id,
                "name": run.name,
                "status": run.status,
                "test_suite": getattr(run, "test_suite", None),
                "start_time": str(getattr(run, "start_time", None)),
                "end_time": str(getattr(run, "end_time", None)),
            }
            for run in runs
        ]

        if ctx:
            await ctx.info(f"Found {len(run_list)} test suite runs")

        return f"Found {len(run_list)} test suite runs:\n{json.dumps(run_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing test suite runs: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_suite_run(test_suite_run_id: str, ctx: Context = None) -> str:
    """Get a specific test suite run by ID."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        run = await testzeus_client.test_suite_runs.get_one(test_suite_run_id)
        run_data = {
            "id": run.id,
            "name": run.name,
            "status": run.status,
            "test_suite": getattr(run, "test_suite", None),
            "workflow_snapshot": getattr(run, "workflow_snapshot", None),
            "input_values": getattr(run, "input_values", None),
            "context_store": getattr(run, "context_store", None),
            "outputs": getattr(run, "outputs", None),
            "execution_checkpoint": getattr(run, "execution_checkpoint", None),
        }

        if ctx:
            await ctx.info(f"Retrieved test suite run: {run.name}")

        return f"Test suite run details:\n{json.dumps(run_data, cls=DateTimeEncoder, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test suite run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_suite_run(
    name: str,
    test_suite: str,
    input_values: dict[str, Any] | None = None,
    environment: str | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test suite run in lenient mode."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        run = await testzeus_client.test_suite_runs.run(
            display_name=name,
            test_suite=test_suite,
            input_values=input_values,
            environment=environment,
            notification_channels=notification_channels,
        )

        if ctx:
            await ctx.info(f"Created test suite run: {name}")

        return f"Successfully created test suite run '{name}' with ID: {run.id}"
    except Exception as e:
        error_msg = f"Error creating test suite run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def pause_test_suite_run(
    test_suite_run_id: str,
    mode: Literal["graceful", "immediate"] = "graceful",
    reason: str | None = None,
    ctx: Context = None,
) -> str:
    """Pause a running test suite run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        result = await testzeus_client.test_suite_runs.pause(
            test_suite_run_id,
            mode=mode,
            reason=reason,
        )
        result_msg = f"Pause result:\n{json.dumps(result, indent=2)}"
        if ctx:
            await ctx.info(f"Paused test suite run: {test_suite_run_id} (mode={mode})")
        return result_msg
    except Exception as e:
        error_msg = f"Error pausing test suite run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def resume_test_suite_run(test_suite_run_id: str, ctx: Context = None) -> str:
    """Resume a paused test suite run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        result = await testzeus_client.test_suite_runs.resume(test_suite_run_id)
        result_msg = f"Resume result:\n{json.dumps(result, indent=2)}"
        if ctx:
            await ctx.info(f"Resumed test suite run: {test_suite_run_id}")
        return result_msg
    except Exception as e:
        error_msg = f"Error resuming test suite run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def cancel_test_suite_run(test_suite_run_id: str, ctx: Context = None) -> str:
    """Cancel a running test suite run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        result = await testzeus_client.test_suite_runs.cancel(test_suite_run_id)
        result_msg = f"Cancel result:\n{json.dumps(result, indent=2)}"
        if ctx:
            await ctx.info(f"Cancelled test suite run: {test_suite_run_id}")
        return result_msg
    except Exception as e:
        error_msg = f"Error cancelling test suite run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_test_suite_node_runs(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test suite node runs in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort

        result = await testzeus_client.test_suite_node_runs.get_list(**params)
        node_runs = result.get("items", [])
        node_run_list = [
            {
                "id": node_run.id,
                "test_suite_run": getattr(node_run, "test_suite_run", None),
                "node_id": getattr(node_run, "node_id", None),
                "status": getattr(node_run, "status", None),
                "test_run": getattr(node_run, "test_run", None),
            }
            for node_run in node_runs
        ]
        result_msg = (
            f"Found {len(node_run_list)} test suite node runs:\n"
            f"{json.dumps(node_run_list, indent=2)}"
        )
        if ctx:
            await ctx.info(f"Found {len(node_run_list)} test suite node runs")
        return result_msg
    except Exception as e:
        error_msg = f"Error listing test suite node runs: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_test_suite_schedules(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test suite schedules in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort

        result = await testzeus_client.test_suite_schedules.get_list(**params)
        schedules = result.get("items", [])
        schedule_list = [
            {
                "id": schedule.id,
                "name": getattr(schedule, "name", None),
                "test_suite": getattr(schedule, "test_suite", None),
                "cron_expression": getattr(schedule, "cron_expression", None),
                "is_active": getattr(schedule, "is_active", None),
            }
            for schedule in schedules
        ]
        result_msg = (
            f"Found {len(schedule_list)} test suite schedules:\n"
            f"{json.dumps(schedule_list, indent=2)}"
        )
        if ctx:
            await ctx.info(f"Found {len(schedule_list)} test suite schedules")
        return result_msg
    except Exception as e:
        error_msg = f"Error listing test suite schedules: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Environment Management Tools
@mcp.tool()
async def list_environments(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List environments with pagination, sorting, and filtering.

    Secret-typed values in data content are masked in the output.

    Args:
        page: 1-based page number.
        per_page: Items per page (max 100).
        filters: Exact match: {"name": "staging"}. Partial match and other
            operators use the operator form: {"name": {"operator": "~", "value": "stag"}}.
            Operators: =, !=, >, >=, <, <=, ~ (contains), !~ (not contains).
            A list ORs values. Group with {"$and": [...]} / {"$or": [...]}.
        sort: Field name to sort by; prefix with '-' for descending (e.g. "-created").
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.environments.get_list(**params)
        environments = result.get("items", [])

        env_list = []
        for env in environments:
            env_list.append(_serialize_environment(env, detail=False))

        if ctx:
            await ctx.info(f"Found {len(env_list)} environments")

        return f"Found {len(env_list)} environments:\n{json.dumps(env_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing environments: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_environment(environment_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific environment by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.environments.get_one(environment_id_or_name)
        env_data = _serialize_environment(env, detail=True)

        if ctx:
            await ctx.info(f"Retrieved environment: {env.name}")

        return f"Environment details:\n{json.dumps(env_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_environment(
    name: str,
    device_type: Literal["browser", "mobile-android", "mobile-ios"] = "browser",
    data_content: dict[str, Any] | str | None = None,
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    mobile_supporting_data_file: str | None = None,
    mobile_device: str | None = None,
    connected_environments: list[str] | None = None,
    email_manager: list[str] | None = None,
    source_code_integrations: list[str] | None = None,
    agent_grounding_prompt: dict[str, Any] | str | None = None,
    ctx: Context = None,
) -> str:
    """Create a new environment. Returns the created record, including its ID.

    device_type controls which fields are allowed / shown:
    - 'browser' (default): supporting_data_files, connected_environments, email_manager
      (do not pass mobile_supporting_data_file or mobile_device)
    - 'mobile-android'/'mobile-ios': mobile_supporting_data_file, mobile_device
      (do not pass supporting_data_files or connected_environments)

    mobile_device is a device_pool ID or device_name (use list_device_pool to discover).
    data_content is a JSON object (or JSON string) in the format:
    {"items": [{"key": "name", "value": "val", "type": "variable|secret"}]}
    tags/connected_environments/email_manager must be names of existing records, or IDs.
    agent_grounding_prompt is a JSON object with 'test_creation' and/or
    'test_execution' string keys; missing keys default to "".
    """
    validation_error = _validate_environment_device_fields(
        device_type,
        supporting_data_files=supporting_data_files,
        mobile_supporting_data_file=mobile_supporting_data_file,
        mobile_device=mobile_device,
        connected_environments=connected_environments,
        email_manager=email_manager,
    )
    if validation_error:
        return validation_error

    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.environments.create_environment(
            name=name,
            device_type=device_type,
            data=data_content,
            tags=tags,
            supporting_data_files=supporting_data_files,
            mobile_supporting_data_file=mobile_supporting_data_file,
            mobile_device=mobile_device,
            connected_environments=connected_environments,
            email_manager=email_manager,
            source_code_integrations=source_code_integrations,
            agent_grounding_prompt=agent_grounding_prompt,
        )

        created = _serialize_environment(env, detail=True)

        if ctx:
            await ctx.info(f"Created environment: {name}")

        return f"Successfully created environment:\n{json.dumps(created, indent=2)}"
    except Exception as e:
        error_msg = f"Error creating environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_environment(
    environment_id: str,
    name: str | None = None,
    device_type: Literal["browser", "mobile-android", "mobile-ios"] | None = None,
    data_content: dict[str, Any] | str | None = None,
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    mobile_supporting_data_file: str | None = None,
    mobile_device: str | None = None,
    connected_environments: list[str] | None = None,
    email_manager: list[str] | None = None,
    source_code_integrations: list[str] | None = None,
    agent_grounding_prompt: dict[str, Any] | str | None = None,
    ctx: Context = None,
) -> str:
    """Update an environment by its 15-character ID or exact name.

    At least one field must be provided.
    device_type controls which fields are allowed / shown:
    - 'browser': supporting_data_files, connected_environments, email_manager
      (do not pass mobile_supporting_data_file or mobile_device)
    - 'mobile-android'/'mobile-ios': mobile_supporting_data_file, mobile_device
      (do not pass supporting_data_files or connected_environments)

    mobile_device is a device_pool ID or device_name (use list_device_pool to discover).
    data_content is a JSON object (or JSON string) in the format:
    {"items": [{"key": "name", "value": "val", "type": "variable|secret"}]}
    agent_grounding_prompt is a JSON object with 'test_creation' and/or
    'test_execution' string keys; keys not provided keep their current value.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    update_args = (
        name,
        device_type,
        data_content,
        tags,
        supporting_data_files,
        mobile_supporting_data_file,
        mobile_device,
        connected_environments,
        email_manager,
        source_code_integrations,
        agent_grounding_prompt,
    )
    if all(arg is None for arg in update_args):
        return "Error updating environment: provide at least one field to update"

    try:
        device_fields_touched = any(
            v is not None
            for v in (
                supporting_data_files,
                mobile_supporting_data_file,
                mobile_device,
                connected_environments,
                email_manager,
            )
        )
        if device_fields_touched or device_type is not None:
            effective_device_type = device_type
            if effective_device_type is None:
                existing = await testzeus_client.environments.get_one(environment_id)
                effective_device_type = existing.device_type or "browser"
            validation_error = _validate_environment_device_fields(
                effective_device_type,
                supporting_data_files=supporting_data_files,
                mobile_supporting_data_file=mobile_supporting_data_file,
                mobile_device=mobile_device,
                connected_environments=connected_environments,
                email_manager=email_manager,
            )
            if validation_error:
                return validation_error

        env = await testzeus_client.environments.update_environment(
            environment_id,
            name=name,
            device_type=device_type,
            env_data=data_content,
            tags=tags,
            supporting_data_files=supporting_data_files,
            mobile_supporting_data_file=mobile_supporting_data_file,
            mobile_device=mobile_device,
            connected_environments=connected_environments,
            email_manager=email_manager,
            source_code_integrations=source_code_integrations,
            agent_grounding_prompt=agent_grounding_prompt,
        )

        updated = _serialize_environment(env, detail=True)

        if ctx:
            await ctx.info(f"Updated environment: {env.name}")

        return f"Successfully updated environment:\n{json.dumps(updated, indent=2)}"

    except Exception as e:
        error_msg = f"Error updating environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_environment(environment_id: str, ctx: Context = None) -> str:
    """Delete an environment by its 15-character ID or exact name.

    The response identifies exactly which environment was deleted (name and ID).
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        # Resolve first so the response can state exactly what was deleted,
        # especially when a name (not an ID) was provided.
        env = await testzeus_client.environments.get_one(environment_id)
        await testzeus_client.environments.delete(env.id)

        matched_note = ""
        if env.id != environment_id:
            matched_note = f" (matched by name from '{environment_id}')"

        if ctx:
            await ctx.info(f"Deleted environment: {env.name} ({env.id})")

        return f"Successfully deleted environment '{env.name}' with ID: {env.id}{matched_note}"

    except Exception as e:
        error_msg = f"Error deleting environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_all_environment_files(environment_id: str, ctx: Context = None) -> str:
    """Remove all environment files."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.environments.remove_all_files(environment_id)
        if ctx:
            await ctx.info(f"Removed all environment files with ID: {environment_id}")
        return f"Successfully removed all environment files with ID: {environment_id}"
    except Exception as e:
        error_msg = f"Error removing all environment files: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def add_environment_file(environment_id: str, file_path: str, ctx: Context = None) -> str:
    """Add a environment file."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.environments.add_file(environment_id, file_path)
        if ctx:
            await ctx.info(f"Added file to environment: {environment_id}")
        return f"Successfully added file to environment with ID: {environment_id}"
    except Exception as e:
        error_msg = f"Error adding environment file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_environment_file(environment_id: str, file_path: str, ctx: Context = None) -> str:
    """Remove a environment file.

    file_path may be the stored file name, the original upload name, or a
    local path to the originally uploaded file.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.environments.remove_file(environment_id, file_path)
        if ctx:
            await ctx.info(f"Removed file from environment: {environment_id}")
        return f"Successfully removed file from environment with ID: {environment_id}"
    except Exception as e:
        error_msg = f"Error removing environment file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Device Pool tools (read-only)
@mcp.tool()
async def list_device_pool(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List available devices in the device pool.

    Devices can be filtered by platform (android/ios),
    cloud_provider (browserstack/saucelabs/local),
    device_type (real/virtual), and is_active (true/false).
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.device_pool.get_list(**params)
        devices = result.get("items", [])

        device_list = []
        for device in devices:
            device_list.append(
                {
                    "id": device.id,
                    "device_name": device.device_name,
                    "platform": device.platform,
                    "platform_version": device.platform_version,
                    "cloud_provider": device.cloud_provider,
                    "device_type": device.device_type,
                    "is_active": device.is_active,
                    "concurrency_limit": device.concurrency_limit,
                    "active_sessions": device.active_sessions,
                    "automation_name": device.automation_name,
                    "device_tier": device.device_tier,
                }
            )

        if ctx:
            await ctx.info(f"Found {len(device_list)} devices")

        return f"Found {len(device_list)} devices:\n{json.dumps(device_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing device pool: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_device_pool_entry(device_id: str, ctx: Context = None) -> str:
    """Get a specific device from the pool by ID."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        device = await testzeus_client.device_pool.get_one(device_id)
        device_data = {
            "id": device.id,
            "device_name": device.device_name,
            "platform": device.platform,
            "platform_version": device.platform_version,
            "cloud_provider": device.cloud_provider,
            "device_type": device.device_type,
            "is_active": device.is_active,
            "concurrency_limit": device.concurrency_limit,
            "active_sessions": device.active_sessions,
            "automation_name": device.automation_name,
            "device_tier": device.device_tier,
            "created": str(device.created),
            "updated": str(device.updated),
        }

        if ctx:
            await ctx.info(f"Retrieved device: {device.device_name}")

        return f"Device details:\n{json.dumps(device_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting device: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


def _format_files(files_info: Any, stored: Any) -> list:
    """Render a file field as {display_name, name} pairs when the server
    provides the original-name mapping, falling back to stored names.

    Works for both multi-file fields (list) and single-file fields (str).
    """
    if files_info:
        return files_info
    if not stored:
        return []
    if isinstance(stored, str):
        stored = [stored]
    return [{"name": f} for f in stored]


def _format_supporting_files(entity: Any) -> list:
    return _format_files(
        getattr(entity, "supporting_data_files_info", None),
        entity.supporting_data_files,
    )


def _is_mobile_device_type(device_type: str | None) -> bool:
    return (device_type or "browser") in ("mobile-android", "mobile-ios")


def _validate_environment_device_fields(
    device_type: str | None,
    *,
    supporting_data_files: Any = None,
    mobile_supporting_data_file: Any = None,
    mobile_device: Any = None,
    connected_environments: Any = None,
    email_manager: Any = None,
) -> str | None:
    """Return an error message when fields conflict with device_type, else None.

    browser: supporting_data_files / connected_environments / email_manager allowed;
             mobile_supporting_data_file / mobile_device forbidden.
    mobile-*: mobile_supporting_data_file / mobile_device allowed;
              supporting_data_files / connected_environments / email_manager forbidden.
    """
    is_mobile = _is_mobile_device_type(device_type)
    if is_mobile:
        if supporting_data_files or connected_environments or email_manager:
            return (
                "Error: supporting_data_files, connected_environments, and "
                "email_manager are not allowed for mobile environments"
            )
    else:
        if mobile_supporting_data_file or mobile_device:
            return (
                "Error: mobile_supporting_data_file and mobile_device are only "
                "allowed for mobile-android/mobile-ios environments"
            )
    return None


def _serialize_environment(env: Any, *, detail: bool = False) -> dict[str, Any]:
    """Serialize an environment, omitting fields that do not apply to device_type."""
    device_type = getattr(env, "device_type", None) or "browser"
    is_mobile = _is_mobile_device_type(device_type)

    data: dict[str, Any] = {
        "id": env.id,
        "name": env.name,
        "device_type": device_type,
        "data": _mask_secret_values(env.data_content),
        "tags": env.tags,
        "created": str(env.created),
        "updated": str(env.updated),
    }

    if is_mobile:
        data["mobile_supporting_data_file"] = _format_files(
            getattr(env, "mobile_supporting_data_file_info", None),
            getattr(env, "mobile_supporting_data_file", None),
        )
        data["mobile_device"] = getattr(env, "mobile_device", None)
    else:
        data["supporting_data_files"] = _format_supporting_files(env)
        if detail:
            data["connected_environments"] = getattr(env, "connected_environments", None)
            data["browser_auth_file"] = _format_files(
                getattr(env, "browser_auth_file_info", None),
                getattr(env, "browser_auth_file", None),
            )
            data["email_manager"] = getattr(env, "email_manager", None)

    if detail:
        data["source_code_integrations"] = getattr(env, "source_code_integrations", None)
        data["agent_grounding_prompt"] = getattr(env, "agent_grounding_prompt", None)
        data["tenant"] = getattr(env, "tenant", None)
        data["modified_by"] = getattr(env, "modified_by", None)

    return data


def _mask_secret_values(content: Any) -> Any:
    """Mask the values of secret-typed items in test data content before display."""
    if isinstance(content, dict) and isinstance(content.get("items"), list):
        masked_items = []
        for item in content["items"]:
            if isinstance(item, dict) and item.get("type") == "secret":
                item = {**item, "value": "********"}
            masked_items.append(item)
        return {**content, "items": masked_items}
    return content


@mcp.tool()
async def get_test_data(test_data_id: str, ctx: Context = None) -> str:
    """Get a specific test data record by its 15-character ID or exact name.

    Secret-typed values in the data content are masked in the output.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.test_data.get_one(test_data_id)
        test_data = {
            "id": test.id,
            "name": test.name,
            "tags": test.tags,
            "created": str(test.created),
            "updated": str(test.updated),
            "tenant": test.tenant,
            "modified_by": test.modified_by,
            "data_content": _mask_secret_values(test.data_content),
            "metadata": test.metadata,
            "agent_grounding_prompt": test.agent_grounding_prompt,
            "supporting_data_files": _format_supporting_files(test),
        }

        if ctx:
            await ctx.info(f"Retrieved test data: {test.name}")

        return f"Test data details:\n{json.dumps(test_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_data(
    name: str,
    content: dict[str, Any] | str | None = None,
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    agent_grounding_prompt: dict[str, Any] | str | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test data record. Returns the created record, including its ID.

    content is a JSON object (or JSON string) in the format:
    {"items": [{"key": "name", "value": "val", "type": "variable|secret"}]}
    tags must be names of existing tags, or tag IDs.
    agent_grounding_prompt is a JSON object with 'test_creation' and/or
    'test_execution' string keys; missing keys default to "".
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test_data = await testzeus_client.test_data.create_test_data(
            name=name,
            content=content,
            tags=tags,
            type="test",
            supporting_data_files=supporting_data_files,
            agent_grounding_prompt=agent_grounding_prompt,
        )

        created = {
            "id": test_data.id,
            "name": test_data.name,
            "tags": test_data.tags,
            "data_content": _mask_secret_values(test_data.data_content),
            "agent_grounding_prompt": test_data.agent_grounding_prompt,
            "created": str(test_data.created),
        }

        if ctx:
            await ctx.info(f"Created test data: {name}")

        return f"Successfully created test data:\n{json.dumps(created, indent=2)}"

    except Exception as e:
        error_msg = f"Error creating test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_data(test_data_id: str, ctx: Context = None) -> str:
    """Delete a test data record by its 15-character ID or exact name.

    The response identifies exactly which record was deleted (name and ID).
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        # Resolve first so the response can state exactly what was deleted,
        # especially when a name (not an ID) was provided.
        test_data = await testzeus_client.test_data.get_one(test_data_id)
        await testzeus_client.test_data.delete(test_data.id)

        matched_note = ""
        if test_data.id != test_data_id:
            matched_note = f" (matched by name from '{test_data_id}')"

        if ctx:
            await ctx.info(f"Deleted test data: {test_data.name} ({test_data.id})")

        return (
            f"Successfully deleted test data '{test_data.name}' "
            f"with ID: {test_data.id}{matched_note}"
        )

    except Exception as e:
        error_msg = f"Error deleting test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test_data(
    test_data_id: str,
    name: str | None = None,
    content: dict[str, Any] | str | None = None,
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    agent_grounding_prompt: dict[str, Any] | str | None = None,
    ctx: Context = None,
) -> str:
    """Update a test data record by its 15-character ID or exact name.

    At least one field must be provided.
    content is a JSON object (or JSON string) in the format:
    {"items": [{"key": "name", "value": "val", "type": "variable|secret"}]}
    tags must be names of existing tags, or tag IDs.
    agent_grounding_prompt is a JSON object with 'test_creation' and/or
    'test_execution' string keys; keys not provided keep their current value.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    update_args = (name, content, tags, supporting_data_files, agent_grounding_prompt)
    if all(arg is None for arg in update_args):
        return (
            "Error updating test data: provide at least one field to update "
            "(name, content, tags, supporting_data_files, or agent_grounding_prompt)"
        )

    try:
        test_data = await testzeus_client.test_data.update_test_data(
            test_data_id,
            name=name,
            content=content,
            tags=tags,
            supporting_data_files=supporting_data_files,
            agent_grounding_prompt=agent_grounding_prompt,
        )

        updated = {
            "id": test_data.id,
            "name": test_data.name,
            "tags": test_data.tags,
            "data_content": _mask_secret_values(test_data.data_content),
            "agent_grounding_prompt": test_data.agent_grounding_prompt,
            "updated": str(test_data.updated),
        }

        if ctx:
            await ctx.info(f"Updated test data: {test_data.name}")

        return f"Successfully updated test data:\n{json.dumps(updated, indent=2)}"

    except Exception as e:
        error_msg = f"Error updating test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_test_data(
    page: int = 1,
    per_page: int = 10,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List test data with pagination, sorting, and filtering.

    Secret-typed values in data content are masked in the output.

    Args:
        page: 1-based page number.
        per_page: Items per page (max 100).
        filters: Exact match: {"name": "smoke-data"}. Partial match and other
            operators use the operator form: {"name": {"operator": "~", "value": "smoke"}}.
            Operators: =, !=, >, >=, <, <=, ~ (contains), !~ (not contains).
            A list ORs values. Group with {"$and": [...]} / {"$or": [...]}.
        sort: Field name to sort by; prefix with '-' for descending (e.g. "-created").
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.test_data.get_list(**params)
        test_data_full_list = result.get("items", [])

        test_data_list = []
        for test_data in test_data_full_list:
            test_data_list.append(
                {
                    "id": test_data.id,
                    "name": test_data.name,
                    "tags": test_data.tags,
                    "data_content": _mask_secret_values(test_data.data_content),
                    "supporting_data_files": _format_supporting_files(test_data),
                    "created": str(test_data.created),
                    "updated": str(test_data.updated),
                    "tenant": test_data.tenant,
                    "modified_by": test_data.modified_by,
                }
            )

        if ctx:
            await ctx.info(f"Found {len(test_data_list)} test data")

        return f"Found {len(test_data_list)} test data:\n{json.dumps(test_data_list, indent=2)}"

    except Exception as e:
        error_msg = f"Error listing test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_all_test_data_files(test_data_id: str, ctx: Context = None) -> str:
    """Remove all test data files."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_data.remove_all_files(test_data_id)
        if ctx:
            await ctx.info(f"Removed all test data files for test data: {test_data_id}")
        return f"Successfully removed all test data files for test data with ID: {test_data_id}"
    except Exception as e:
        error_msg = f"Error removing all test data files: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def add_test_data_file(test_data_id: str, file_path: str, ctx: Context = None) -> str:
    """Add a test data file."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_data.add_file(test_data_id, file_path)
        if ctx:
            await ctx.info(f"Added file to test data: {test_data_id}")
        return f"Successfully added file to test data with ID: {test_data_id}"
    except Exception as e:
        error_msg = f"Error adding file to test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_test_data_file(test_data_id: str, file_path: str, ctx: Context = None) -> str:
    """Remove a test data file.

    file_path may be the stored file name, the original upload name, or a
    local path to the originally uploaded file.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_data.remove_file(test_data_id, file_path)
        if ctx:
            await ctx.info(f"Removed file from test data: {test_data_id}")
        return f"Successfully removed file from test data with ID: {test_data_id}"
    except Exception as e:
        error_msg = f"Error removing file from test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# HYPERMIND CODE BLOCKS OPERATIONS
# ============================================================================


@mcp.tool()
async def list_hypermind_code_blocks(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all hypermind code blocks in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.hypermind_code_blocks.get_list(**params)
        code_blocks = result.get("items", [])

        code_block_list = []
        for block in code_blocks:
            code_block_list.append(
                {
                    "id": block.id,
                    "name": block.name,
                    "status": block.status,
                    "tags": block.tags,
                    "code_files": block.code_files,
                    "created": str(block.created),
                    "updated": str(block.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(code_block_list)} hypermind code blocks")

        result = json.dumps(code_block_list, indent=2)
        return f"Found {len(code_block_list)} hypermind code blocks:\n{result}"
    except Exception as e:
        error_msg = f"Error listing hypermind code blocks: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_hypermind_code_block(code_block_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific hypermind code block by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        block = await testzeus_client.hypermind_code_blocks.get_one(code_block_id_or_name)
        block_data = {
            "id": block.id,
            "name": block.name,
            "status": block.status,
            "tags": block.tags,
            "code_files": block.code_files,
            "created": str(block.created),
            "updated": str(block.updated),
            "tenant": block.tenant,
            "modified_by": block.modified_by,
        }

        if ctx:
            await ctx.info(f"Retrieved hypermind code block: {block.name}")

        return f"Hypermind code block details:\n{json.dumps(block_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_hypermind_code_block(
    name: str,
    status: Literal["draft", "ready", "deleted"] = "draft",
    tags: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        block = await testzeus_client.hypermind_code_blocks.create_hypermind_code_block(
            name=name,
            status=status,
            tags=tags,
        )

        if ctx:
            await ctx.info(f"Created hypermind code block: {name}")

        return f"Successfully created hypermind code block '{name}' with ID: {block.id}"
    except Exception as e:
        error_msg = f"Error creating hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_hypermind_code_block(
    code_block_id: str,
    name: str | None = None,
    status: Literal["draft", "ready", "deleted"] | None = None,
    tags: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Update a hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if status:
            data["status"] = status
        if tags:
            data["tags"] = tags

        await testzeus_client.hypermind_code_blocks.update_hypermind_code_block(
            code_block_id, **data
        )

        if ctx:
            await ctx.info(f"Updated hypermind code block: {code_block_id}")

        return f"Successfully updated hypermind code block with ID: {code_block_id}"
    except Exception as e:
        error_msg = f"Error updating hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_hypermind_code_block(code_block_id: str, ctx: Context = None) -> str:
    """Delete a hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.hypermind_code_blocks.delete(code_block_id)

        if ctx:
            await ctx.info(f"Deleted hypermind code block: {code_block_id}")

        return f"Successfully deleted hypermind code block with ID: {code_block_id}"
    except Exception as e:
        error_msg = f"Error deleting hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def add_hypermind_code_block_file(
    code_block_id: str, file_path: str, ctx: Context = None
) -> str:
    """Add a code file to a hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.hypermind_code_blocks.add_file(code_block_id, file_path)
        if ctx:
            await ctx.info(f"Added file to hypermind code block: {code_block_id}")
        return f"Successfully added file to hypermind code block with ID: {code_block_id}"
    except Exception as e:
        error_msg = f"Error adding file to hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_hypermind_code_block_file(
    code_block_id: str, file_path: str, ctx: Context = None
) -> str:
    """Remove a code file from a hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.hypermind_code_blocks.remove_file(code_block_id, file_path)
        if ctx:
            await ctx.info(f"Removed file from hypermind code block: {code_block_id}")
        return f"Successfully removed file from hypermind code block with ID: {code_block_id}"
    except Exception as e:
        error_msg = f"Error removing file from hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_all_hypermind_code_block_files(code_block_id: str, ctx: Context = None) -> str:
    """Remove all code files from a hypermind code block."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.hypermind_code_blocks.remove_all_files(code_block_id)
        if ctx:
            await ctx.info(f"Removed all files from hypermind code block: {code_block_id}")
        return f"Successfully removed all files from hypermind code block with ID: {code_block_id}"
    except Exception as e:
        error_msg = f"Error removing all files from hypermind code block: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# USER INTEGRATION OPERATIONS
# ============================================================================


@mcp.tool()
async def list_user_integrations(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all user integrations in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.user_integrations.get_list(**params)
        integrations = result.get("items", [])

        integration_list = []
        for integration in integrations:
            integration_list.append(
                {
                    "id": integration.id,
                    "name": integration.name,
                    "integration_type": getattr(integration, "integration_type", None),
                    "connection_status": getattr(integration, "connection_status", None),
                    "project_id": getattr(integration, "project_id", None),
                    "created": str(integration.created),
                    "updated": str(integration.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(integration_list)} user integrations")

        result = json.dumps(integration_list, indent=2)
        return f"Found {len(integration_list)} user integrations:\n{result}"
    except Exception as e:
        error_msg = f"Error listing user integrations: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_user_integration(integration_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific user integration by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        integration = await testzeus_client.user_integrations.get_one(integration_id_or_name)
        integration_data = {
            "id": integration.id,
            "name": integration.name,
            "integration_type": getattr(integration, "integration_type", None),
            "connection_status": getattr(integration, "connection_status", None),
            "project_id": getattr(integration, "project_id", None),
            "auth_config_id": getattr(integration, "auth_config_id", None),
            "connected_account_id": getattr(integration, "connected_account_id", None),
            "scopes": getattr(integration, "scopes", None),
            "created": str(integration.created),
            "updated": str(integration.updated),
            "tenant_id": getattr(integration, "tenant_id", None),
            "user_id": getattr(integration, "user_id", None),
        }

        if ctx:
            await ctx.info(f"Retrieved user integration: {integration.name}")

        return f"User integration details:\n{json.dumps(integration_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting user integration: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# CONNECTED ENVIRONMENT OPERATIONS
# ============================================================================


@mcp.tool()
async def list_connected_environments(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all connected environments in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.connected_environments.get_list(**params)
        connected_envs = result.get("items", [])

        connected_env_list = []
        for env in connected_envs:
            connected_env_list.append(
                {
                    "id": env.id,
                    "name": env.name,
                    "connection": getattr(env, "connection", None),
                    "created": str(env.created),
                    "updated": str(env.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(connected_env_list)} connected environments")

        result = json.dumps(connected_env_list, indent=2)
        return f"Found {len(connected_env_list)} connected environments:\n{result}"
    except Exception as e:
        error_msg = f"Error listing connected environments: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_connected_environment(connected_env_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific connected environment by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.connected_environments.get_one(connected_env_id_or_name)
        env_data = {
            "id": env.id,
            "name": env.name,
            "connection": getattr(env, "connection", None),
            "created": str(env.created),
            "updated": str(env.updated),
            "tenant": env.tenant,
            "modified_by": env.modified_by,
        }

        if ctx:
            await ctx.info(f"Retrieved connected environment: {env.name}")

        return f"Connected environment details:\n{json.dumps(env_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting connected environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_connected_environment(
    name: str,
    connection: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.connected_environments.create_connected_environment(
            name=name,
            connection=connection,
            tags=tags,
            metadata=metadata,
        )

        if ctx:
            await ctx.info(f"Created connected environment: {name}")

        return f"Successfully created connected environment '{name}' with ID: {env.id}"
    except Exception as e:
        error_msg = f"Error creating connected environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_connected_environment(
    connected_env_id: str,
    name: str | None = None,
    connection: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Update a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if connection:
            data["connection"] = connection
        if tags:
            data["tags"] = tags
        if metadata:
            data["metadata"] = metadata

        await testzeus_client.connected_environments.update_connected_environment(
            connected_env_id, **data
        )

        if ctx:
            await ctx.info(f"Updated connected environment: {connected_env_id}")

        return f"Successfully updated connected environment with ID: {connected_env_id}"
    except Exception as e:
        error_msg = f"Error updating connected environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_connected_environment(connected_env_id: str, ctx: Context = None) -> str:
    """Delete a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.connected_environments.delete(connected_env_id)

        if ctx:
            await ctx.info(f"Deleted connected environment: {connected_env_id}")

        return f"Successfully deleted connected environment with ID: {connected_env_id}"
    except Exception as e:
        error_msg = f"Error deleting connected environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_tags(name: str, value: str | None = None, ctx: Context = None) -> str:
    """Create a single tag. Returns the created tag, including its ID."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        tag = await testzeus_client.tags.create_tag(name=name, value=value)

        tag_data = {
            "id": tag.id,
            "name": tag.name,
            "value": tag.value,
            "created": str(tag.created),
        }

        if ctx:
            await ctx.info(f"Created tag: {name}")

        return f"Successfully created tag:\n{json.dumps(tag_data, indent=2)}"

    except Exception as e:
        error_msg = f"Error creating tag: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_tags(
    page: int = 1,
    per_page: int = 10,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List tags with pagination, sorting, and filtering.

    Args:
        page: 1-based page number.
        per_page: Items per page (max 100).
        filters: Exact match: {"name": "smoke"}. Partial match and other
            operators use the operator form: {"name": {"operator": "~", "value": "smoke"}}.
            Operators: =, !=, >, >=, <, <=, ~ (contains), !~ (not contains).
            A list ORs values: {"name": ["a", "b"]}. Group with {"$and": [...]} / {"$or": [...]}.
        sort: Field name to sort by; prefix with '-' for descending (e.g. "-created").
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.tags.get_list(**params)
        tags = result.get("items", [])

        tag_list = []
        for tag in tags:
            tag_list.append(
                {
                    "id": tag.id,
                    "name": tag.name,
                    "value": tag.value,
                    "created": str(tag.created),
                    "updated": str(tag.updated),
                    "tenant": tag.tenant,
                    "modified_by": tag.modified_by,
                }
            )

        if ctx:
            await ctx.info(f"Found {len(tag_list)} tags")

        return f"Found {len(tag_list)} tags:\n{json.dumps(tag_list, indent=2)}"

    except Exception as e:
        error_msg = f"Error listing tags: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_tag(tag_id: str, ctx: Context = None) -> str:
    """Get a specific tag by its 15-character ID or exact name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        tag = await testzeus_client.tags.get_one(tag_id)

        tag_data = {
            "id": tag.id,
            "name": tag.name,
            "value": tag.value,
            "tenant": tag.tenant,
            "modified_by": tag.modified_by,
            "created": str(tag.created),
            "updated": str(tag.updated),
        }

        if ctx:
            await ctx.info(f"Retrieved tag: {tag.name}")

        return f"Tag details:\n{json.dumps(tag_data, indent=2)}"

    except Exception as e:
        error_msg = f"Error getting tag: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_tag(tag_id: str, ctx: Context = None) -> str:
    """Delete a tag by its 15-character ID or exact name.

    The response identifies exactly which tag was deleted (name and ID).
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        # Resolve first so the response can state exactly what was deleted,
        # especially when a name (not an ID) was provided.
        tag = await testzeus_client.tags.get_one(tag_id)
        await testzeus_client.tags.delete(tag.id)

        matched_note = "" if tag.id == tag_id else f" (matched by name from '{tag_id}')"

        if ctx:
            await ctx.info(f"Deleted tag: {tag.name} ({tag.id})")

        return f"Successfully deleted tag '{tag.name}' with ID: {tag.id}{matched_note}"

    except Exception as e:
        error_msg = f"Error deleting tag: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_tag(
    tag_id: str, name: str | None = None, value: str | None = None, ctx: Context = None
) -> str:
    """Update a tag's name and/or value by its 15-character ID or exact name.

    At least one of name or value must be provided. Pass value="" to clear the value.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if name is None and value is None:
        return "Error updating tag: provide at least one of 'name' or 'value' to update"

    try:
        tag = await testzeus_client.tags.update_tag(tag_id, name=name, value=value)

        tag_data = {
            "id": tag.id,
            "name": tag.name,
            "value": tag.value,
            "updated": str(tag.updated),
        }

        if ctx:
            await ctx.info(f"Updated tag: {tag.name}")

        return f"Successfully updated tag:\n{json.dumps(tag_data, indent=2)}"

    except Exception as e:
        error_msg = f"Error updating tag: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Test Run Group Management Tools
@mcp.tool()
async def list_test_run_groups(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test run groups in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.test_run_groups.get_list(**params)
        test_run_groups = result.get("items", [])

        group_list = []
        for group in test_run_groups:
            group_list.append(
                {
                    "id": group.id,
                    "name": getattr(group, "name", None),
                    "status": group.status,
                    "ctrf_status": getattr(group, "ctrf_status", None),
                    "execution_mode": group.execution_mode,
                    "test_ids": getattr(group, "test_ids", []),
                    "tags": getattr(group, "tags", []),
                    "environment": getattr(group, "environment", None),
                    "created": str(group.created),
                    "updated": str(group.updated),
                }
            )

        if ctx:
            await ctx.info(f"Found {len(group_list)} test run groups")

        return f"Found {len(group_list)} test run groups:\n{json.dumps(group_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing test run groups: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_run_group(test_run_group_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test run group by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        group = await testzeus_client.test_run_groups.get_one(test_run_group_id_or_name)
        group_data = {
            "id": group.id,
            "name": group.name,
            "display_name": getattr(group, "display_name", None),
            "status": group.status,
            "ctrf_status": getattr(group, "ctrf_status", None),
            "execution_mode": group.execution_mode,
            "test_ids": getattr(group, "test_ids", []),
            "tags": getattr(group, "tags", []),
            "environment": getattr(group, "environment", None),
            "notification_channels": getattr(group, "notification_channels", []),
            "test_report_run": getattr(group, "test_report_run", None),
            "created": str(group.created),
            "updated": str(group.updated),
            "created_by": getattr(group, "created_by", None),
        }

        if ctx:
            await ctx.info(f"Retrieved test run group: {group.name}")

        return f"Test run group details:\n{json.dumps(group_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test run group: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_run_group(
    name: str,
    test_ids: list[str] | None = None,
    environment: str | None = None,
    tags: list[str] | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create and execute a new test runs in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if test_ids and tags:
        return "Error: test_ids and tags cannot be used together, provide one of them."

    try:
        group = await testzeus_client.test_run_groups.create_and_execute(
            name=name,
            test_ids=test_ids,
            execution_mode="lenient",  # Hardcoded to lenient
            environment=environment,
            tags=tags,
            notification_channels=notification_channels,
        )

        if ctx:
            await ctx.info(f"Created test run group: {name}")

        return f"Successfully created test run group '{name}' with ID: {group.id}"
    except Exception as e:
        error_msg = f"Error creating test run group: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_run_group(test_run_group_id_or_name: str, ctx: Context = None) -> str:
    """Delete a test run group (sets status to deleted)."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_run_groups.delete(test_run_group_id_or_name)

        if ctx:
            await ctx.info(f"Deleted test run group: {test_run_group_id_or_name}")

        return f"Successfully deleted test run group '{test_run_group_id_or_name}'"
    except Exception as e:
        error_msg = f"Error deleting test run group: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def cancel_test_run_group(test_run_group_id_or_name: str, ctx: Context = None) -> str:
    """Cancel all running test runs in a test run group."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        group = await testzeus_client.test_run_groups.cancel_group(test_run_group_id_or_name)

        if ctx:
            await ctx.info(f"Cancelled test run group: {test_run_group_id_or_name}")

        return f"Successfully cancelled test run group '{group.name}' (ID: {group.id})"
    except Exception as e:
        error_msg = f"Error cancelling test run group: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def download_test_run_group_report(
    test_run_group_id_or_name: str,
    output_dir: str = "downloads",
    format: Literal["ctrf", "pdf", "csv", "zip"] = "pdf",
    ctx: Context = None,
) -> str:
    """Download the report for a test run group."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        file_path = await testzeus_client.test_run_groups.download_report(
            test_run_group_id_or_name, output_dir, format
        )

        if file_path:
            if ctx:
                await ctx.info(f"Downloaded report for test run group: {test_run_group_id_or_name}")
            return f"Successfully downloaded report to: {file_path}"
        else:
            return f"No report available for test run group '{test_run_group_id_or_name}'"

    except Exception as e:
        error_msg = f"Error downloading test run group report: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def download_test_run_group_attachments(
    test_run_group_id_or_name: str,
    output_dir: str = "downloads",
    ctx: Context = None,
) -> str:
    """Download all attachments for all test runs in a test run group."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        downloaded_attachments = await testzeus_client.test_run_groups.download_all_attachments(
            test_run_group_id_or_name, output_dir
        )

        total_files = sum(len(files) for files in downloaded_attachments.values())

        if ctx:
            await ctx.info(
                f"Downloaded {total_files} attachments for test run group: "
                f"{test_run_group_id_or_name}"
            )

        result = {
            "test_run_group": test_run_group_id_or_name,
            "total_files_downloaded": total_files,
            "downloads_by_test_run": downloaded_attachments,
            "output_directory": output_dir,
        }

        return f"Downloaded attachments for test run group:\n{json.dumps(result, indent=2)}"

    except Exception as e:
        error_msg = f"Error downloading test run group attachments: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Resources for browsing TestZeus entities
@mcp.resource("tests://")
async def list_tests_resource() -> str:
    """List all tests as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.tests.get_list(per_page=100)
        tests = result.get("items", [])

        test_list = []
        for test in tests:
            test_list.append(
                {
                    "id": test.id,
                    "name": test.name,
                    "status": test.status,
                    "testing_type": test.testing_type,
                    "test_feature": test.test_feature,
                    "uri": f"test://{test.id}",
                }
            )

        return json.dumps({"tests": test_list}, indent=2)
    except Exception as e:
        return f"Error listing tests: {str(e)}"


@mcp.resource("test://{test_id}")
async def get_test_resource(test_id: str) -> str:
    """Get a specific test as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.tests.get_one(test_id)
        test_data = {
            "id": test.id,
            "name": test.name,
            "status": test.status,
            "testing_type": test.testing_type,
            "test_feature": test.test_feature,
            "tags": test.tags,
            "test_data": test.test_data,
            "environment": test.environment,
            "config": getattr(test, "config", None),
            "metadata": getattr(test, "metadata", None),
            "created": str(test.created),
            "updated": str(test.updated),
            "modified_by": test.modified_by,
        }

        return json.dumps(test_data, indent=2)
    except Exception as e:
        return f"Error getting test: {str(e)}"


@mcp.resource("test-runs://")
async def list_test_runs_resource() -> str:
    """List all test runs as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.test_runs.get_list(per_page=100)
        test_runs = result.get("items", [])

        run_list = []
        for run in test_runs:
            run_list.append(
                {
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "test": run.test,
                    "uri": f"test-run://{run.id}",
                }
            )

        return json.dumps({"test_runs": run_list}, indent=2)
    except Exception as e:
        return f"Error listing test runs: {str(e)}"


@mcp.resource("test-run://{test_run_id}")
async def get_test_run_resource(test_run_id: str) -> str:
    """Get a specific test run as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        run = await testzeus_client.test_runs.get_one(test_run_id)
        run_data = {
            "id": run.id,
            "name": run.name,
            "status": run.status,
            "test_status": getattr(run, "test_status", None),
            "start_time": str(getattr(run, "start_time", None)),
            "end_time": str(getattr(run, "end_time", None)),
            "tags": getattr(run, "tags", []),
            "metadata": getattr(run, "metadata", None),
            "created": str(run.created),
            "updated": str(run.updated),
            "modified_by": run.modified_by,
        }

        return json.dumps(run_data, indent=2)
    except Exception as e:
        return f"Error getting test run: {str(e)}"


@mcp.resource("environments://")
async def list_environments_resource() -> str:
    """List all environments as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.environments.get_list(per_page=100)
        environments = result.get("items", [])

        env_list = []
        for env in environments:
            summary = {
                "id": env.id,
                "name": env.name,
                "device_type": env.device_type,
                "description": _mask_secret_values(env.data_content),
                "uri": f"environment://{env.id}",
            }
            if _is_mobile_device_type(env.device_type):
                summary["mobile_device"] = getattr(env, "mobile_device", None)
                summary["files"] = 1 if env.mobile_supporting_data_file else 0
            else:
                files = env.supporting_data_files
                summary["files"] = len(files) if files else 0
            env_list.append(summary)

        return json.dumps({"environments": env_list}, indent=2)
    except Exception as e:
        return f"Error listing environments: {str(e)}"


@mcp.resource("environment://{environment_id}")
async def get_environment_resource(environment_id: str) -> str:
    """Get a specific environment as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.environments.get_one(environment_id)
        env_data = _serialize_environment(env, detail=True)
        env_data["description"] = env_data.pop("data", None)
        env_data["files"] = (
            len(env.supporting_data_files)
            if not _is_mobile_device_type(env.device_type) and env.supporting_data_files
            else (
                1
                if _is_mobile_device_type(env.device_type) and env.mobile_supporting_data_file
                else 0
            )
        )

        return json.dumps(env_data, indent=2)
    except Exception as e:
        return f"Error getting environment: {str(e)}"


@mcp.resource("device-pool://")
async def list_device_pool_resource() -> str:
    """List all devices in the pool as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.device_pool.get_list(per_page=100)
        devices = result.get("items", [])

        device_list = []
        for device in devices:
            device_list.append(
                {
                    "id": device.id,
                    "device_name": device.device_name,
                    "platform": device.platform,
                    "platform_version": device.platform_version,
                    "cloud_provider": device.cloud_provider,
                    "is_active": device.is_active,
                    "uri": f"device-pool://{device.id}",
                }
            )

        return json.dumps({"device_pool": device_list}, indent=2)
    except Exception as e:
        return f"Error listing device pool: {str(e)}"


@mcp.resource("device-pool://{device_id}")
async def get_device_pool_resource(device_id: str) -> str:
    """Get a specific device from the pool as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        device = await testzeus_client.device_pool.get_one(device_id)
        device_data = {
            "id": device.id,
            "device_name": device.device_name,
            "platform": device.platform,
            "platform_version": device.platform_version,
            "cloud_provider": device.cloud_provider,
            "device_type": device.device_type,
            "is_active": device.is_active,
            "concurrency_limit": device.concurrency_limit,
            "active_sessions": device.active_sessions,
            "automation_name": device.automation_name,
            "device_tier": device.device_tier,
            "created": str(device.created),
            "updated": str(device.updated),
        }

        return json.dumps(device_data, indent=2)
    except Exception as e:
        return f"Error getting device: {str(e)}"


@mcp.resource("test-data://")
async def list_test_data_resource() -> str:
    """List all test data as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.test_data.get_list(per_page=100)
        test_data = result.get("items", [])

        test_data_list = []
        for test_data in test_data:
            test_data_list.append(
                {
                    "id": test_data.id,
                    "name": test_data.name,
                    "tags": test_data.tags,
                    "data_content": _mask_secret_values(test_data.data_content),
                    "files": len(test_data.supporting_data_files or []),
                    "uri": f"test-data://{test_data.id}",
                }
            )

        return json.dumps({"test_data": test_data_list}, indent=2)
    except Exception as e:
        return f"Error listing test data: {str(e)}"


@mcp.resource("test-data://{test_data_id}")
async def get_test_data_resource(test_data_id: str) -> str:
    """Get a specific test data as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test_data = await testzeus_client.test_data.get_one(test_data_id)
        test_data_data = {
            "id": test_data.id,
            "name": test_data.name,
            "tags": test_data.tags,
            "data_content": _mask_secret_values(test_data.data_content),
            "supporting_data_files": _format_supporting_files(test_data),
            "created": str(test_data.created),
            "updated": str(test_data.updated),
            "files_count": len(test_data.supporting_data_files or []),
            "modified_by": test_data.modified_by,
        }

        return json.dumps(test_data_data, indent=2)
    except Exception as e:
        return f"Error getting test data: {str(e)}"


@mcp.resource("tags://")
async def list_tags_resource() -> str:
    """List all tags as a browsable resource."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus tool first."

    try:
        result = await testzeus_client.tags.get_list(per_page=100)
        tags = result.get("items", [])

        tag_list = []
        for tag in tags:
            tag_list.append(
                {
                    "id": tag.id,
                    "name": tag.name,
                    "value": tag.value,
                    "uri": f"tag://{tag.id}",
                }
            )

        return json.dumps({"tags": tag_list}, indent=2)
    except Exception as e:
        return f"Error listing tags: {str(e)}"


@mcp.resource("tag://{tag_id}")
async def get_tag_resource(tag_id: str) -> str:
    """Get a specific tag as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        tag = await testzeus_client.tags.get_one(tag_id)
        tag_data = {
            "id": tag.id,
            "name": tag.name,
            "value": tag.value,
            "created": str(tag.created),
            "updated": str(tag.updated),
            "tenant": tag.tenant,
            "modified_by": tag.modified_by,
        }

        return json.dumps(tag_data, indent=2)
    except Exception as e:
        return f"Error getting tag: {str(e)}"


@mcp.resource("test-run-groups://")
async def list_test_run_groups_resource() -> str:
    """List all test run groups as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.test_run_groups.get_list(per_page=100)
        test_run_groups = result.get("items", [])

        group_list = []
        for group in test_run_groups:
            group_list.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "status": group.status,
                    "ctrf_status": getattr(group, "ctrf_status", None),
                    "execution_mode": group.execution_mode,
                    "test_count": len(getattr(group, "test_ids", [])),
                    "uri": f"test-run-group://{group.id}",
                }
            )

        return json.dumps({"test_run_groups": group_list}, indent=2)
    except Exception as e:
        return f"Error listing test run groups: {str(e)}"


@mcp.resource("test-run-group://{test_run_group_id}")
async def get_test_run_group_resource(test_run_group_id: str) -> str:
    """Get a specific test run group as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        group = await testzeus_client.test_run_groups.get_one(test_run_group_id)
        group_data = {
            "id": group.id,
            "name": group.name,
            "status": group.status,
            "ctrf_status": getattr(group, "ctrf_status", None),
            "execution_mode": group.execution_mode,
            "test_ids": getattr(group, "test_ids", []),
            "tags": getattr(group, "tags", []),
            "environment": getattr(group, "environment", None),
            "notification_channels": getattr(group, "notification_channels", []),
            "test_report_run": getattr(group, "test_report_run", None),
            "created": str(group.created),
            "updated": str(group.updated),
            "created_by": getattr(group, "created_by", None),
        }

        return json.dumps(group_data, indent=2)
    except Exception as e:
        return f"Error getting test run group: {str(e)}"


@mcp.resource("hypermind-code-blocks://")
async def list_hypermind_code_blocks_resource() -> str:
    """List all hypermind code blocks as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.hypermind_code_blocks.get_list(per_page=100)
        code_blocks = result.get("items", [])

        block_list = []
        for block in code_blocks:
            block_list.append(
                {
                    "id": block.id,
                    "name": block.name,
                    "status": block.status,
                    "tags": block.tags,
                    "files_count": len(block.code_files),
                    "uri": f"hypermind-code-block://{block.id}",
                }
            )

        return json.dumps({"hypermind_code_blocks": block_list}, indent=2)
    except Exception as e:
        return f"Error listing hypermind code blocks: {str(e)}"


@mcp.resource("hypermind-code-block://{code_block_id}")
async def get_hypermind_code_block_resource(code_block_id: str) -> str:
    """Get a specific hypermind code block as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        block = await testzeus_client.hypermind_code_blocks.get_one(code_block_id)
        block_data = {
            "id": block.id,
            "name": block.name,
            "status": block.status,
            "tags": block.tags,
            "code_files": block.code_files,
            "created": str(block.created),
            "updated": str(block.updated),
            "modified_by": block.modified_by,
        }

        return json.dumps(block_data, indent=2)
    except Exception as e:
        return f"Error getting hypermind code block: {str(e)}"


@mcp.resource("user-integrations://")
async def list_user_integrations_resource() -> str:
    """List all user integrations as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.user_integrations.get_list(per_page=100)
        integrations = result.get("items", [])

        integration_list = []
        for integration in integrations:
            integration_list.append(
                {
                    "id": integration.id,
                    "name": integration.name,
                    "integration_type": getattr(integration, "integration_type", None),
                    "connection_status": getattr(integration, "connection_status", None),
                    "uri": f"user-integration://{integration.id}",
                }
            )

        return json.dumps({"user_integrations": integration_list}, indent=2)
    except Exception as e:
        return f"Error listing user integrations: {str(e)}"


@mcp.resource("user-integration://{integration_id}")
async def get_user_integration_resource(integration_id: str) -> str:
    """Get a specific user integration as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        integration = await testzeus_client.user_integrations.get_one(integration_id)
        integration_data = {
            "id": integration.id,
            "name": integration.name,
            "integration_type": getattr(integration, "integration_type", None),
            "connection_status": getattr(integration, "connection_status", None),
            "project_id": getattr(integration, "project_id", None),
            "auth_config_id": getattr(integration, "auth_config_id", None),
            "connected_account_id": getattr(integration, "connected_account_id", None),
            "scopes": getattr(integration, "scopes", None),
            "created": str(integration.created),
            "updated": str(integration.updated),
        }

        return json.dumps(integration_data, indent=2)
    except Exception as e:
        return f"Error getting user integration: {str(e)}"


@mcp.resource("connected-environments://")
async def list_connected_environments_resource() -> str:
    """List all connected environments as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        result = await testzeus_client.connected_environments.get_list(per_page=100)
        connected_envs = result.get("items", [])

        env_list = []
        for env in connected_envs:
            env_list.append(
                {
                    "id": env.id,
                    "name": env.name,
                    "connection": getattr(env, "connection", None),
                    "tags": env.tags,
                    "uri": f"connected-environment://{env.id}",
                }
            )

        return json.dumps({"connected_environments": env_list}, indent=2)
    except Exception as e:
        return f"Error listing connected environments: {str(e)}"


@mcp.resource("connected-environment://{connected_env_id}")
async def get_connected_environment_resource(connected_env_id: str) -> str:
    """Get a specific connected environment as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.connected_environments.get_one(connected_env_id)
        env_data = {
            "id": env.id,
            "name": env.name,
            "connection": getattr(env, "connection", None),
            "created": str(env.created),
            "updated": str(env.updated),
            "modified_by": env.modified_by,
        }

        return json.dumps(env_data, indent=2)
    except Exception as e:
        return f"Error getting connected environment: {str(e)}"


# ============================================================================
# TEST REPORT SCHEDULE OPERATIONS
# ============================================================================


@mcp.tool()
async def list_test_report_schedules(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test report schedules in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.test_report_schedules.get_list(**params)
        schedules = result.get("items", [])

        schedule_list = []
        for schedule in schedules:
            schedule_list.append(
                {
                    "id": schedule.id,
                    "name": schedule.name,
                    "is_active": getattr(schedule, "is_active", False),
                    "cron_expression": getattr(schedule, "cron_expression", None),
                    "filter_name_pattern": getattr(schedule, "filter_name_pattern", None),
                    "filter_time_intervals": getattr(schedule, "filter_time_intervals", None),
                    "filter_tags": getattr(schedule, "filter_tags", []),
                    "filter_tag_pattern": getattr(schedule, "filter_tag_pattern", None),
                    "filter_env": getattr(schedule, "filter_env", []),
                    "filter_env_pattern": getattr(schedule, "filter_env_pattern", None),
                    "filter_test_data": getattr(schedule, "filter_test_data", []),
                    "filter_test_data_pattern": getattr(schedule, "filter_test_data_pattern", None),
                    "notification_channels": getattr(schedule, "notification_channels", []),
                    "created": str(schedule.created),
                    "updated": str(schedule.updated),
                }
            )

        if ctx:
            await ctx.info(f"Retrieved {len(schedule_list)} test report schedules")

        return json.dumps(
            {
                "test_report_schedules": schedule_list,
                "page": page,
                "per_page": per_page,
                "total": result.get("totalItems", len(schedule_list)),
            },
            indent=2,
            cls=DateTimeEncoder,
        )
    except Exception as e:
        error_msg = f"Error listing test report schedules: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_report_schedule(schedule_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test report schedule by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        schedule = await testzeus_client.test_report_schedules.get_one(schedule_id_or_name)
        schedule_data = {
            "id": schedule.id,
            "name": schedule.name,
            "is_active": getattr(schedule, "is_active", False),
            "filter_name_pattern": getattr(schedule, "filter_name_pattern", None),
            "filter_time_intervals": getattr(schedule, "filter_time_intervals", None),
            "cron_expression": getattr(schedule, "cron_expression", None),
            "filter_tags": getattr(schedule, "filter_tags", []),
            "filter_tag_pattern": getattr(schedule, "filter_tag_pattern", None),
            "filter_env": getattr(schedule, "filter_env", []),
            "filter_env_pattern": getattr(schedule, "filter_env_pattern", None),
            "filter_test_data": getattr(schedule, "filter_test_data", []),
            "filter_test_data_pattern": getattr(schedule, "filter_test_data_pattern", None),
            "notification_channels": getattr(schedule, "notification_channels", []),
            "created": str(schedule.created),
            "updated": str(schedule.updated),
            "tenant": schedule.tenant,
            "created_by": getattr(schedule, "created_by", None),
        }

        if ctx:
            await ctx.info(f"Retrieved test report schedule: {schedule.name}")

        return json.dumps(schedule_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error getting test report schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_report_schedule(
    name: str,
    is_active: bool = True,
    filter_name_pattern: str | None = None,
    filter_time_intervals: dict[str, str] | None = None,
    cron_expression: str | None = None,
    filter_tags: list[str] | None = None,
    filter_tag_pattern: str | None = None,
    filter_env: list[str] | None = None,
    filter_env_pattern: str | None = None,
    filter_test_data: list[str] | None = None,
    filter_test_data_pattern: str | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """
    Create a new test report schedule.

    Args:
        name: Name of the test report schedule
        is_active: Set as active test report schedule (default: True)
        filter_name_pattern: Filter using TestRun name pattern
        filter_time_intervals: Filter using time intervals (mutually exclusive with cron_expression)
            example: {"start_time": "2025-01-01 00:00:00", "end_time": "2025-01-01 01:00:00"}
        cron_expression: Cron expression (mutually exclusive with filter_time_intervals)
        filter_tags: Filter using tag names (mutually exclusive with filter_tag_pattern)
        filter_tag_pattern: Filter using tag pattern (mutually exclusive with filter_tags)
        filter_env: Filter using environment names (mutually exclusive with
            filter_env_pattern)
        filter_env_pattern: Filter using environment pattern (mutually exclusive
            with filter_env)
        filter_test_data: Filter using test data names (mutually exclusive with
            filter_test_data_pattern)
        filter_test_data_pattern: Filter test data pattern (mutually exclusive
            with filter_test_data)
        notification_channels: List of notification channel names

    Returns:
        JSON string with created schedule details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        schedule = await testzeus_client.test_report_schedules.create_test_report_schedule(
            name=name,
            is_active=is_active,
            filter_name_pattern=filter_name_pattern,
            filter_time_intervals=filter_time_intervals,
            cron_expression=cron_expression,
            filter_tags=filter_tags,
            filter_tag_pattern=filter_tag_pattern,
            filter_env=filter_env,
            filter_env_pattern=filter_env_pattern,
            filter_test_data=filter_test_data,
            filter_test_data_pattern=filter_test_data_pattern,
            notification_channels=notification_channels,
        )

        schedule_data = {
            "id": schedule.id,
            "name": schedule.name,
            "is_active": getattr(schedule, "is_active", False),
            "created": str(schedule.created),
        }

        if ctx:
            await ctx.info(f"Created test report schedule: {schedule.name}")

        return json.dumps(schedule_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error creating test report schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test_report_schedule(
    schedule_id_or_name: str,
    name: str | None = None,
    is_active: bool | None = None,
    filter_name_pattern: str | None = None,
    filter_time_intervals: dict[str, str] | None = None,
    cron_expression: str | None = None,
    filter_tags: list[str] | None = None,
    filter_tag_pattern: str | None = None,
    filter_env: list[str] | None = None,
    filter_env_pattern: str | None = None,
    filter_test_data: list[str] | None = None,
    filter_test_data_pattern: str | None = None,
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """
    Update an existing test report schedule.

    Args:
        schedule_id_or_name: ID or name of the test report schedule to update
        name: New name for the schedule
        is_active: Set as active/inactive
        filter_name_pattern: Filter using TestRun name pattern
        filter_time_intervals: Filter using time intervals (mutually exclusive with cron_expression)
        cron_expression: Cron expression (mutually exclusive with filter_time_intervals)
        filter_tags: Filter using tag names (mutually exclusive with filter_tag_pattern)
        filter_tag_pattern: Filter using tag pattern (mutually exclusive with filter_tags)
        filter_env: Filter using environment names (mutually exclusive with
            filter_env_pattern)
        filter_env_pattern: Filter using environment pattern (mutually exclusive
            with filter_env)
        filter_test_data: Filter using test data names (mutually exclusive with
            filter_test_data_pattern)
        filter_test_data_pattern: Filter test data pattern (mutually exclusive
            with filter_test_data)
        notification_channels: List of notification channel names

    Returns:
        JSON string with updated schedule details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        schedule = await testzeus_client.test_report_schedules.update_test_report_schedule(
            id_or_name=schedule_id_or_name,
            name=name,
            is_active=is_active,
            filter_name_pattern=filter_name_pattern,
            filter_time_intervals=filter_time_intervals,
            cron_expression=cron_expression,
            filter_tags=filter_tags,
            filter_tag_pattern=filter_tag_pattern,
            filter_env=filter_env,
            filter_env_pattern=filter_env_pattern,
            filter_test_data=filter_test_data,
            filter_test_data_pattern=filter_test_data_pattern,
            notification_channels=notification_channels,
        )

        schedule_data = {
            "id": schedule.id,
            "name": schedule.name,
            "is_active": getattr(schedule, "is_active", False),
            "updated": str(schedule.updated),
        }

        if ctx:
            await ctx.info(f"Updated test report schedule: {schedule.name}")

        return json.dumps(schedule_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error updating test report schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_report_schedule(schedule_id_or_name: str, ctx: Context = None) -> str:
    """Delete a test report schedule (sets status to deleted)."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        await testzeus_client.test_report_schedules.delete(schedule_id_or_name)

        if ctx:
            await ctx.info(f"Deleted test report schedule: {schedule_id_or_name}")

        return json.dumps(
            {"message": f"Test report schedule {schedule_id_or_name} deleted successfully"},
            indent=2,
        )
    except Exception as e:
        error_msg = f"Error deleting test report schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# TEST REPORT RUN OPERATIONS
# ============================================================================


@mcp.tool()
async def list_test_report_runs(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all test report runs in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.test_report_runs.get_list(**params)
        reports = result.get("items", [])

        report_list = []
        for report in reports:
            report_list.append(
                {
                    "id": report.id,
                    "name": report.display_name,
                    "status": report.status,
                    "end_time": str(getattr(report, "end_time", None)),
                    "ctrf_report_findings": getattr(report, "ctrf_report_findings", None),
                    "created": str(report.created),
                    "updated": str(report.updated),
                }
            )

        if ctx:
            await ctx.info(f"Retrieved {len(report_list)} test report runs")

        return json.dumps(
            {
                "test_report_runs": report_list,
                "page": page,
                "per_page": per_page,
                "total": result.get("totalItems", len(report_list)),
            },
            indent=2,
            cls=DateTimeEncoder,
        )
    except Exception as e:
        error_msg = f"Error listing test report runs: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_test_report_run(report_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test report run by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        report = await testzeus_client.test_report_runs.get_one(report_id_or_name)
        report_data = {
            "id": report.id,
            "name": report.name,
            "status": report.status,
            "schedule": getattr(report, "schedule", None),
            "test_run_group": getattr(report, "test_run_group", None),
            "end_time": str(getattr(report, "end_time", None)),
            "ctrf_report": getattr(report, "ctrf_report", None),
            "pdf_report": getattr(report, "pdf_report", None),
            "csv_report": getattr(report, "csv_report", None),
            "zip_report": getattr(report, "zip_report", None),
            "ctrf_report_findings": getattr(report, "ctrf_report_findings", None),
            "test_runs": getattr(report, "test_runs", []),
            "created": str(report.created),
            "updated": str(report.updated),
            "tenant": report.tenant,
            "modified_by": getattr(report, "modified_by", None),
        }

        if ctx:
            await ctx.info(f"Retrieved test report run: {report.name}")

        return json.dumps(report_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error getting test report run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_report_run(report_id_or_name: str, ctx: Context = None) -> str:
    """Delete a test report run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        await testzeus_client.test_report_runs.delete(report_id_or_name)

        if ctx:
            await ctx.info(f"Deleted test report run: {report_id_or_name}")

        return json.dumps(
            {"message": f"Test report run {report_id_or_name} deleted successfully"},
            indent=2,
        )
    except Exception as e:
        error_msg = f"Error deleting test report run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def download_test_report(
    report_id_or_name: str,
    output_dir: str = "downloads",
    format: str = "ctrf",
    ctx: Context = None,
) -> str:
    """
    Download a test report file.

    Args:
        report_id_or_name: ID or name of the test report run
        output_dir: Directory to save the downloaded file (default: "downloads")
        format: Report format to download ("ctrf", "pdf", "csv", or "zip")

    Returns:
        JSON string with download details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    if format not in ["ctrf", "pdf", "csv", "zip"]:
        error_msg = "format must be one of: 'ctrf', 'pdf', 'csv', 'zip'"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        file_path = await testzeus_client.test_report_runs.download_report(
            id_or_name=report_id_or_name,
            output_dir=output_dir,
            format=format,
        )

        if file_path is None:
            error_msg = (
                f"Test report run {report_id_or_name} is not completed or report not available"
            )
            if ctx:
                await ctx.error(error_msg)
            return error_msg

        download_data = {
            "report_id": report_id_or_name,
            "format": format,
            "file_path": str(file_path),
            "output_dir": output_dir,
            "message": f"Successfully downloaded {format} report to {file_path}",
        }

        if ctx:
            await ctx.info(f"Downloaded {format} report for {report_id_or_name} to {file_path}")

        return json.dumps(download_data, indent=2)
    except Exception as e:
        error_msg = f"Error downloading test report: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# TEST REPORT RUN RESOURCES
# ============================================================================


@mcp.resource("test-report-runs://list")
async def list_test_report_runs_resource() -> str:
    """List all test report runs as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        result = await testzeus_client.test_report_runs.get_list(per_page=100)
        reports = result.get("items", [])

        report_list = []
        for report in reports:
            report_list.append(
                {
                    "id": report.id,
                    "name": report.name,
                    "status": report.status,
                    "trigger_time": str(getattr(report, "trigger_time", None)),
                    "end_time": str(getattr(report, "end_time", None)),
                    "has_ctrf_report": bool(getattr(report, "ctrf_report", None)),
                    "has_pdf_report": bool(getattr(report, "pdf_report", None)),
                    "has_csv_report": bool(getattr(report, "csv_report", None)),
                    "has_zip_report": bool(getattr(report, "zip_report", None)),
                    "test_run_count": len(getattr(report, "test_runs", [])),
                    "uri": f"test-report-run://{report.id}",
                }
            )

        return json.dumps({"test_report_runs": report_list}, indent=2)
    except Exception as e:
        return f"Error listing test report runs: {str(e)}"


@mcp.resource("test-report-run://{report_id}")
async def get_test_report_run_resource(report_id: str) -> str:
    """Get a specific test report run as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        report = await testzeus_client.test_report_runs.get_one(report_id)
        report_data = {
            "id": report.id,
            "name": report.name,
            "display_name": getattr(report, "display_name", None),
            "status": report.status,
            "schedule": getattr(report, "schedule", None),
            "test_run_group": getattr(report, "test_run_group", None),
            "trigger_time": str(getattr(report, "trigger_time", None)),
            "end_time": str(getattr(report, "end_time", None)),
            "ctrf_report": getattr(report, "ctrf_report", None),
            "pdf_report": getattr(report, "pdf_report", None),
            "csv_report": getattr(report, "csv_report", None),
            "zip_report": getattr(report, "zip_report", None),
            "ctrf_report_findings": getattr(report, "ctrf_report_findings", None),
            "test_runs": getattr(report, "test_runs", []),
            "created": str(report.created),
            "updated": str(report.updated),
            "tenant": report.tenant,
            "modified_by": getattr(report, "modified_by", None),
        }

        return json.dumps(report_data, indent=2)
    except Exception as e:
        return f"Error getting test report run: {str(e)}"


# ============================================================================
# NOTIFICATION CHANNEL OPERATIONS
# ============================================================================


@mcp.tool()
async def list_notification_channels(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all notification channels in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.notification_channels.get_list(**params)
        channels = result.get("items", [])

        channel_list = []
        for channel in channels:
            channel_list.append(
                {
                    "id": channel.id,
                    "name": getattr(channel, "name", None),
                    "display_name": getattr(channel, "display_name", None),
                    "is_active": getattr(channel, "is_active", False),
                    "is_default": getattr(channel, "is_default", False),
                    "emails": getattr(channel, "emails", {}),
                    "webhooks": getattr(channel, "webhooks", {}),
                    "created": str(channel.created),
                    "updated": str(channel.updated),
                }
            )

        if ctx:
            await ctx.info(f"Retrieved {len(channel_list)} notification channels")

        return json.dumps(
            {
                "notification_channels": channel_list,
                "page": page,
                "per_page": per_page,
                "total": result.get("totalItems", len(channel_list)),
            },
            indent=2,
            cls=DateTimeEncoder,
        )
    except Exception as e:
        error_msg = f"Error listing notification channels: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_notification_channel(channel_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific notification channel by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        channel = await testzeus_client.notification_channels.get_one(channel_id_or_name)
        channel_data = {
            "id": channel.id,
            "name": getattr(channel, "name", None),
            "display_name": getattr(channel, "display_name", None),
            "is_active": getattr(channel, "is_active", False),
            "is_default": getattr(channel, "is_default", False),
            "emails": getattr(channel, "emails", {}),
            "webhooks": getattr(channel, "webhooks", {}),
            "created": str(channel.created),
            "updated": str(channel.updated),
            "modified_by": getattr(channel, "modified_by", None),
        }

        if ctx:
            await ctx.info(
                f"Retrieved notification channel: {getattr(channel, 'name', channel.id)}"
            )

        return json.dumps(channel_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error getting notification channel: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_notification_channel(
    name: str,
    emails: list[str],
    webhooks: list[str] | None = None,
    is_active: bool = True,
    is_default: bool = True,
    ctx: Context = None,
) -> str:
    """
    Create a new notification channel.

    Args:
        name: Name of the notification channel
        emails: List of email addresses (required)
        webhooks: List of webhook URLs (optional)
        is_active: Set as active notification channel (default: True)
        is_default: Set as default notification channel (default: True)

    Returns:
        JSON string with created channel details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        channel = await testzeus_client.notification_channels.create_notification_channel(
            name=f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            display_name=name,
            emails=emails,
            webhooks=webhooks,
            is_active=is_active,
            is_default=is_default,
        )

        channel_data = {
            "id": channel.id,
            "name": getattr(channel, "name", None),
            "display_name": getattr(channel, "display_name", None),
            "is_active": getattr(channel, "is_active", False),
            "is_default": getattr(channel, "is_default", False),
            "created": str(channel.created),
        }

        if ctx:
            await ctx.info(f"Created notification channel: {getattr(channel, 'name', channel.id)}")

        return json.dumps(channel_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error creating notification channel: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_notification_channel(
    channel_id_or_name: str,
    name: str | None = None,
    emails: list[str] | None = None,
    webhooks: list[str] | None = None,
    is_active: bool | None = None,
    is_default: bool | None = None,
    ctx: Context = None,
) -> str:
    """
    Update an existing notification channel.

    Args:
        channel_id_or_name: ID or name of the notification channel to update
        name: New name for the channel
        emails: List of email addresses
        webhooks: List of webhook URLs
        is_active: Set as active/inactive
        is_default: Set as default/non-default

    Returns:
        JSON string with updated channel details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        channel = await testzeus_client.notification_channels.update_notification_channel(
            id_or_name=channel_id_or_name,
            name=f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            display_name=name,
            emails=emails,
            webhooks=webhooks,
            is_active=is_active,
            is_default=is_default,
        )

        channel_data = {
            "id": channel.id,
            "name": getattr(channel, "name", None),
            "display_name": getattr(channel, "display_name", None),
            "is_active": getattr(channel, "is_active", False),
            "is_default": getattr(channel, "is_default", False),
            "updated": str(channel.updated),
        }

        if ctx:
            await ctx.info(f"Updated notification channel: {getattr(channel, 'name', channel.id)}")

        return json.dumps(channel_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error updating notification channel: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_notification_channel(channel_id_or_name: str, ctx: Context = None) -> str:
    """Delete a notification channel."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        await testzeus_client.notification_channels.delete(channel_id_or_name)

        if ctx:
            await ctx.info(f"Deleted notification channel: {channel_id_or_name}")

        return json.dumps(
            {"message": f"Notification channel {channel_id_or_name} deleted successfully"},
            indent=2,
        )
    except Exception as e:
        error_msg = f"Error deleting notification channel: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_notification_config(
    channel_id_or_name: str,
    config_type: str,
    ctx: Context = None,
) -> str:
    """
    Remove a configuration from a notification channel.

    Args:
        channel_id_or_name: ID or name of the notification channel
        config_type: Type of configuration to remove ('webhook' or 'slack')

    Returns:
        JSON string with updated channel details
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        error_msg = "Authentication failed - unable to connect to TestZeus"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    if config_type not in ["webhook", "slack"]:
        error_msg = "config_type must be one of: 'webhook', 'slack'"
        if ctx:
            await ctx.error(error_msg)
        return error_msg

    try:
        channel = await testzeus_client.notification_channels.remove_config(
            id_or_name=channel_id_or_name,
            config_type=config_type,
        )

        channel_data = {
            "id": channel.id,
            "name": getattr(channel, "name", None),
            "message": f"Removed {config_type} configuration",
            "updated": str(channel.updated),
        }

        if ctx:
            await ctx.info(
                f"Removed {config_type} config from notification channel: "
                f"{getattr(channel, 'name', channel.id)}"
            )

        return json.dumps(channel_data, indent=2, cls=DateTimeEncoder)
    except Exception as e:
        error_msg = f"Error removing {config_type} config: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ============================================================================
# NOTIFICATION CHANNEL RESOURCES
# ============================================================================


@mcp.resource("notification-channels://list")
async def list_notification_channels_resource() -> str:
    """List all notification channels as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        result = await testzeus_client.notification_channels.get_list(per_page=100)
        channels = result.get("items", [])

        channel_list = []
        for channel in channels:
            channel_list.append(
                {
                    "id": channel.id,
                    "name": getattr(channel, "name", None),
                    "display_name": getattr(channel, "display_name", None),
                    "is_active": getattr(channel, "is_active", False),
                    "is_default": getattr(channel, "is_default", False),
                    "has_emails": bool(getattr(channel, "emails", {})),
                    "has_webhooks": bool(getattr(channel, "webhooks", {})),
                    "uri": f"notification-channel://{channel.id}",
                }
            )

        return json.dumps({"notification_channels": channel_list}, indent=2)
    except Exception as e:
        return f"Error listing notification channels: {str(e)}"


@mcp.resource("notification-channel://{channel_id}")
async def get_notification_channel_resource(channel_id: str) -> str:
    """Get a specific notification channel as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        channel = await testzeus_client.notification_channels.get_one(channel_id)
        channel_data = {
            "id": channel.id,
            "name": getattr(channel, "name", None),
            "display_name": getattr(channel, "display_name", None),
            "is_active": getattr(channel, "is_active", False),
            "is_default": getattr(channel, "is_default", False),
            "emails": getattr(channel, "emails", {}),
            "webhooks": getattr(channel, "webhooks", {}),
            "created": str(channel.created),
            "updated": str(channel.updated),
            "modified_by": getattr(channel, "modified_by", None),
        }

        return json.dumps(channel_data, indent=2)
    except Exception as e:
        return f"Error getting notification channel: {str(e)}"


# ============================================================================
# TEST REPORT SCHEDULE RESOURCES
# ============================================================================


@mcp.resource("test-report-schedules://list")
async def list_test_report_schedules_resource() -> str:
    """List all test report schedules as a browsable resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        result = await testzeus_client.test_report_schedules.get_list(per_page=100)
        schedules = result.get("items", [])

        schedule_list = []
        for schedule in schedules:
            schedule_list.append(
                {
                    "id": schedule.id,
                    "name": schedule.name,
                    "is_active": getattr(schedule, "is_active", False),
                    "cron_expression": getattr(schedule, "cron_expression", None),
                    "filter_tags": getattr(schedule, "filter_tags", []),
                    "filter_tag_pattern": getattr(schedule, "filter_tag_pattern", None),
                    "filter_env": getattr(schedule, "filter_env", []),
                    "filter_env_pattern": getattr(schedule, "filter_env_pattern", None),
                    "filter_test_data": getattr(schedule, "filter_test_data", []),
                    "filter_test_data_pattern": getattr(schedule, "filter_test_data_pattern", None),
                    "notification_channels": getattr(schedule, "notification_channels", []),
                    "uri": f"test-report-schedule://{schedule.id}",
                }
            )

        return json.dumps({"test_report_schedules": schedule_list}, indent=2)
    except Exception as e:
        return f"Error listing test report schedules: {str(e)}"


@mcp.resource("test-report-schedule://{schedule_id}")
async def get_test_report_schedule_resource(schedule_id: str) -> str:
    """Get a specific test report schedule as a resource."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    # Check if authentication was successful
    if testzeus_client is None:
        return json.dumps({"error": "Authentication failed - unable to connect to TestZeus"})

    try:
        schedule = await testzeus_client.test_report_schedules.get_one(schedule_id)
        schedule_data = {
            "id": schedule.id,
            "name": schedule.name,
            "is_active": getattr(schedule, "is_active", False),
            "filter_name_pattern": getattr(schedule, "filter_name_pattern", None),
            "filter_time_intervals": getattr(schedule, "filter_time_intervals", None),
            "cron_expression": getattr(schedule, "cron_expression", None),
            "filter_tags": getattr(schedule, "filter_tags", []),
            "filter_tag_pattern": getattr(schedule, "filter_tag_pattern", None),
            "filter_env": getattr(schedule, "filter_env", []),
            "filter_env_pattern": getattr(schedule, "filter_env_pattern", None),
            "filter_test_data": getattr(schedule, "filter_test_data", []),
            "filter_test_data_pattern": getattr(schedule, "filter_test_data_pattern", None),
            "notification_channels": getattr(schedule, "notification_channels", []),
            "created": str(schedule.created),
            "updated": str(schedule.updated),
            "created_by": getattr(schedule, "created_by", None),
        }

        return json.dumps(schedule_data, indent=2)
    except Exception as e:
        return f"Error getting test report schedule: {str(e)}"


# =====================================================================
# SDK-parity tools: knowledge bases, extensions, AI generator, suite
# schedules, suite node run (get), connected-environment file ops.
# =====================================================================


# ----------------------------- Knowledge bases -----------------------------


@mcp.tool()
async def list_knowledge_bases(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all knowledge bases in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.knowledge_bases.get_list(**params)
        items = result.get("items", [])
        kb_list = [
            {
                "id": kb.id,
                "name": getattr(kb, "name", None),
                "source": getattr(kb, "source", None),
                "description": getattr(kb, "description", None),
                "status": getattr(kb, "status", None),
            }
            for kb in items
        ]
        if ctx:
            await ctx.info(f"Found {len(kb_list)} knowledge bases")
        return f"Found {len(kb_list)} knowledge bases:\n{json.dumps(kb_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing knowledge bases: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_knowledge_base(knowledge_base_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific knowledge base by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        kb = await testzeus_client.knowledge_bases.get_one(knowledge_base_id_or_name)
        kb_data = {
            "id": kb.id,
            "name": getattr(kb, "name", None),
            "source": getattr(kb, "source", None),
            "description": getattr(kb, "description", None),
            "status": getattr(kb, "status", None),
            "tenant": getattr(kb, "tenant", None),
            "modified_by": getattr(kb, "modified_by", None),
            "created": str(getattr(kb, "created", None)),
            "updated": str(getattr(kb, "updated", None)),
        }
        if ctx:
            await ctx.info(f"Retrieved knowledge base: {kb_data['name']}")
        return f"Knowledge base details:\n{json.dumps(kb_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting knowledge base: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_knowledge_base(
    name: str,
    source: str | None = None,
    description: str | None = None,
    status: Literal["draft", "ready", "deleted"] = "draft",
    ctx: Context = None,
) -> str:
    """Create a new knowledge base."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {"name": name, "status": status}
        if source is not None:
            data["source"] = source
        if description is not None:
            data["description"] = description
        kb = await testzeus_client.knowledge_bases.create(data)
        if ctx:
            await ctx.info(f"Created knowledge base: {name}")
        return f"Successfully created knowledge base '{name}' with ID: {kb.id}"
    except Exception as e:
        error_msg = f"Error creating knowledge base: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_knowledge_base(
    knowledge_base_id: str,
    name: str | None = None,
    source: str | None = None,
    description: str | None = None,
    status: Literal["draft", "ready", "deleted"] | None = None,
    ctx: Context = None,
) -> str:
    """Update a knowledge base."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if source is not None:
            data["source"] = source
        if description is not None:
            data["description"] = description
        if status:
            data["status"] = status
        await testzeus_client.knowledge_bases.update(knowledge_base_id, data)
        if ctx:
            await ctx.info(f"Updated knowledge base: {knowledge_base_id}")
        return f"Successfully updated knowledge base with ID: {knowledge_base_id}"
    except Exception as e:
        error_msg = f"Error updating knowledge base: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_knowledge_base(knowledge_base_id: str, ctx: Context = None) -> str:
    """Delete a knowledge base."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        await testzeus_client.knowledge_bases.delete(knowledge_base_id)
        if ctx:
            await ctx.info(f"Deleted knowledge base: {knowledge_base_id}")
        return f"Successfully deleted knowledge base with ID: {knowledge_base_id}"
    except Exception as e:
        error_msg = f"Error deleting knowledge base: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ------------------------------- Extensions --------------------------------


@mcp.tool()
async def list_extensions(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
    filters: dict[str, Any] | None = None,
    sort: str | list[str] | None = None,
) -> str:
    """List all extensions in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        params = {"page": page, "per_page": min(per_page, 100)}
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        result = await testzeus_client.extensions.get_list(**params)
        items = result.get("items", [])
        ext_list = [
            {
                "id": ext.id,
                "name": getattr(ext, "name", None),
                "data_content": getattr(ext, "data_content", None),
                "response": getattr(ext, "response", None),
                "submit": getattr(ext, "submit", None),
            }
            for ext in items
        ]
        if ctx:
            await ctx.info(f"Found {len(ext_list)} extensions")
        return f"Found {len(ext_list)} extensions:\n{json.dumps(ext_list, indent=2)}"
    except Exception as e:
        error_msg = f"Error listing extensions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_extension(extension_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific extension by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        ext = await testzeus_client.extensions.get_one(extension_id_or_name)
        ext_data = {
            "id": ext.id,
            "name": getattr(ext, "name", None),
            "data_content": getattr(ext, "data_content", None),
            "response": getattr(ext, "response", None),
            "metadata": getattr(ext, "metadata", None),
            "submit": getattr(ext, "submit", None),
            "tenant": getattr(ext, "tenant", None),
            "modified_by": getattr(ext, "modified_by", None),
            "created": str(getattr(ext, "created", None)),
            "updated": str(getattr(ext, "updated", None)),
        }
        if ctx:
            await ctx.info(f"Retrieved extension: {ext_data['name']}")
        return f"Extension details:\n{json.dumps(ext_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting extension: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_extension(
    name: str,
    data_content: str | None = None,
    submit: bool = False,
    metadata: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new extension."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {"name": name, "submit": submit}
        if data_content is not None:
            data["data_content"] = data_content
        if metadata is not None:
            data["metadata"] = metadata
        ext = await testzeus_client.extensions.create(data)
        if ctx:
            await ctx.info(f"Created extension: {name}")
        return f"Successfully created extension '{name}' with ID: {ext.id}"
    except Exception as e:
        error_msg = f"Error creating extension: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_extension(
    extension_id: str,
    name: str | None = None,
    data_content: str | None = None,
    submit: bool | None = None,
    metadata: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Update an extension."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if data_content is not None:
            data["data_content"] = data_content
        if submit is not None:
            data["submit"] = submit
        if metadata is not None:
            data["metadata"] = metadata
        await testzeus_client.extensions.update(extension_id, data)
        if ctx:
            await ctx.info(f"Updated extension: {extension_id}")
        return f"Successfully updated extension with ID: {extension_id}"
    except Exception as e:
        error_msg = f"Error updating extension: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_extension(extension_id: str, ctx: Context = None) -> str:
    """Delete an extension."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        await testzeus_client.extensions.delete(extension_id)
        if ctx:
            await ctx.info(f"Deleted extension: {extension_id}")
        return f"Successfully deleted extension with ID: {extension_id}"
    except Exception as e:
        error_msg = f"Error deleting extension: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ---------------------------- AI test generator ----------------------------


@mcp.tool()
async def generate_test(
    user_prompt: str,
    test_feature: str | None = None,
    environment: str | None = None,
    test_data: list[str] | None = None,
    num_of_testcases: int | None = None,
    reasoning_effort: Literal["low", "medium", "high"] = "medium",
    submit: bool = True,
    ctx: Context = None,
) -> str:
    """Generate test case(s) from a natural-language prompt using the TestZeus AI generator.

    Creates a tests_ai_generator record; with submit=True the platform runs generation.
    """
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {
            "user_prompt": user_prompt,
            "reasoning_effort": reasoning_effort,
            "submit": submit,
        }
        if test_feature is not None:
            data["test_feature"] = test_feature
        if environment is not None:
            data["environment"] = environment
        if test_data is not None:
            data["test_data"] = test_data
        if num_of_testcases is not None:
            data["num_of_testcases"] = num_of_testcases
        gen = await testzeus_client.tests_ai_generator.create(data)
        if ctx:
            await ctx.info("Submitted AI test generation request")
        return f"Successfully submitted AI test generation request with ID: {gen.id}"
    except Exception as e:
        error_msg = f"Error generating test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# --------------------------- Test suite schedules --------------------------
# (list_test_suite_schedules already exists above)


@mcp.tool()
async def get_test_suite_schedule(schedule_id_or_name: str, ctx: Context = None) -> str:
    """Get a specific test suite schedule by ID or name."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        sc = await testzeus_client.test_suite_schedules.get_one(schedule_id_or_name)
        sc_data = {
            "id": sc.id,
            "name": getattr(sc, "name", None),
            "display_name": getattr(sc, "display_name", None),
            "test_suite": getattr(sc, "test_suite", None),
            "cron_expression": getattr(sc, "cron_expression", None),
            "is_active": getattr(sc, "is_active", None),
            "environment": getattr(sc, "environment", None),
            "notification_channels": getattr(sc, "notification_channels", None),
            "next_run_at": str(getattr(sc, "next_run_at", None)),
            "last_run_at": str(getattr(sc, "last_run_at", None)),
        }
        if ctx:
            await ctx.info(f"Retrieved test suite schedule: {sc_data['name']}")
        return f"Test suite schedule details:\n{json.dumps(sc_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test suite schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_suite_schedule(
    name: str,
    test_suite: str,
    cron_expression: str,
    environment: str | None = None,
    is_active: bool = True,
    notification_channels: list[str] | None = None,
    display_name: str | None = None,
    input_values: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test suite schedule (cron-based)."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {
            "name": name,
            "test_suite": test_suite,
            "cron_expression": cron_expression,
            "is_active": is_active,
        }
        if environment is not None:
            data["environment"] = environment
        if notification_channels is not None:
            data["notification_channels"] = notification_channels
        if display_name is not None:
            data["display_name"] = display_name
        if input_values is not None:
            data["input_values"] = input_values
        sc = await testzeus_client.test_suite_schedules.create(data)
        if ctx:
            await ctx.info(f"Created test suite schedule: {name}")
        return f"Successfully created test suite schedule '{name}' with ID: {sc.id}"
    except Exception as e:
        error_msg = f"Error creating test suite schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test_suite_schedule(
    schedule_id: str,
    name: str | None = None,
    test_suite: str | None = None,
    cron_expression: str | None = None,
    environment: str | None = None,
    is_active: bool | None = None,
    notification_channels: list[str] | None = None,
    display_name: str | None = None,
    input_values: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """Update a test suite schedule."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if test_suite:
            data["test_suite"] = test_suite
        if cron_expression:
            data["cron_expression"] = cron_expression
        if environment is not None:
            data["environment"] = environment
        if is_active is not None:
            data["is_active"] = is_active
        if notification_channels is not None:
            data["notification_channels"] = notification_channels
        if display_name is not None:
            data["display_name"] = display_name
        if input_values is not None:
            data["input_values"] = input_values
        await testzeus_client.test_suite_schedules.update(schedule_id, data)
        if ctx:
            await ctx.info(f"Updated test suite schedule: {schedule_id}")
        return f"Successfully updated test suite schedule with ID: {schedule_id}"
    except Exception as e:
        error_msg = f"Error updating test suite schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_suite_schedule(schedule_id: str, ctx: Context = None) -> str:
    """Delete a test suite schedule."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        await testzeus_client.test_suite_schedules.delete(schedule_id)
        if ctx:
            await ctx.info(f"Deleted test suite schedule: {schedule_id}")
        return f"Successfully deleted test suite schedule with ID: {schedule_id}"
    except Exception as e:
        error_msg = f"Error deleting test suite schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ------------------------ Test suite node runs (get) -----------------------
# (list_test_suite_node_runs already exists above)


@mcp.tool()
async def get_test_suite_node_run(node_run_id: str, ctx: Context = None) -> str:
    """Get a specific test suite node run by ID."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    try:
        nr = await testzeus_client.test_suite_node_runs.get_one(node_run_id)
        nr_data = {
            "id": nr.id,
            "test_suite_run": getattr(nr, "test_suite_run", None),
            "node_id": getattr(nr, "node_id", None),
            "status": getattr(nr, "status", None),
            "test_run": getattr(nr, "test_run", None),
            "retry_count": getattr(nr, "retry_count", None),
            "max_retries": getattr(nr, "max_retries", None),
            "started_at": str(getattr(nr, "started_at", None)),
            "completed_at": str(getattr(nr, "completed_at", None)),
        }
        if ctx:
            await ctx.info(f"Retrieved test suite node run: {node_run_id}")
        return f"Test suite node run details:\n{json.dumps(nr_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test suite node run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# ---------------------- Connected-environment file ops ---------------------
# (create/get/list/update/delete_connected_environment already exist above)


@mcp.tool()
async def add_connected_environment_code_file(
    connected_environment_id: str, file_path: str, ctx: Context = None
) -> str:
    """Add a code file to a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.add_code_file(cid, file_path)
        if ctx:
            await ctx.info(f"Added code file to connected environment: {cid}")
        return f"Successfully added code file to connected environment {cid}"
    except Exception as e:
        error_msg = f"Error adding connected environment code file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_connected_environment_code_file(
    connected_environment_id: str, file_name: str, ctx: Context = None
) -> str:
    """Remove a code file from a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.remove_code_file(cid, file_name)
        if ctx:
            await ctx.info(f"Removed code file from connected environment: {cid}")
        return f"Successfully removed code file from connected environment {cid}"
    except Exception as e:
        error_msg = f"Error removing connected environment code file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_all_connected_environment_code_files(
    connected_environment_id: str, ctx: Context = None
) -> str:
    """Remove all code files from a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.remove_all_code_files(cid)
        if ctx:
            await ctx.info(f"Removed all code files from connected environment: {cid}")
        return f"Successfully removed all code files from connected environment {cid}"
    except Exception as e:
        error_msg = f"Error removing all connected environment code files: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def add_connected_environment_metadata_file(
    connected_environment_id: str, file_path: str, ctx: Context = None
) -> str:
    """Add a metadata file to a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.add_metadata_file(cid, file_path)
        if ctx:
            await ctx.info(f"Added metadata file to connected environment: {cid}")
        return f"Successfully added metadata file to connected environment {cid}"
    except Exception as e:
        error_msg = f"Error adding connected environment metadata file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_connected_environment_metadata_file(
    connected_environment_id: str, file_name: str, ctx: Context = None
) -> str:
    """Remove a metadata file from a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.remove_metadata_file(cid, file_name)
        if ctx:
            await ctx.info(f"Removed metadata file from connected environment: {cid}")
        return f"Successfully removed metadata file from connected environment {cid}"
    except Exception as e:
        error_msg = f"Error removing connected environment metadata file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def remove_all_connected_environment_metadata_files(
    connected_environment_id: str, ctx: Context = None
) -> str:
    """Remove all metadata files from a connected environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"

    cid = connected_environment_id
    try:
        await testzeus_client.connected_environments.remove_all_metadata_files(cid)
        if ctx:
            await ctx.info(f"Removed all metadata files from connected environment: {cid}")
        return f"Successfully removed all metadata files from connected environment {cid}"
    except Exception as e:
        error_msg = f"Error removing all connected environment metadata files: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# =====================================================================
# Agent Harness: adversarial testing of AI agents (Salesforce Agentforce).
# Wraps the SDK's client.agent_harness manager. Flow: list agents ->
# list/generate pathways -> run simulation -> poll status -> results.
# =====================================================================


async def _prepare_agent_harness() -> str | None:
    """Authenticate if needed and confirm the Agent Harness is usable.

    Returns an error string to hand back to the caller, or None when the client is
    authenticated and the installed SDK exposes the agent_harness manager. Captures
    authenticate_testzeus()'s return so wrong-credential failures surface clearly.
    """
    if not await ensure_authenticated():
        auth_result = await authenticate_testzeus()
        if not await ensure_authenticated():
            return auth_result
    if testzeus_client is None:
        return "Authentication failed - unable to connect to TestZeus"
    if not hasattr(testzeus_client, "agent_harness"):
        return (
            "Agent Harness requires a newer testzeus-sdk. Upgrade with: pip install -U testzeus-sdk"
        )
    return None


@mcp.tool()
async def list_adversary_agents(
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
    search: str | None = None,
    ctx: Context = None,
) -> str:
    """List agents available for adversarial (Agent Harness) testing."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.list_agents(
            page=page,
            per_page=min(per_page, 100),
            status=status,
            search=search,
        )
        items = result.get("items", []) if isinstance(result, dict) else result
        agent_list = [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "status": a.get("status"),
                "pathways_count": a.get("pathways_count"),
            }
            for a in items
        ]
        if ctx:
            await ctx.info(f"Found {len(agent_list)} agents")
        payload = json.dumps(agent_list, indent=2, cls=DateTimeEncoder)
        return f"Found {len(agent_list)} agents:\n{payload}"
    except Exception as e:
        error_msg = f"Error listing adversary agents: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_adversary_agent(agent_id: str, ctx: Context = None) -> str:
    """Get details for a single Agent Harness agent by ID."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.get_agent(agent_id)
        if ctx:
            await ctx.info(f"Retrieved agent {agent_id}")
        return f"Agent details:\n{json.dumps(result, indent=2, cls=DateTimeEncoder)}"
    except Exception as e:
        error_msg = f"Error getting adversary agent: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def list_adversary_pathways(
    agent_id: str | None = None,
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None,
) -> str:
    """List adversarial test pathways, optionally scoped to a single agent."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.list_pathways(
            agent_id=agent_id,
            page=page,
            per_page=min(per_page, 100),
        )
        items = result.get("items", []) if isinstance(result, dict) else result
        pathway_list = [
            {
                "id": getattr(p, "id", None),
                "name": getattr(p, "name", None),
                "objective": getattr(p, "objective", None),
                "risk_level": getattr(p, "risk_level", None),
                "agent_id": getattr(p, "agent_id", None),
            }
            for p in items
        ]
        if ctx:
            await ctx.info(f"Found {len(pathway_list)} pathways")
        payload = json.dumps(pathway_list, indent=2, cls=DateTimeEncoder)
        return f"Found {len(pathway_list)} pathways:\n{payload}"
    except Exception as e:
        error_msg = f"Error listing adversary pathways: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def generate_adversary_pathways(
    agent_profile: str,
    directional_prompt: str,
    name: str | None = None,
    agent_name: str | None = None,
    num_pathways: int | None = None,
    allow_destructive: bool = False,
    ctx: Context = None,
) -> str:
    """Start an AI pathway-generation job for a Salesforce agent profile."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.generate_pathways(
            agent_profile=agent_profile,
            directional_prompt=directional_prompt,
            name=name,
            agent_name=agent_name,
            num_pathways=num_pathways,
            allow_destructive=allow_destructive,
        )
        if ctx:
            await ctx.info("Started pathway generation")
        payload = json.dumps(result.data, indent=2, cls=DateTimeEncoder)
        return f"Pathway generation started:\n{payload}"
    except Exception as e:
        error_msg = f"Error generating adversary pathways: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def run_adversary_simulation(
    agent_id: str,
    pathway_ids: list[str],
    name: str | None = None,
    agent_name: str | None = None,
    run_as_profile: str | None = None,
    ctx: Context = None,
) -> str:
    """Start an adversarial simulation run (creates a pathways group)."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard
    if not pathway_ids:
        return "Error running adversary simulation: provide at least one pathway_id"

    try:
        result = await testzeus_client.agent_harness.run(
            agent_id,
            pathway_ids,
            name=name,
            agent_name=agent_name,
            run_as_profile=run_as_profile,
        )
        group_id = getattr(result, "id", None)
        if ctx:
            await ctx.info(f"Started simulation run (group {group_id})")
        payload = json.dumps(result.data, indent=2, cls=DateTimeEncoder)
        return f"Simulation run started (group {group_id}):\n{payload}"
    except Exception as e:
        error_msg = f"Error running adversary simulation: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_adversary_run_status(group_id: str, ctx: Context = None) -> str:
    """Get status and results for an adversarial simulation run group."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.get_status(group_id)
        if ctx:
            await ctx.info(f"Retrieved status for group {group_id}")
        return f"Run status:\n{json.dumps(result, indent=2, cls=DateTimeEncoder)}"
    except Exception as e:
        error_msg = f"Error getting adversary run status: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def cancel_adversary_run(group_id: str, ctx: Context = None) -> str:
    """Cancel a running adversarial simulation group."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.cancel(group_id)
        if ctx:
            await ctx.info(f"Cancelled simulation group {group_id}")
        payload = json.dumps(result, indent=2, cls=DateTimeEncoder)
        return f"Cancelled simulation group {group_id}:\n{payload}"
    except Exception as e:
        error_msg = f"Error cancelling adversary run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def get_salesforce_run_as_profiles(connection_id: str, ctx: Context = None) -> str:
    """Get Salesforce user profiles for the Run-As-User (RBAC) picker."""
    guard = await _prepare_agent_harness()
    if guard:
        return guard

    try:
        result = await testzeus_client.agent_harness.get_sf_profiles(connection_id)
        if ctx:
            await ctx.info(f"Retrieved Salesforce profiles for connection {connection_id}")
        return f"Salesforce profiles:\n{json.dumps(result, indent=2, cls=DateTimeEncoder)}"
    except Exception as e:
        error_msg = f"Error getting Salesforce run-as profiles: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Server run function for backwards compatibility
async def run():
    """Run the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    mcp.run()
