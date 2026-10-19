# TODO: Use dependcy injection or whatever for get user.
# and for get session as well, or for this use state.pool or something..
# TODO: Add .env.example file.
# TODO: Set the /api/token endpoint.
# TODO: Put "ref": bool, in mind in jwts.
# TODO: Make use of the threadpool in /api/sign_up.
# TODO: Make a depenedncy injection for token stuff.
# FIXME: In the todo above, check the exp_date, cuz you don't do that now.
# FIXME: Possible mismatch in /api/token in exp_date, also it looks ugly.
# FIXME: I don't like some https error codes in auth.py

import asyncio

from todo_app.ui import interface


def main() -> None:
    asyncio.run(interface())


if __name__ == "__main__":
    main()
