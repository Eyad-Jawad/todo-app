all:
    uv run pytest
    uv run black --check .
    uv run ruff check .
    uv run mypy .
    echo "Everything looks good!"

test: # for local testing
    uv run pytest -k "not test_integration"

lint:
    uv run black .
    uv run ruff check --fix .

typing:
    uv run mypy .
