"""
Main entry point for TestZeus FastMCP Server.
"""

import asyncio
import sys


def main() -> None:
    """Main entry point for the TestZeus FastMCP Server."""
    try:
        from .server import mcp
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down TestZeus MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error running TestZeus MCP Server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
