.PHONY: install install-dev install-browser test lint format build clean

install:
	python scripts/bootstrap.py

install-dev:
	python scripts/bootstrap.py --dev

install-browser:
	python scripts/bootstrap.py --browser

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
