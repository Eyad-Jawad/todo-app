from . import ui as ui
import asyncio


def main() -> None:
    asyncio.run(ui.interface())
