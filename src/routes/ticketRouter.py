import os
from pathlib import Path

from quart import Blueprint, redirect, render_template, session, send_from_directory, abort

import services.configService as settings
from services.discordService import isGuildAdmin

from models.ticketModel import Ticket

router = Blueprint("ticket", __name__, url_prefix="/")

BASE_DIR = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"

@router.route("/<guildId>/<channelId>", methods=["GET"])
async def showTranscript(guildId, channelId):
    ticket = await Ticket.findByChannelId(channelId)
    
    if not ticket:
        return await render_template("error/404.html"), 404
    
    if str(ticket.guild) != guildId:
        return await render_template("error/404.html"), 404
    
    username = session.get("username")
    if not username:
        return redirect(f"/login?from={guildId}/{channelId}")
    
    if not int(username) == ticket.user and not await isGuildAdmin(guildId, username):
        return await render_template("error/403.html"), 403
    
    file_path = TRANSCRIPTS_DIR / str(guildId) / f"{channelId}.html"
    if not os.path.exists(file_path):\
        abort(404)
    return await send_from_directory(file_path.parent, file_path.name)