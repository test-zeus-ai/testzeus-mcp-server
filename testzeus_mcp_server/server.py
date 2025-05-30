"""
TestZeus FastMCP Server - Modern MCP server implementation for TestZeus SDK.

This module provides a FastMCP-based server that exposes TestZeus SDK
functionality to MCP clients like Claude Desktop in a clean, modern way.
"""

import json
import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP, Context
from testzeus_sdk.client import TestZeusClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP("TestZeus MCP Server")

# Global client instance
testzeus_client: Optional[TestZeusClient] = None


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


# Authentication
@mcp.tool()
async def authenticate_testzeus(
    email: str, 
    password: str, 
    base_url: Optional[str] = None,
    ctx: Context = None
) -> str:
    """Authenticate with TestZeus platform using email and password."""
    global testzeus_client
    
    try:
        testzeus_client = TestZeusClient(
            email=email,
            password=password,
            base_url=base_url
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
    status: Optional[str] = None,
    ctx: Context = None
) -> str:
    """List all tests in TestZeus."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
            
        result = await testzeus_client.tests.get_list(**params)
        tests = result.get("items", [])
        
        test_list = []
        for test in tests:
            test_list.append({
                "id": test.id,
                "name": test.name,
                "status": test.status,
                "test_feature": test.test_feature,
                "tags": test.tags,
                "created": str(test.created),
                "updated": str(test.updated),
            })
        
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
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
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
    test_data: Optional[list] = None,
    tags: Optional[list] = None,
    ctx: Context = None
) -> str:
    """Create a new test in TestZeus."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        test = await testzeus_client.tests.create_test(
            name=name,
            test_feature=test_feature,
            status=status,
            test_data=test_data,
            tags=tags,
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
    name: Optional[str] = None,
    test_feature: Optional[str] = None,
    status: Optional[str] = None,
    test_data: Optional[list] = None,
    tags: Optional[list] = None,
    ctx: Context = None
) -> str:
    """Update an existing test in TestZeus."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
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
            
        test = await testzeus_client.tests.update(test_id_or_name, data)
        
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
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        test = await testzeus_client.tests.update(test_id_or_name, {"status": "deleted"})
        
        if ctx:
            await ctx.info(f"Deleted test: {test.name}")
            
        return f"Successfully deleted test '{test.name}' (ID: {test.id})"
    except Exception as e:
        error_msg = f"Error deleting test: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def run_test(test_id_or_name: str, ctx: Context = None) -> str:
    """Execute a test and start a test run."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        test_run = await testzeus_client.tests.run_test(test_id_or_name)
        
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
    test_id: Optional[str] = None,
    status: Optional[str] = None,
    ctx: Context = None
) -> str:
    """List all test runs in TestZeus."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        per_page = min(per_page, 100)  # Cap at 100
        params = {"page": page, "per_page": per_page}
        if test_id:
            params["test_id"] = test_id
        if status:
            params["status"] = status
            
        result = await testzeus_client.test_runs.get_list(**params)
        test_runs = result.get("items", [])
        
        run_list = []
        for run in test_runs:
            run_list.append({
                "id": run.id,
                "name": run.name,
                "status": run.status,
                "test": run.test,
                "start_time": str(getattr(run, "start_time", None)),
                "end_time": str(getattr(run, "end_time", None)),
                "created": str(run.created),
                "updated": str(run.updated),
            })
        
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
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
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
            "workflow_run_id": getattr(run, "workflow_run_id", None),
            "tags": getattr(run, "tags", []),
            "metadata": getattr(run, "metadata", None),
            "created": str(run.created),
            "updated": str(run.updated),
            "tenant": run.tenant,
            "modified_by": run.modified_by,
        }
        
        if ctx:
            await ctx.info(f"Retrieved test run: {run.name}")
            
        return f"Test run details:\n{json.dumps(run_data, indent=2)}"
    except Exception as e:
        error_msg = f"Error getting test run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def create_test_run(
    test_id: str,
    name: Optional[str] = None,
    environment: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    ctx: Context = None
) -> str:
    """Create a new test run."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        data = {"test": test_id}
        if name:
            data["name"] = name
        if environment:
            data["environment"] = environment
        if config:
            data["config"] = config
            
        test_run = await testzeus_client.test_runs.create(data)
        
        if ctx:
            await ctx.info(f"Created test run: {test_run.name}")
            
        return f"Successfully created test run '{test_run.name}' with ID: {test_run.id}"
    except Exception as e:
        error_msg = f"Error creating test run: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Environment Management Tools
@mcp.tool()
async def list_environments(
    page: int = 1,
    per_page: int = 50,
    ctx: Context = None
) -> str:
    """List all environments in TestZeus."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        per_page = min(per_page, 100)
        result = await testzeus_client.environments.get_list(page=page, per_page=per_page)
        environments = result.get("items", [])
        
        env_list = []
        for env in environments:
            env_list.append({
                "id": env.id,
                "name": env.name,
                "description": env.description,
                "config": getattr(env, "config", None),
                "created": str(env.created),
                "updated": str(env.updated),
            })
        
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
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        env = await testzeus_client.environments.get_one(environment_id_or_name)
        env_data = {
            "id": env.id,
            "name": env.name,
            "description": env.description,
            "config": getattr(env, "config", None),
            "metadata": getattr(env, "metadata", None),
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
    description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    ctx: Context = None
) -> str:
    """Create a new environment."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus first."
    
    try:
        data = {"name": name}
        if description:
            data["description"] = description
        if config:
            data["config"] = config
            
        env = await testzeus_client.environments.create(data)
        
        if ctx:
            await ctx.info(f"Created environment: {name}")
            
        return f"Successfully created environment '{name}' with ID: {env.id}"
    except Exception as e:
        error_msg = f"Error creating environment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return error_msg


# Resources for browsing TestZeus entities
@mcp.resource("tests://")
async def list_tests_resource() -> str:
    """List all tests as a browsable resource."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
    try:
        result = await testzeus_client.tests.get_list(per_page=100)
        tests = result.get("items", [])
        
        test_list = []
        for test in tests:
            test_list.append({
                "id": test.id,
                "name": test.name,
                "status": test.status,
                "test_feature": test.test_feature,
                "uri": f"test://{test.id}"
            })
        
        return json.dumps({"tests": test_list}, indent=2)
    except Exception as e:
        return f"Error listing tests: {str(e)}"


@mcp.resource("test://{test_id}")
async def get_test_resource(test_id: str) -> str:
    """Get a specific test as a resource."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
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
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
    try:
        result = await testzeus_client.test_runs.get_list(per_page=100)
        test_runs = result.get("items", [])
        
        run_list = []
        for run in test_runs:
            run_list.append({
                "id": run.id,
                "name": run.name,
                "status": run.status,
                "test": run.test,
                "uri": f"test-run://{run.id}"
            })
        
        return json.dumps({"test_runs": run_list}, indent=2)
    except Exception as e:
        return f"Error listing test runs: {str(e)}"


@mcp.resource("test-run://{test_run_id}")
async def get_test_run_resource(test_run_id: str) -> str:
    """Get a specific test run as a resource."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
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
            "workflow_run_id": getattr(run, "workflow_run_id", None),
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
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
    try:
        result = await testzeus_client.environments.get_list(per_page=100)
        environments = result.get("items", [])
        
        env_list = []
        for env in environments:
            env_list.append({
                "id": env.id,
                "name": env.name,
                "description": env.description,
                "uri": f"environment://{env.id}"
            })
        
        return json.dumps({"environments": env_list}, indent=2)
    except Exception as e:
        return f"Error listing environments: {str(e)}"


@mcp.resource("environment://{environment_id}")
async def get_environment_resource(environment_id: str) -> str:
    """Get a specific environment as a resource."""
    if not await ensure_authenticated():
        return "Error: Not authenticated. Use authenticate_testzeus tool first."
    
    try:
        env = await testzeus_client.environments.get_one(environment_id)
        env_data = {
            "id": env.id,
            "name": env.name,
            "description": env.description,
            "config": getattr(env, "config", None),
            "metadata": getattr(env, "metadata", None),
            "created": str(env.created),
            "updated": str(env.updated),
            "tenant": env.tenant,
            "modified_by": env.modified_by,
        }
        
        return json.dumps(env_data, indent=2)
    except Exception as e:
        return f"Error getting environment: {str(e)}"


# Server run function for backwards compatibility
async def run():
    """Run the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    mcp.run()
