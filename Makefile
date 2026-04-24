.PHONY: build check clean-build format format-check lint test typecheck verify-dist

PYTHON ?= python
UV_CACHE_DIR ?= .uv-cache

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run $(PYTHON) -m unittest discover -s tests

typecheck:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run mypy

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check src tests

format:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format src tests

format-check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check src tests

clean-build:
	rm -rf build src/hermes_membase.egg-info
	mkdir -p dist
	find dist -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \) -delete

build: clean-build
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run $(PYTHON) -m build

verify-dist: build
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run twine check dist/*

check: typecheck lint format-check test verify-dist
