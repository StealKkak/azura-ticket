import os

from quart import Blueprint, redirect, render_template, session, request

import services.configService as settings

from services.discordService import isGuildAdmin

router = Blueprint("main", __name__, url_prefix="/")

clientId = os.getenv("CLIENT_ID")
domain = os.getenv("DOMAIN")
serviceName = settings.serviceName

@router.route("/")
async def index():
    return await render_template("index.html", serviceName=serviceName, clientId=clientId, login=session.get("username"))

@router.route("/logout")
async def logout():
    session.clear()
    return redirect("/")

@router.route("/login")
async def login():
    if session.get("login"):
        return redirect("/")
    else:
        url = f"https://discord.com/oauth2/authorize?client_id={clientId}&response_type=code&redirect_uri={domain}%2Fapi%2Fauth%2Flogin&scope=identify+guilds&prompt=none"
        state = request.args.get("from")
        if state:
            url += f"&state={state}"
        return redirect(url)
    
@router.route("/terms")
async def terms():
    return redirect("https://azura.cfx.kr/terms")

@router.route("/dashboard")
async def guildList():
    if not session.get("username"):
        return redirect(f"https://discord.com/oauth2/authorize?client_id={clientId}&response_type=code&redirect_uri={domain}%2Fapi%2Fauth%2Flogin&scope=identify+guilds&prompt=none")
    else:
        return await render_template("dashboard.html", serviceName=settings.serviceName, username=session["username"])

@router.route("/dashboard/<parameter>")
async def dashboard(parameter):
    username = session.get("username")

    if not username:
        return redirect("/")
    
    if not await isGuildAdmin(parameter, username):
        return await render_template("error/403.html"), 403

    return await render_template("setting.html", serviceName=settings.serviceName)