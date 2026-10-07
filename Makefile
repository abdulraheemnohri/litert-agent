.PHONY: install test lint format build clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

format:
	ruff format src tests

build:
	python -m build --wheel

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
