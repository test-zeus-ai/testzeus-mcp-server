.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

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
	uv run ruff check testzeus_mcp_server/
	uv run ruff check tests/ 2>/dev/null || echo "No tests directory found"

.PHONY: type-check
type-check:       ## Run mypy type checker.
	uv run mypy testzeus_mcp_server/

.PHONY: test
test: lint type-check  ## Run tests.
	uv run pytest -v --junit-xml=test_output.xml -l --tb=short --maxfail=1 tests/ 2>/dev/null || echo "No tests directory found"

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
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

.PHONY: build
build:            ## Build package.
	uv build

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

.PHONY: publish
publish:          ## Publish the package to PyPI.
	@echo "Publishing to PyPI ..."
	@uv publish --token $${PYPI_API_TOKEN} 