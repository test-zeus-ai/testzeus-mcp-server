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
create_test_suite, update_test_suite, and create_test_suite_run.
Test run groups still use hardcoded 'lenient' mode for consistent behavior.
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
                    "test_feature": test.test_feature,
                    "tags": test.tags,
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
            "test_feature": test.test_feature,
            "tags": test.tags,
            "test_data": test.test_data,
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
    status: str = "draft",
    test_data: list[str] | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    test_params: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    execution_mode: Literal["lenient", "strict"] = "lenient",
    ctx: Context = None,
) -> str:
    """Create a new test in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.tests.create_test(
            name=name,
            test_feature=test_feature,
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
    status: str | None = None,
    test_data: list[str] | None = None,
    tags: list[str] | None = None,
    environment: str | None = None,
    test_params: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    execution_mode: Literal["lenient", "strict"] | None = None,
    ctx: Context = None,
) -> str:
    """Update an existing test in TestZeus."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if test_feature:
            data["test_feature"] = test_feature
        if status:
            data["status"] = status
        if test_data:
            data["test_data"] = test_data
        if tags:
            data["tags"] = tags
        if environment:
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

    try:
        result = await testzeus_client.tests.get_dependent_test_suites(test_id)

        if ctx:
            await ctx.info(f"Retrieved dependent suites for test: {test_id}")

        return f"Dependent test suites:\n{json.dumps(result, indent=2)}"
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
    execution_mode: Literal["lenient", "strict"] = "lenient",
    notification_channels: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test suite run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        if execution_mode != "lenient":
            raise ValueError(
                "Test suite runs currently support only execution_mode='lenient'."
            )

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
    """List all environments in TestZeus."""
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
            env_list.append(
                {
                    "id": env.id,
                    "name": env.name,
                    "data": env.data_content,
                    "status": env.status,
                    "tags": env.tags,
                    "supporting_data_files": env.supporting_data_files,
                    "created": str(env.created),
                    "updated": str(env.updated),
                }
            )

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
        env_data = {
            "id": env.id,
            "name": env.name,
            "data": env.data_content,
            "status": env.status,
            "tags": env.tags,
            "supporting_data_files": env.supporting_data_files,
            "created": str(env.created),
            "updated": str(env.updated),
            "tenant": env.tenant,
            "modified_by": env.modified_by,
        }

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
    data_content: str | None = None,
    status: Literal["draft", "ready", "deleted"] = "draft",
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    connected_environments: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Create a new environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        env = await testzeus_client.environments.create_environment(
            name=name,
            data=data_content,
            status=status,
            tags=tags,
            supporting_data_files=supporting_data_files,
            connected_environments=connected_environments,
        )

        if ctx:
            await ctx.info(f"Created environment: {name}")

        return f"Successfully created environment '{name}' with ID: {env.id}"
    except Exception as e:
        error_msg = f"Error creating environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_environment(
    environment_id: str,
    name: str | None = None,
    data_content: str | None = None,
    status: Literal["draft", "ready", "deleted"] | None = None,
    tags: list[str] | None = None,
    supporting_data_files: str | None = None,
    connected_environments: list[str] | None = None,
    ctx: Context = None,
) -> str:
    """Update an environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if data_content:
            data["env_data"] = data_content
        if status:
            data["status"] = status
        if tags:
            data["tags"] = tags
        if supporting_data_files:
            data["supporting_data_files"] = supporting_data_files
        if connected_environments is not None:
            data["connected_environments"] = connected_environments

        await testzeus_client.environments.update_environment(environment_id, **data)

        if ctx:
            await ctx.info(f"Updated environment: {name}")

        return f"Successfully updated environment '{name}' with ID: {environment_id}"

    except Exception as e:
        error_msg = f"Error updating environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_environment(environment_id: str, ctx: Context = None) -> str:
    """Delete an environment."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.environments.delete(environment_id)

        if ctx:
            await ctx.info(f"Deleted environment: {environment_id}")

        return f"Successfully deleted environment with ID: {environment_id}"

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
    """Remove a environment file."""
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


@mcp.tool()
async def get_test_data(test_id: str, ctx: Context = None) -> str:
    """Get the test data for a specific test."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test = await testzeus_client.test_data.get_one(test_id)
        test_data = {
            "id": test.id,
            "name": test.name,
            "status": test.status,
            "tags": test.tags,
            "created": str(test.created),
            "updated": str(test.updated),
            "tenant": test.tenant,
            "modified_by": test.modified_by,
            "data content": test.data_content,
            "type": test.type,
            "metadata": test.metadata,
            "supporting data files": test.supporting_data_files,
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
    status: Literal["draft", "ready", "deleted"] = "draft",
    content: str | None = None,
    tags: list[str] | None = None,
    type: Literal["test", "design", "run"] = "test",
    supporting_data_files: str | None = None,
    ctx: Context = None,
) -> str:
    """Create a new test data."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test_data = await testzeus_client.test_data.create_test_data(
            name=name,
            status=status,
            content=content,
            tags=tags,
            type=type,
            supporting_data_files=supporting_data_files,
        )

        if ctx:
            await ctx.info(f"Created test data: {name}")

        return f"Successfully created test data '{name}' with ID: {test_data.id}"

    except Exception as e:
        error_msg = f"Error creating test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def delete_test_data(test_data_id: str, ctx: Context = None) -> str:
    """Delete a test data."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.test_data.delete(test_data_id)

        if ctx:
            await ctx.info(f"Deleted test data: {test_data_id}")

        return f"Successfully deleted test data with ID: {test_data_id}"

    except Exception as e:
        error_msg = f"Error deleting test data: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_test_data(
    test_data_id: str,
    name: str | None = None,
    status: Literal["draft", "ready", "deleted"] | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    type: Literal["test", "design", "run"] | None = None,
    supporting_data_files: str | None = None,
    ctx: Context = None,
) -> str:
    """Update a test data."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if status:
            data["status"] = status
        if content:
            data["content"] = content
        if tags:
            data["tags"] = tags
        if type:
            data["type"] = type
        if supporting_data_files:
            data["supporting_data_files"] = supporting_data_files

        await testzeus_client.test_data.update_test_data(test_data_id, **data)

        if ctx:
            await ctx.info(f"Updated test data: {name}")

        return f"Successfully updated test data with ID: {test_data_id}"

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
    """List all test data."""
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
                    "status": test_data.status,
                    "tags": test_data.tags,
                    "type": test_data.type,
                    "data_content": test_data.data_content,
                    "supporting_data_files": test_data.supporting_data_files,
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
    """Remove a test data file."""
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
    """Create a new tag."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        _ = await testzeus_client.tags.create_tag(name=name, value=value)

        if ctx:
            await ctx.info(f"Created tag: {name}")

        return f"Successfully created tag '{name}' with value: {value}"

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
    """List all tags."""
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
    """Get a specific tag."""
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
    """Delete a tag."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        await testzeus_client.tags.delete(tag_id)

        if ctx:
            await ctx.info(f"Deleted tag: {tag_id}")

        return f"Successfully deleted tag with ID: {tag_id}"

    except Exception as e:
        error_msg = f"Error deleting tag: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def update_tag(
    tag_id: str, name: str | None = None, value: str | None = None, ctx: Context = None
) -> str:
    """Update a tag."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        data = {}
        if name:
            data["name"] = name
        if value:
            data["value"] = value

        await testzeus_client.tags.update_tag(tag_id, **data)

        if ctx:
            await ctx.info(f"Updated tag: {name}")

        return f"Successfully updated tag with ID: {tag_id}"

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
            "test_feature": test.test_feature,
            "tags": test.tags,
            "test_data": test.test_data,
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
            env_list.append(
                {
                    "id": env.id,
                    "name": env.name,
                    "status": env.status,
                    "description": env.data_content,
                    "files": len(env.supporting_data_files),
                    "uri": f"environment://{env.id}",
                }
            )

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
        env_data = {
            "id": env.id,
            "name": env.name,
            "description": env.data_content,
            "metadata": getattr(env, "metadata", None),
            "created": str(env.created),
            "updated": str(env.updated),
            "files": len(env.supporting_data_files),
            "modified_by": env.modified_by,
        }

        return json.dumps(env_data, indent=2)
    except Exception as e:
        return f"Error getting environment: {str(e)}"


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
                    "status": test_data.status,
                    "tags": test_data.tags,
                    "data content": test_data.data_content,
                    "files": len(test_data.supporting_data_files),
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
            "status": test_data.status,
            "tags": test_data.tags,
            "type": test_data.type,
            "data content": test_data.data_content,
            "supporting data files": test_data.supporting_data_files,
            "created": str(test_data.created),
            "updated": str(test_data.updated),
            "files count": len(test_data.supporting_data_files),
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


# Server run function for backwards compatibility
async def run():
    """Run the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    mcp.run()
