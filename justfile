all:
    ENV_FILE=.env.testing uv run pytest
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy .
    echo "Everything looks good!"

test: # for local testing
    ENV_FILE=.env.testing uv run pytest

lint:
    uv run ruff format .
    uv run ruff check --fix .

typing:
    uv run mypy .
