"""
TestZeus FastMCP Server - Modern MCP server implementation for TestZeus SDK.

This module provides a FastMCP-based server that exposes TestZeus SDK
functionality to MCP clients like Claude Desktop in a clean, modern way.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from testzeus_sdk.client import TestZeusClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            email=email, password=password
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
            test_data=test_data,
            tags=tags,
            environment=environment,
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
    execution_mode: Literal["lenient", "strict"] = "lenient",
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
        if execution_mode:
            data["execution_mode"] = execution_mode
        if environment:
            data["environment"] = environment
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
    test_id_or_name: str,
    execution_mode: Literal["lenient", "strict"] = "lenient",
    ctx: Context = None,
) -> str:
    """Execute a test and start a test run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    try:
        test_run = await testzeus_client.tests.run_test(
            test_id_or_name, execution_mode=execution_mode
        )

        if ctx:
            await ctx.info(f"Started test run for test: {test_id_or_name}")

        return f"Successfully started test run '{test_run.name}' with ID: {test_run.id}"
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

        return (
            f"Test run details:\n{json.dumps(details, cls=DateTimeEncoder, indent=2)}"
        )
    except Exception as e:
        error_msg = f"Error getting test run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_run(test_id: str, name: str, ctx: Context = None) -> str:
    """Create a new test run."""
    if not await ensure_authenticated():
        await authenticate_testzeus()

    if not name or not test_id:
        return "Error: Name and test_id are required to run a test."

    try:
        test_run = await testzeus_client.test_runs.create_and_start(
            name=name, test=test_id
        )

        if ctx:
            await ctx.info(f"Created test run: {test_run.name}")

        return f"Successfully created test run '{test_run.name}' with ID: {test_run.id}"
    except Exception as e:
        error_msg = f"Error creating test run: {str(e)}"
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
async def add_environment_file(
    environment_id: str, file_path: str, ctx: Context = None
) -> str:
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
async def remove_environment_file(
    environment_id: str, file_path: str, ctx: Context = None
) -> str:
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
async def add_test_data_file(
    test_data_id: str, file_path: str, ctx: Context = None
) -> str:
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
async def remove_test_data_file(
    test_data_id: str, file_path: str, ctx: Context = None
) -> str:
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
            "tenant": test.tenant,
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
            "test": run.test,
            "test_status": getattr(run, "test_status", None),
            "start_time": str(getattr(run, "start_time", None)),
            "end_time": str(getattr(run, "end_time", None)),
            "tags": getattr(run, "tags", []),
            "metadata": getattr(run, "metadata", None),
            "created": str(run.created),
            "updated": str(run.updated),
            "tenant": run.tenant,
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
            "tenant": env.tenant,
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
            "tenant": test_data.tenant,
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


# Server run function for backwards compatibility
async def run():
    """Run the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    mcp.run()
