import traceback

from quart import Blueprint, request, session, render_template, redirect, jsonify

from bot import bot

from models.ticketModel import *

import services.configService as settings

from services.discordService import *

router = Blueprint("ticketApiRouter", __name__, url_prefix="/")

@router.route("/<guildId>", methods=["GET"])
async def getTicketList(guildId):
    if not settings.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
        
    tickets = await Ticket.findByGuildId(guildId)

    if not tickets:
        return jsonify({"status": "success", "data": []})

    query = request.args.get("query", "").lower()
    pageStr = request.args.get("page", 1)
    filteredTickets = [ticket for ticket in tickets if ticket.status == "saved"]

    try:
        page = int(pageStr)
    except ValueError:
        return jsonify({"error": "page must be an integer!"}), 400

    if page < 1:
        return jsonify({"error": "page must be 1 or greater!"}), 400

    if query:
        filteredTickets = [ticket for ticket in filteredTickets if query == ticket.user or query in str(await getUsername(ticket.user))]

    start = (page - 1) * 10
    end = start + 10
    paginatedTickets = filteredTickets[start:end]
    totalPages = (len(filteredTickets) + 9) // 10

    return jsonify({"data": [{
        "guild_id": str(ticket.guild),
        "username": str(await getUsername(ticket.user)),
        "channel_id": str(ticket.channel),
        "ticket_status": ticket.status,
        "open_time": ticket.openTime,
        "close_time": ticket.closeTime.strftime("%Y-%m-%d %H:%M") if ticket.closeTime else None
    } for ticket in paginatedTickets],
    "total_pages": totalPages,
    "current_page": page})