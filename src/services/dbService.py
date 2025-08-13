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
    await cur.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, guild TEXT, user TEXT, channel TEXT UNIQUE, ticket_status TEXT NOT NULL DEFAULT \"open\", open_time DATETIME, close_time DATETIME)")
    await cur.execute("CREATE TABLE IF NOT EXISTS guilds (id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '티켓 열기', description TEXT NOT NULL DEFAULT '아래 버튼을 눌러 문의를 위한 개인 채널을 생성하세요!', button_label TEXT NOT NULL DEFAULT '💌ㅣ티켓 열기')")
    await cur.execute("CREATE TABLE IF NOT EXISTS ticket_settings (guild TEXT, name TEXT, survey1 TEXT, survey2 TEXT, survey3 TEXT role TEXT, user_close INTEGER NOT NULL DEFAULT 0, max_ticket INTEGER NOT NULL DEFAULT 0)")
    await con.commit()
    await closeDB(con, cur)

loop = asyncio.get_event_loop()
loop.create_task(initDB())