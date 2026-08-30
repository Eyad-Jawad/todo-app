from todo_app.db import init_db, get_session

async def interface(user_id: int = 0):
    await init_db()
    
    async with get_session() as session:
        print(f"User: {user_id}")
