import asyncio

from aiosqlite import connect, Row

async def loadDB(path:str="database.db"):
    con = await connect("db/" + path)
    con.row_factory = Row
    cur = await con.cursor()
    return con, cur

async def closeDB(con, cur):
    await cur.close()
    await con.close()
    return

async def initDB():
    con, cur = await loadDB()
    await cur.execute("CREATE TABLE IF NOT EXISTS tickets (id PRIMARY KEY AUTOINCREMENT, ticket_id TEXT UNIQUE, guild TEXT, user TEXT, ticket_status TEXT NOT NULL DEFAULT open, open_time DATETIME, close_time DATETIME)")
    await con.commit()
    await closeDB(con, cur)

asyncio.run(initDB())