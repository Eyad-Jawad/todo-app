import asyncio

from todo_app.ui import interface


def main() -> None:
    asyncio.run(interface())


if __name__ == "__main__":
    main()
