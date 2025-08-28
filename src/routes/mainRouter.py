import os

from quart import Blueprint, redirect, render_template, session

import services.configService as settings

from services.discordService import isGuildAdmin

router = Blueprint("main", __name__, url_prefix="/")

@router.route("/")
async def index():
    return redirect("/dashboard")

@router.route("/logout")
async def logout():
    session.clear()
    return redirect("/")

@router.route("/dashboard")
async def guildList():
    if not session.get("username"):
        return redirect(f"https://discord.com/oauth2/authorize?client_id={os.getenv("CLIENT_ID")}&response_type=code&redirect_uri={os.getenv("DOMAIN")}%2Fapi%2Fauth%2Flogin&scope=identify+guilds&prompt=none")
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