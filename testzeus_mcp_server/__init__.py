"""
TestZeus FastMCP Server - Expose TestZeus testing platform via FastMCP.

This package provides a FastMCP server that allows MCP clients (like Claude Desktop)
to interact with the TestZeus intelligent testing platform through modern FastMCP
decorators and clean function-based tools and resources.
"""

from .server import mcp

__version__ = "2.0.0"
__author__ = "TestZeus Team"
__email__ = "support@testzeus.com"

__all__ = ["mcp"]
