"""Tests for pyproject.toml configuration."""

import os
import tomllib
from pathlib import Path

import pytest


class TestPyprojectToml:
    """Test suite for pyproject.toml configuration file."""

    @pytest.fixture
    def pyproject_path(self):
        """Get the path to pyproject.toml."""
        return Path(__file__).parent.parent / "pyproject.toml"

    @pytest.fixture
    def pyproject_data(self, pyproject_path):
        """Load and parse pyproject.toml."""
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)

    def test_pyproject_exists(self, pyproject_path):
        """Test that pyproject.toml exists."""
        assert pyproject_path.exists(), "pyproject.toml file not found"
        assert pyproject_path.is_file(), "pyproject.toml is not a file"

    def test_pyproject_valid_toml(self, pyproject_path):
        """Test that pyproject.toml is valid TOML."""
        try:
            with open(pyproject_path, "rb") as f:
                tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML syntax: {e}")

    def test_build_system_present(self, pyproject_data):
        """Test that build-system section is present."""
        assert "build-system" in pyproject_data
        assert "requires" in pyproject_data["build-system"]
        assert "build-backend" in pyproject_data["build-system"]

    def test_build_system_uses_hatchling(self, pyproject_data):
        """Test that hatchling is used as build backend."""
        assert pyproject_data["build-system"]["build-backend"] == "hatchling.build"
        assert "hatchling" in pyproject_data["build-system"]["requires"]

    def test_project_metadata_present(self, pyproject_data):
        """Test that required project metadata is present."""
        assert "project" in pyproject_data
        project = pyproject_data["project"]

        # Required fields
        assert "name" in project
        assert "version" in project
        assert "description" in project
        assert "requires-python" in project

    def test_project_name(self, pyproject_data):
        """Test project name is correct."""
        assert pyproject_data["project"]["name"] == "testzeus-mcp-server"

    def test_project_version_format(self, pyproject_data):
        """Test project version follows semantic versioning."""
        version = pyproject_data["project"]["version"]
        parts = version.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"
        for part in parts:
            assert part.isdigit() or part.startswith("0"), f"Invalid version part: {part}"

    def test_project_version_is_valid(self, pyproject_data):
        """Test that version is current and valid."""
        version = pyproject_data["project"]["version"]
        assert version == "2.0.0", f"Expected version 2.0.0, got {version}"

    def test_python_version_requirement(self, pyproject_data):
        """Test Python version requirement."""
        requires_python = pyproject_data["project"]["requires-python"]
        assert ">=3.11" in requires_python or "3.11" in requires_python
        assert "<4.0" in requires_python or "4.0" in requires_python

    def test_dependencies_present(self, pyproject_data):
        """Test that required dependencies are listed."""
        dependencies = pyproject_data["project"]["dependencies"]
        assert isinstance(dependencies, list)
        assert len(dependencies) > 0

        # Check for key dependencies
        dep_names = [dep.split(">=")[0].split("==")[0] for dep in dependencies]
        assert "fastmcp" in dep_names
        assert "testzeus-sdk" in dep_names
        assert "aiohttp" in dep_names

    def test_fastmcp_version(self, pyproject_data):
        """Test FastMCP version constraint."""
        dependencies = pyproject_data["project"]["dependencies"]
        fastmcp_dep = [d for d in dependencies if d.startswith("fastmcp")][0]
        assert ">=2.0.0" in fastmcp_dep, "FastMCP should be >= 2.0.0"

    def test_testzeus_sdk_version(self, pyproject_data):
        """Test TestZeus SDK version constraint."""
        dependencies = pyproject_data["project"]["dependencies"]
        sdk_dep = [d for d in dependencies if d.startswith("testzeus-sdk")][0]
        assert ">=0.0.10" in sdk_dep, "TestZeus SDK should be >= 0.0.10"

    def test_dev_dependencies(self, pyproject_data):
        """Test that dev dependencies are specified."""
        assert "project" in pyproject_data
        assert "optional-dependencies" in pyproject_data["project"]
        assert "dev" in pyproject_data["project"]["optional-dependencies"]

        dev_deps = pyproject_data["project"]["optional-dependencies"]["dev"]
        dev_dep_names = [dep.split(">=")[0].split("==")[0] for dep in dev_deps]

        # Check for essential dev tools
        assert "pytest" in dev_dep_names
        assert "pytest-asyncio" in dev_dep_names
        assert "ruff" in dev_dep_names

    def test_scripts_entry_point(self, pyproject_data):
        """Test that command-line entry point is defined."""
        assert "project" in pyproject_data
        assert "scripts" in pyproject_data["project"]
        scripts = pyproject_data["project"]["scripts"]

        assert "testzeus-mcp-server" in scripts
        entry_point = scripts["testzeus-mcp-server"]
        assert entry_point == "testzeus_mcp_server.__main__:main"

    def test_project_urls(self, pyproject_data):
        """Test that project URLs are defined."""
        assert "project" in pyproject_data
        assert "urls" in pyproject_data["project"]
        urls = pyproject_data["project"]["urls"]

        assert "Homepage" in urls
        assert "Repository" in urls
        assert "Issues" in urls

        # Verify URLs are valid-looking
        assert urls["Homepage"].startswith("https://")
        assert urls["Repository"].startswith("https://")
        assert urls["Issues"].startswith("https://")

    def test_repository_url_correct(self, pyproject_data):
        """Test that repository URL is correct."""
        urls = pyproject_data["project"]["urls"]
        assert (
            "github.com/testzeus/testzeus-mcp-server" in urls["Repository"]
        )

    def test_authors_present(self, pyproject_data):
        """Test that authors are specified."""
        assert "authors" in pyproject_data["project"]
        authors = pyproject_data["project"]["authors"]
        assert len(authors) > 0
        assert "name" in authors[0]

    def test_readme_specified(self, pyproject_data):
        """Test that README is specified."""
        assert "readme" in pyproject_data["project"]
        assert pyproject_data["project"]["readme"] == "README.md"

        # Verify README exists
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md file not found"

    def test_hatch_build_targets(self, pyproject_data):
        """Test hatch build configuration."""
        assert "tool" in pyproject_data
        assert "hatch" in pyproject_data["tool"]
        assert "build" in pyproject_data["tool"]["hatch"]
        assert "targets" in pyproject_data["tool"]["hatch"]["build"]
        assert "wheel" in pyproject_data["tool"]["hatch"]["build"]["targets"]

        wheel_config = pyproject_data["tool"]["hatch"]["build"]["targets"]["wheel"]
        assert "packages" in wheel_config
        assert "testzeus_mcp_server" in wheel_config["packages"]

    def test_ruff_configuration(self, pyproject_data):
        """Test ruff linter configuration."""
        assert "tool" in pyproject_data
        assert "ruff" in pyproject_data["tool"]

        ruff_config = pyproject_data["tool"]["ruff"]
        assert "line-length" in ruff_config
        assert "target-version" in ruff_config

        # Check line length is reasonable
        assert ruff_config["line-length"] == 100

        # Check target version
        assert ruff_config["target-version"] == "py311"

    def test_ruff_lint_rules(self, pyproject_data):
        """Test ruff lint rules are configured."""
        assert "tool" in pyproject_data
        assert "ruff" in pyproject_data["tool"]
        assert "lint" in pyproject_data["tool"]["ruff"]

        lint_config = pyproject_data["tool"]["ruff"]["lint"]
        assert "select" in lint_config

        # Verify essential rules are enabled
        rules = lint_config["select"]
        assert "E" in rules  # Error
        assert "F" in rules  # Pyflakes
        assert "W" in rules  # Warning
        assert "I" in rules  # Import sorting
        assert "UP" in rules  # Upgrade syntax

    def test_no_conflicting_dependencies(self, pyproject_data):
        """Test that there are no conflicting dependency versions."""
        dependencies = pyproject_data["project"]["dependencies"]
        dep_dict = {}

        for dep in dependencies:
            name = dep.split(">=")[0].split("==")[0].split("<")[0]
            if name in dep_dict:
                pytest.fail(f"Duplicate dependency: {name}")
            dep_dict[name] = dep

    def test_uv_tool_configuration(self, pyproject_data):
        """Test UV tool configuration is present."""
        assert "tool" in pyproject_data
        assert "uv" in pyproject_data["tool"]

    def test_all_dependencies_have_versions(self, pyproject_data):
        """Test that all dependencies specify version constraints."""
        dependencies = pyproject_data["project"]["dependencies"]

        for dep in dependencies:
            # Should have version specifier (>=, ==, <, etc.)
            assert any(
                op in dep for op in [">=", "==", ">", "<", "~="]
            ), f"Dependency missing version constraint: {dep}"

    def test_project_description_not_empty(self, pyproject_data):
        """Test that project description is meaningful."""
        description = pyproject_data["project"]["description"]
        assert len(description) > 20, "Description should be descriptive"
        assert "TestZeus" in description
        assert "MCP" in description

    def test_python_dateutil_dependency(self, pyproject_data):
        """Test that python-dateutil is included (required dependency)."""
        dependencies = pyproject_data["project"]["dependencies"]
        dep_names = [dep.split(">=")[0].split("==")[0] for dep in dependencies]
        assert "python-dateutil" in dep_names

    def test_optional_dependencies_structure(self, pyproject_data):
        """Test structure of optional dependencies."""
        optional_deps = pyproject_data["project"]["optional-dependencies"]
        assert isinstance(optional_deps, dict)

        for group_name, deps in optional_deps.items():
            assert isinstance(deps, list), f"{group_name} should be a list"
            for dep in deps:
                assert isinstance(dep, str), f"Dependency in {group_name} should be string"


class TestPyprojectIntegrity:
    """Test suite for pyproject.toml file integrity and consistency."""

    def test_package_directory_exists(self):
        """Test that the main package directory exists."""
        package_dir = Path(__file__).parent.parent / "testzeus_mcp_server"
        assert package_dir.exists(), "Package directory not found"
        assert package_dir.is_dir(), "Package path is not a directory"

    def test_package_has_init(self):
        """Test that package has __init__.py."""
        init_file = Path(__file__).parent.parent / "testzeus_mcp_server" / "__init__.py"
        assert init_file.exists(), "__init__.py not found in package"

    def test_package_has_main(self):
        """Test that package has __main__.py."""
        main_file = Path(__file__).parent.parent / "testzeus_mcp_server" / "__main__.py"
        assert main_file.exists(), "__main__.py not found in package"

    def test_package_has_server(self):
        """Test that package has server.py."""
        server_file = Path(__file__).parent.parent / "testzeus_mcp_server" / "server.py"
        assert server_file.exists(), "server.py not found in package"

    def test_entry_point_file_exists(self):
        """Test that the entry point file specified in pyproject.toml exists."""
        # Entry point: testzeus_mcp_server.__main__:main
        main_file = Path(__file__).parent.parent / "testzeus_mcp_server" / "__main__.py"
        assert main_file.exists(), "Entry point file not found"

    def test_readme_mentioned_exists(self):
        """Test that README.md mentioned in pyproject.toml exists."""
        readme_file = Path(__file__).parent.parent / "README.md"
        assert readme_file.exists(), "README.md not found"

    def test_dependencies_installable(self):
        """Test that key dependencies are importable (if installed)."""
        try:
            import fastmcp  # noqa: F401
            import testzeus_sdk  # noqa: F401
            import aiohttp  # noqa: F401
        except ImportError as e:
            pytest.skip(f"Dependencies not installed: {e}")

    def test_dev_dependencies_installable(self):
        """Test that dev dependencies are importable (if installed)."""
        try:
            import pytest  # noqa: F401
            import ruff  # noqa: F401
        except ImportError as e:
            pytest.skip(f"Dev dependencies not installed: {e}")


class TestPyprojectEdgeCases:
    """Test edge cases and regression scenarios for pyproject.toml."""

    @pytest.fixture
    def pyproject_path(self):
        """Get the path to pyproject.toml."""
        return Path(__file__).parent.parent / "pyproject.toml"

    @pytest.fixture
    def pyproject_data(self, pyproject_path):
        """Load and parse pyproject.toml."""
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)

    def test_no_empty_sections(self, pyproject_data):
        """Test that there are no empty sections."""
        def check_empty(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, (dict, list)) and len(value) == 0:
                        pytest.fail(f"Empty section found: {current_path}")
                    check_empty(value, current_path)

        check_empty(pyproject_data)

    def test_version_not_zero(self, pyproject_data):
        """Test that version is not 0.0.0."""
        version = pyproject_data["project"]["version"]
        assert version != "0.0.0", "Version should not be 0.0.0"

    def test_no_todo_comments_in_fields(self, pyproject_data):
        """Test that there are no TODO comments in important fields."""
        def check_todos(data):
            if isinstance(data, str):
                assert "TODO" not in data.upper(), f"TODO found in: {data}"
            elif isinstance(data, dict):
                for value in data.values():
                    check_todos(value)
            elif isinstance(data, list):
                for item in data:
                    check_todos(item)

        check_todos(pyproject_data["project"])

    def test_urls_are_https(self, pyproject_data):
        """Test that all URLs use HTTPS."""
        urls = pyproject_data["project"]["urls"]
        for name, url in urls.items():
            assert url.startswith("https://"), f"{name} URL should use HTTPS: {url}"

    def test_license_field_optional(self, pyproject_data):
        """Test license handling (optional field)."""
        # License is optional, just check if present it's valid
        if "license" in pyproject_data["project"]:
            license_info = pyproject_data["project"]["license"]
            assert isinstance(license_info, (str, dict))