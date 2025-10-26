from quart import Blueprint, request, redirect, session, jsonify

from services.dbService import *
from services.discordService import *

router = Blueprint("authApi", __name__, url_prefix="/")

@router.route("/login", methods=["GET"])
async def login():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return redirect("/")

    exchangeRes = await exchangeToken(code)
    if not exchangeRes:
        return "로그인 실패", 401
    
    userInfo = await getUserInfo(exchangeRes["access_token"])
    if not userInfo:
        return "로그인 실패", 401
    
    userId = userInfo["id"]
    con, cur = await loadDB()
    await cur.execute("SELECT * FROM users WHERE id = ?", (userId,))
    exists = await cur.fetchone()

    if not exists:
        await cur.execute("INSERT INTO users (id, refresh_token) VALUES (?, ?)", (userId, exchangeRes["refresh_token"]))
    else:
        await cur.execute("UPDATE users SET refresh_token = ? WHERE id = ?", (exchangeRes["refresh_token"], userId,))
    await con.commit()
    await closeDB(con, cur)

    session["username"] = userId

    if state:
        return redirect(f"{state}")
    return redirect("/dashboard")

@router.route("/logout", methods=["GET", "POST"])
async def logout():
    session.clear()
    return jsonify({"status": "success"}), 201