# TODO: Use dependcy injection or whatever for get user 
# and for get session as well, or for this use state.pool or something.
# TODO: Add .env.example file
# TODO: Set the /api/token endpoint
# TODO: Put "ref": bool, in mind in jwts

import asyncio

from todo_app.ui import interface


def main() -> None:
    asyncio.run(interface())


if __name__ == "__main__":
    main()
