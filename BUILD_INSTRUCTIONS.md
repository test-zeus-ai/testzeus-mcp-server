# Build Instructions for TestZeus MCP Server

This document provides instructions for building and publishing the TestZeus MCP Server package.

## Prerequisites

- Python >= 3.11
- UV package manager

## UV Version Compatibility

This project supports both older and newer versions of UV:

### For UV versions < 0.4.0 (Current: 0.3.0)
- Use `make build` and `make publish`
- Uses `python -m build` and `twine` internally

### For UV versions >= 0.4.0
- First run `make upgrade-uv` to upgrade UV
- Then use `make build-modern` and `make publish-modern`
- Uses native `uv build` and `uv publish` commands

## Available Make Targets

### Development
- `make install` - Install the project in dev mode
- `make dev-install` - Install with development dependencies  
- `make fmt` - Format code using ruff
- `make lint` - Run ruff linter with formatting
- `make test` - Run tests with linting
- `make run` - Run the MCP server
- `make clean` - Clean unused files

### Building & Publishing
- `make build` - Build package (compatible with current UV version)
- `make build-modern` - Build using modern uv build (requires UV >= 0.4.0)
- `make publish` - Publish to PyPI using twine
- `make publish-modern` - Publish using modern uv publish (requires UV >= 0.4.0)
- `make check-build` - Verify package can be built and installed
- `make upgrade-uv` - Upgrade UV to latest version

### Release Management
- `make release` - Interactive release with custom version
- `make release-patch` - Automatic patch version bump (2.0.0 → 2.0.1)
- `make release-minor` - Automatic minor version bump (2.0.0 → 2.1.0)
- `make release-major` - Automatic major version bump (2.0.0 → 3.0.0)
- `make release-custom` - Custom version release

## Quick Start

1. **Setup development environment:**
   ```bash
   make dev-install
   ```

2. **Build the package:**
   ```bash
   make build
   ```

3. **Verify the build:**
   ```bash
   make check-build
   ```

4. **Publish to PyPI:**
   ```bash
   export PYPI_API_TOKEN=your_token_here
   make publish
   ```

## Build Process Details

The build process:

1. **Cleans** the environment of old build artifacts
2. **Installs** build dependencies using UV
3. **Creates** both source distribution (.tar.gz) and wheel (.whl) files
4. **Places** artifacts in the `dist/` directory

## Publishing Requirements

To publish to PyPI, you need:

1. **PyPI API Token:** Set the `PYPI_API_TOKEN` environment variable
2. **Built packages:** Run `make build` first
3. **Valid credentials:** The token should have permission to publish this package

## Upgrading UV

To use the modern UV build/publish features:

```bash
make upgrade-uv
# Restart your shell or source your profile
make build-modern
make publish-modern
```

## Troubleshooting

### Build Failures
- Ensure you have the latest dependencies: `make dev-install`
- Clean and rebuild: `make clean && make build`
- Check UV version: `uv --version`

### Import Errors
- Verify package structure matches `pyproject.toml`
- Check that all dependencies are properly declared
- Test import: `make check-build`

### Publishing Issues
- Verify PYPI_API_TOKEN is set correctly
- Ensure you have permission to publish this package
- Check network connectivity

## Project Structure

The project follows standard Python packaging conventions:

```
testzeus-mcp-server/
├── testzeus_mcp_server/     # Main package directory
├── pyproject.toml           # Package configuration
├── README.md               # Project documentation
├── Makefile               # Build automation
└── dist/                  # Build artifacts (created by build)
```

## Dependencies

### Runtime Dependencies
- fastmcp >= 2.0.0
- testzeus-sdk >= 0.0.9
- aiohttp >= 3.8.0

### Development Dependencies
- pytest >= 7.0.0
- pytest-asyncio >= 0.21.0
- ruff >= 0.1.0
- build >= 1.0.0
- twine >= 4.0.0

All dependencies are managed through UV and defined in `pyproject.toml`. 