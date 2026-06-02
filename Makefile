.DEFAULT_GOAL := check
PYTHON ?= python

.PHONY: install lint format format-check typecheck test check build clean

install:
	$(PYTHON) -m pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy

test:
	pytest

check: lint format-check typecheck test

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
