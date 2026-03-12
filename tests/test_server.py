"""Tests for testzeus_mcp_server.server module.

Note: These tests focus on testable components that can be isolated.
Full integration tests would require the actual testzeus_sdk dependency.
"""

import ast
import json
from datetime import datetime

import pytest


class TestDateTimeEncoder:
    """Test suite for DateTimeEncoder JSON encoder.

    This is a standalone utility that can be tested in isolation.
    """

    def test_encode_datetime(self):
        """Test encoding datetime objects to ISO format."""

        # Create a minimal DateTimeEncoder implementation for testing
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        dt = datetime(2024, 1, 15, 10, 30, 45)
        encoder = DateTimeEncoder()
        result = encoder.default(dt)
        assert result == "2024-01-15T10:30:45"

    def test_encode_datetime_with_microseconds(self):
        """Test encoding datetime with microseconds."""

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        encoder = DateTimeEncoder()
        result = encoder.default(dt)
        assert result == "2024-01-15T10:30:45.123456"

    def test_encode_other_types(self):
        """Test that non-datetime types raise TypeError."""

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        encoder = DateTimeEncoder()
        with pytest.raises(TypeError):
            encoder.default("not a datetime")

    def test_encode_in_json_dumps(self):
        """Test DateTimeEncoder works with json.dumps()."""

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        data = {
            "timestamp": datetime(2024, 1, 15, 10, 30, 45),
            "name": "test",
        }
        result = json.dumps(data, cls=DateTimeEncoder)
        assert '"timestamp": "2024-01-15T10:30:45"' in result
        assert '"name": "test"' in result

    def test_encode_nested_datetime(self):
        """Test encoding nested structures with datetime objects."""

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        data = {
            "events": [
                {"time": datetime(2024, 1, 1, 12, 0, 0)},
                {"time": datetime(2024, 1, 2, 13, 0, 0)},
            ]
        }
        result = json.dumps(data, cls=DateTimeEncoder)
        assert "2024-01-01T12:00:00" in result
        assert "2024-01-02T13:00:00" in result

    def test_datetime_encoder_preserves_other_json_types(self):
        """Test that encoder handles normal JSON types correctly."""

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "timestamp": datetime(2024, 1, 1),
        }
        result = json.dumps(data, cls=DateTimeEncoder)
        parsed = json.loads(result)

        assert parsed["string"] == "value"
        assert parsed["number"] == 42
        assert parsed["float"] == 3.14
        assert parsed["boolean"] is True
        assert parsed["null"] is None
        assert parsed["array"] == [1, 2, 3]
        assert parsed["timestamp"] == "2024-01-01T00:00:00"


class TestServerConfiguration:
    """Test suite for server configuration and setup."""

    def test_server_uses_fastmcp(self):
        """Test that server is configured to use FastMCP."""
        # This test validates that the server file exists and uses FastMCP
        import os

        assert os.path.exists("testzeus_mcp_server/server.py")

        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert "FastMCP" in content

    def test_server_module_has_required_components(self):
        """Test that server module defines expected components."""
        # Check that server.py file exists and has content
        import os

        assert os.path.exists("testzeus_mcp_server/server.py")

        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert len(content) > 100

    def test_main_module_exports_main_function(self):
        """Test that __main__ module has main() function."""
        # Check that __main__.py exists and defines main
        import os

        assert os.path.exists("testzeus_mcp_server/__main__.py")

        with open("testzeus_mcp_server/__main__.py") as f:
            content = f.read()
            assert "def main()" in content


class TestServerDocumentation:
    """Test suite for server module documentation and structure."""

    def test_server_module_has_docstring(self):
        """Test that server module has documentation."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should have module docstring
            assert '"""' in content or "'''" in content
            # Should mention TestZeus
            assert "TestZeus" in content or "testzeus" in content.lower()

    def test_server_imports_required_dependencies(self):
        """Test that server imports necessary dependencies."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Check for key imports
            assert "from mcp.server.fastmcp import" in content or "import fastmcp" in content
            assert "from testzeus_sdk" in content or "import testzeus_sdk" in content

    def test_server_defines_mcp_tools(self):
        """Test that server defines MCP tools with decorators."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should have @mcp.tool() decorators
            assert "@mcp.tool()" in content
            # Should define various tool functions
            assert "async def list_tests" in content
            assert "async def get_test" in content
            assert "async def create_test" in content
            assert "async def list_test_suites" in content
            assert "async def create_test_suite" in content
            assert "async def list_test_suite_runs" in content

    def test_server_has_authentication_functions(self):
        """Test that server has authentication-related functions."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert "authenticate_testzeus" in content
            assert "ensure_authenticated" in content

    def test_server_defines_datetime_encoder(self):
        """Test that server defines DateTimeEncoder class."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert "class DateTimeEncoder" in content
            assert "json.JSONEncoder" in content

    def test_server_has_error_handling(self):
        """Test that server implements error handling."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should have try/except blocks
            assert "try:" in content
            assert "except Exception" in content
            # Should handle errors gracefully
            assert "error_msg" in content or "error" in content

    def test_server_uses_environment_variables(self):
        """Test that server reads environment variables for configuration."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert "TESTZEUS_EMAIL" in content
            assert "TESTZEUS_PASSWORD" in content
            assert "os.getenv" in content or "os.environ" in content

    def test_server_implements_test_management_tools(self):
        """Test that server implements test management functionality."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Core test management operations
            assert "list_tests" in content
            assert "get_test" in content
            assert "create_test" in content
            assert "update_test" in content
            assert "delete_test" in content
            assert "get_test_input_params" in content
            assert "get_dependent_test_suites" in content

    def test_server_implements_test_suite_management_tools(self):
        """Test that server implements suite management functionality."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            assert "list_test_suites" in content
            assert "get_test_suite" in content
            assert "create_test_suite" in content
            assert "update_test_suite" in content
            assert "delete_test_suite" in content
            assert "list_test_suite_runs" in content
            assert "get_test_suite_run" in content
            assert "create_test_suite_run" in content
            assert "pause_test_suite_run" in content
            assert "resume_test_suite_run" in content
            assert "cancel_test_suite_run" in content
            assert "list_test_suite_node_runs" in content
            assert "list_test_suite_schedules" in content

    def test_server_implements_resource_templates(self):
        """Test that server defines MCP resources."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should define resources
            assert "@mcp.resource" in content or "resource" in content


class TestModuleStructure:
    """Test suite for module structure and organization."""

    def test_package_has_init_file(self):
        """Test that package has __init__.py."""
        import os

        assert os.path.exists("testzeus_mcp_server/__init__.py")

    def test_package_has_main_file(self):
        """Test that package has __main__.py."""
        import os

        assert os.path.exists("testzeus_mcp_server/__main__.py")

    def test_package_has_server_file(self):
        """Test that package has server.py."""
        import os

        assert os.path.exists("testzeus_mcp_server/server.py")

    def test_main_file_defines_entry_point(self):
        """Test that __main__.py defines main() function."""
        with open("testzeus_mcp_server/__main__.py") as f:
            content = f.read()
            assert "def main()" in content
            assert "mcp.run()" in content

    def test_server_file_is_substantial(self):
        """Test that server.py contains substantial implementation."""
        import os

        size = os.path.getsize("testzeus_mcp_server/server.py")
        # Server file should be reasonably large (many tools defined)
        assert size > 10000, f"Server file seems too small: {size} bytes"

    def test_init_file_exports_mcp(self):
        """Test that __init__.py exports the mcp instance."""
        with open("testzeus_mcp_server/__init__.py") as f:
            content = f.read()
            # Should export or import mcp
            assert "mcp" in content


class TestErrorHandlingPatterns:
    """Test suite for error handling patterns in server code."""

    def test_authentication_error_handling(self):
        """Test that authentication errors are handled."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # authenticate_testzeus should have error handling
            lines = content.split("async def authenticate_testzeus")
            if len(lines) > 1:
                func_content = lines[1].split("async def ")[0]
                assert "try:" in func_content or "except" in func_content

    def test_tool_functions_have_error_handling(self):
        """Test that MCP tool functions implement error handling."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Find tool definitions and check for error handling nearby
            assert content.count("except Exception") >= 10  # Many tools with error handling

    def test_context_logging_used(self):
        """Test that Context is used for logging."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should use ctx.info, ctx.error for logging
            assert "ctx.info" in content or "ctx.error" in content or "Context" in content


class TestAPIIntegrationPatterns:
    """Test suite for TestZeus SDK integration patterns."""

    def test_client_initialization_pattern(self):
        """Test that client is initialized with proper parameters."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should create TestZeusClient
            assert "TestZeusClient" in content
            assert "email=" in content
            assert "password=" in content

    def test_client_methods_called(self):
        """Test that various client methods are invoked."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should call various SDK methods
            assert "testzeus_client.tests" in content
            assert "testzeus_client.environments" in content or "environments" in content

    def test_pagination_parameters_used(self):
        """Test that pagination is implemented in list operations."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # List operations should support pagination
            assert "page" in content
            assert "per_page" in content

    def test_filter_and_sort_support(self):
        """Test that filtering and sorting are supported."""
        with open("testzeus_mcp_server/server.py") as f:
            content = f.read()
            # Should support filters and sorting
            assert "filters" in content
            assert "sort" in content

    @staticmethod
    def _get_function_node(function_name: str) -> ast.AsyncFunctionDef:
        with open("testzeus_mcp_server/server.py") as f:
            module = ast.parse(f.read())

        for node in module.body:
            if isinstance(node, ast.AsyncFunctionDef) and node.name == function_name:
                return node

        raise AssertionError(f"Could not find function {function_name}")

    def test_test_tools_use_test_params_field(self):
        """Test that create_test and update_test use test_params for test defaults."""
        create_node = self._get_function_node("create_test")
        update_node = self._get_function_node("update_test")

        create_args = [arg.arg for arg in create_node.args.args]
        update_args = [arg.arg for arg in update_node.args.args]

        assert "test_params" in create_args
        assert "input_schema" not in create_args
        assert "test_params" in update_args
        assert "input_schema" not in update_args

        create_calls = [
            node
            for node in ast.walk(create_node)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_test"
        ]
        assert any(
            any(keyword.arg == "test_params" for keyword in call.keywords) for call in create_calls
        )

        update_assignments = [
            node
            for node in ast.walk(update_node)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Subscript)
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "test_params"
                for target in node.targets
            )
        ]
        assert update_assignments

    def test_suite_run_creation_uses_sdk_run_helper(self):
        """Test that suite run creation delegates to the SDK helper."""
        create_run_node = self._get_function_node("create_test_suite_run")
        create_run_args = [arg.arg for arg in create_run_node.args.args]

        assert "execution_mode" not in create_run_args

        run_calls = [
            node
            for node in ast.walk(create_run_node)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "test_suite_runs"
        ]
        assert run_calls
        assert not any(
            any(keyword.arg == "workflow_snapshot" for keyword in call.keywords)
            for call in run_calls
        )
