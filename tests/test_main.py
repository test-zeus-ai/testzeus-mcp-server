"""Tests for testzeus_mcp_server.__main__ module."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch, Mock

import pytest


class TestMain:
    """Test suite for the main entry point."""

    def test_main_successful_run(self):
        """Test successful server startup."""
        # Mock the server module before importing
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock()
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            # Import and execute within the patched context
            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")
            main_module.main()

            # Restore stdout
            sys.stdout = sys.__stdout__

            # Verify
            mock_mcp.run.assert_called_once()
            assert "Starting TestZeus MCP Server..." in captured_output.getvalue()

    def test_main_keyboard_interrupt(self):
        """Test graceful shutdown on KeyboardInterrupt."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock(side_effect=KeyboardInterrupt())
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")

            with pytest.raises(SystemExit) as exc_info:
                main_module.main()

            sys.stdout = sys.__stdout__

            # Verify exit code is 0 (clean shutdown)
            assert exc_info.value.code == 0
            assert "Shutting down TestZeus MCP Server..." in captured_output.getvalue()

    def test_main_exception_handling(self):
        """Test error handling for general exceptions."""
        error_message = "Test error"
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock(side_effect=Exception(error_message))
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")

            with pytest.raises(SystemExit) as exc_info:
                main_module.main()

            sys.stdout = sys.__stdout__

            # Verify exit code is 1 (error)
            assert exc_info.value.code == 1
            output = captured_output.getvalue()
            assert "Error running TestZeus MCP Server:" in output
            assert error_message in output

    def test_main_import_error(self):
        """Test handling of import errors."""
        # Simulate ImportError when trying to import the server module
        with patch.dict("sys.modules", {"testzeus_mcp_server.server": None}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            # This will cause ImportError when main() tries to import server
            with pytest.raises((SystemExit, ImportError)):
                main_module = importlib.import_module("testzeus_mcp_server.__main__")
                main_module.main()

            sys.stdout = sys.__stdout__

    def test_main_as_module(self):
        """Test running as a module with __name__ == '__main__'."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock()
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")
            assert callable(main_module.main)

    def test_main_prints_startup_message(self):
        """Test that startup message is printed."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock()
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")
            main_module.main()

            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()
            assert "Starting TestZeus MCP Server..." in output

    def test_main_runtime_error(self):
        """Test handling of RuntimeError."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock(side_effect=RuntimeError("Runtime issue"))
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")

            with pytest.raises(SystemExit) as exc_info:
                main_module.main()

            sys.stdout = sys.__stdout__

            assert exc_info.value.code == 1
            output = captured_output.getvalue()
            assert "Error running TestZeus MCP Server:" in output
            assert "Runtime issue" in output

    def test_main_value_error(self):
        """Test handling of ValueError."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock(side_effect=ValueError("Invalid value"))
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            captured_output = StringIO()
            sys.stdout = captured_output

            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")

            with pytest.raises(SystemExit) as exc_info:
                main_module.main()

            sys.stdout = sys.__stdout__

            assert exc_info.value.code == 1
            output = captured_output.getvalue()
            assert "Error running TestZeus MCP Server:" in output
            assert "Invalid value" in output

    def test_main_multiple_calls(self):
        """Test that main can be called multiple times (edge case)."""
        mock_server = Mock()
        mock_mcp = MagicMock()
        mock_mcp.run = MagicMock()
        mock_server.mcp = mock_mcp

        with patch.dict("sys.modules", {"testzeus_mcp_server.server": mock_server}):
            import importlib
            if "testzeus_mcp_server.__main__" in sys.modules:
                del sys.modules["testzeus_mcp_server.__main__"]

            main_module = importlib.import_module("testzeus_mcp_server.__main__")

            # Call main multiple times
            captured_output = StringIO()
            sys.stdout = captured_output
            main_module.main()
            first_call_count = mock_mcp.run.call_count
            sys.stdout = sys.__stdout__

            captured_output = StringIO()
            sys.stdout = captured_output
            main_module.main()
            second_call_count = mock_mcp.run.call_count
            sys.stdout = sys.__stdout__

            # Each call should increment the call count
            assert second_call_count == first_call_count + 1