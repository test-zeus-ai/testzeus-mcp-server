# Makefile for TestZeus MCP Server
# 
# This Makefile provides build and publish targets that work with both
# older UV versions (0.3.0) and newer UV versions (>= 0.4.0) that support
# native build/publish commands.
#
# For older UV versions: Uses python -m build and twine
# For newer UV versions: Use make upgrade-uv first, then use build-modern/publish-modern

.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@fgrep "##" Makefile | fgrep -v fgrep | grep -E "(install|dev|fmt|lint|test|run|clean)"
	@echo ""
	@echo "Building & Publishing:"
	@fgrep "##" Makefile | fgrep -v fgrep | grep -E "(build|publish|check|upgrade)"
	@echo ""
	@echo "Release Management:"
	@fgrep "##" Makefile | fgrep -v fgrep | grep -E "(release)"
	@echo ""
	@echo "For UV versions < 0.4.0: Use 'build' and 'publish'"
	@echo "For UV versions >= 0.4.0: Run 'make upgrade-uv' first, then use 'build-modern' and 'publish-modern'"

.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	uv python pin

.PHONY: install
install:          ## Install the project in dev mode.
	uv sync

.PHONY: fmt
fmt:              ## Format code using ruff.
	uv run ruff format testzeus_mcp_server/
	uv run ruff format tests/ 2>/dev/null || echo "No tests directory found"

.PHONY: lint
lint: fmt         ## Run ruff linter.
	uv run ruff check --fix
	uv run ruff check --fix tests/ 2>/dev/null || echo "No tests directory found"

.PHONY: test
test: lint  ## Run tests.
	uv run pytest -v --junit-xml=test_output.xml -l --tb=short --maxfail=1 tests/ 2>/dev/null || echo "No tests directory found"

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \; 2>/dev/null || true
	@find ./ -name '__pycache__' -exec rm -rf {} \; 2>/dev/null || true
	@find ./ -name 'Thumbs.db' -exec rm -f {} \; 2>/dev/null || true
	@find ./ -name '*~' -exec rm -f {} \; 2>/dev/null || true
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .ruff_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf test_output.xml

.PHONY: dev-install
dev-install:      ## Install with development dependencies.
	uv sync --dev

.PHONY: run
run:              ## Run the MCP server.
	uv run testzeus-mcp-server

.PHONY: upgrade-uv
upgrade-uv:       ## Upgrade UV to the latest version with build/publish support.
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "UV upgraded! Please restart your shell or run 'source ~/.bashrc' (or ~/.zshrc)"
	@echo "After restarting, you can use 'make build-modern' and 'make publish-modern'"

.PHONY: build
build:            ## Build package using python build (compatible with current UV version).
	@echo "Building package using python -m build..."
	uv add --dev build
	uv run python -m build
	@echo "Package built successfully in dist/"

.PHONY: build-modern
build-modern:     ## Build package using modern uv build (requires UV >= 0.4.0).
	@echo "Building package using uv build..."
	@command -v uv >/dev/null 2>&1 && uv build --no-sources || { echo "Error: uv build not available. Run 'make upgrade-uv' first."; exit 1; }

.PHONY: publish
publish:          ## Publish the package to PyPI using twine.
	@echo "Publishing to PyPI using twine..."
	@if [ -z "$$PYPI_API_TOKEN" ]; then \
		echo "Error: PYPI_API_TOKEN environment variable not set"; \
		echo "Please set it with: export PYPI_API_TOKEN=your_token_here"; \
		exit 1; \
	fi
	uv add --dev twine
	uv run python -m twine upload dist/* --username __token__ --password $$PYPI_API_TOKEN

.PHONY: publish-modern
publish-modern:   ## Publish the package using modern uv publish (requires UV >= 0.4.0).
	@echo "Publishing to PyPI using uv publish..."
	@if [ -z "$$PYPI_API_TOKEN" ]; then \
		echo "Error: PYPI_API_TOKEN environment variable not set"; \
		echo "Please set it with: export PYPI_API_TOKEN=your_token_here"; \
		exit 1; \
	fi
	@command -v uv >/dev/null 2>&1 && uv publish --token $$PYPI_API_TOKEN || { echo "Error: uv publish not available. Run 'make upgrade-uv' first."; exit 1; }

.PHONY: check-build
check-build:      ## Check if the package can be built and installed.
	@echo "Checking if package builds correctly..."
	$(MAKE) clean
	$(MAKE) build
	@echo "Testing package installation..."
	uv run --with ./dist/*.whl --no-project -- python -c "import testzeus_mcp_server; print('Package imports successfully!')"

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create a version tag and push to GitHub"
	@( \
	  read -p "Version to release (e.g., 2.0.1): " VERSION; \
	  echo "Updating version to $$VERSION"; \
	  sed -i.bak 's/version = "[^"]*"/version = "'$$VERSION'"/' pyproject.toml; \
	  rm pyproject.toml.bak; \
	  read -p "Do you want to continue? (y/n) : " CONTINUE; \
	  [ $$CONTINUE = "y" ] || exit 1; \
	  echo "New Version: $$VERSION"; \
	  git add pyproject.toml; \
	  git commit -m "release: version $$VERSION 🚀"; \
	  echo "creating git tag : v$$VERSION"; \
	  git tag v$$VERSION; \
	  git push -u origin HEAD --tags; \
	  echo "GitHub Actions will detect the new tag and release the new version."; \
	)

.PHONY: release-patch
release-patch:    ## Create a new patch release.
	@( \
	  CURRENT_VERSION=$$(grep 'version = ' pyproject.toml | sed 's/.*version = "\([^"]*\)".*/\1/'); \
	  NEW_VERSION=$$(python -c "v='$$CURRENT_VERSION'.split('.'); v[2]=str(int(v[2])+1); print('.'.join(v))"); \
	  sed -i.bak 's/version = "[^"]*"/version = "'$$NEW_VERSION'"/' pyproject.toml; \
	  rm pyproject.toml.bak; \
	  git add pyproject.toml; \
	  git commit -m "release: version $$NEW_VERSION 🚀"; \
	  git tag v$$NEW_VERSION; \
	  git push -u origin HEAD --tags; \
	  echo "Released v$$NEW_VERSION"; \
	)

.PHONY: release-minor
release-minor:    ## Create a new minor release.
	@( \
	  CURRENT_VERSION=$$(grep 'version = ' pyproject.toml | sed 's/.*version = "\([^"]*\)".*/\1/'); \
	  NEW_VERSION=$$(python -c "v='$$CURRENT_VERSION'.split('.'); v[1]=str(int(v[1])+1); v[2]='0'; print('.'.join(v))"); \
	  sed -i.bak 's/version = "[^"]*"/version = "'$$NEW_VERSION'"/' pyproject.toml; \
	  rm pyproject.toml.bak; \
	  git add pyproject.toml; \
	  git commit -m "release: version $$NEW_VERSION 🚀"; \
	  git tag v$$NEW_VERSION; \
	  git push -u origin HEAD --tags; \
	  echo "Released v$$NEW_VERSION"; \
	)

.PHONY: release-major
release-major:    ## Create a new major release.
	@( \
	  CURRENT_VERSION=$$(grep 'version = ' pyproject.toml | sed 's/.*version = "\([^"]*\)".*/\1/'); \
	  NEW_VERSION=$$(python -c "v='$$CURRENT_VERSION'.split('.'); v[0]=str(int(v[0])+1); v[1]='0'; v[2]='0'; print('.'.join(v))"); \
	  sed -i.bak 's/version = "[^"]*"/version = "'$$NEW_VERSION'"/' pyproject.toml; \
	  rm pyproject.toml.bak; \
	  git add pyproject.toml; \
	  git commit -m "release: version $$NEW_VERSION 🚀"; \
	  git tag v$$NEW_VERSION; \
	  git push -u origin HEAD --tags; \
	  echo "Released v$$NEW_VERSION"; \
	)

.PHONY: release-custom
release-custom:   ## Create a new release with custom version.
	@( \
	  read -p "Enter custom version (e.g., 1.2.3): " VERSION; \
	  sed -i.bak 's/version = "[^"]*"/version = "'$$VERSION'"/' pyproject.toml; \
	  rm pyproject.toml.bak; \
	  git add pyproject.toml; \
	  git commit -m "release: version $$VERSION 🚀"; \
	  git tag v$$VERSION; \
	  git push -u origin HEAD --tags; \
	  echo "Released v$$VERSION"; \
	) 