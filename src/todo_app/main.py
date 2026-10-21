# TODO: Add .env.example file.
# TODO: Add tests to the new stuff

# FIXME: I don't like some https error codes in auth.py
# FIXME: The pydantic settings defaults for db stuff to support local stuff
# FIXME: Tests

import asyncio

from todo_app.ui import interface


def main() -> None:
    asyncio.run(interface())


if __name__ == "__main__":
    main()
