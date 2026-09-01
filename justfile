tests:
    uv run pytest
    uv run black --check .
    uv run ruff --check .
    uv run mypy .

test:
    uv run pytest

lint:
    uv run black .
    uv run ruff --check --fix .
