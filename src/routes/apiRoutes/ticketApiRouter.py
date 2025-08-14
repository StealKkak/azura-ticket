from quart import Blueprint, request, session, render_template, redirect, jsonify

from models.ticketModel import *

import services.configService as settings

from services.discordService import *

router = Blueprint("ticketApiRouter", __name__, url_prefix="/")

@router.route("/<guildId>/tickets", methods=["GET"])
async def getTicketList(guildId):
    if not settings.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
        
    tickets = await Ticket.findByGuildId(guildId)
    query = request.args.get("query")
    filteredTickets = [ticket for ticket in tickets if ticket.status == "deleted"]

    if query:
        tickets = [ticket for ticket in tickets if query in ticket.name or ticket.user == query]

    return jsonify({"data": [{
        "guild_id": ticket.guild,
        "user_id": ticket.user,
        "channel_id": ticket.channel,
        "ticket_status": ticket.status,
        "open_time": ticket.openTime,
        "close_time": ticket.closeTime
    } for ticket in filteredTickets]})