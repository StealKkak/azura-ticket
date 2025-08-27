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
    query = request.args.get("query", "").lower()
    pageStr = request.args.get("page", 1)
    filteredTickets = [ticket for ticket in tickets if ticket.status == "saved"]

    try:
        page = int(pageStr)
    except ValueError:
        return jsonify({"error": "page must be an integer!"}), 400

    if page < 1:
        return jsonify({"error": "page must be 1 or greater!"}), 400

    try:
        guild = await bot.fetch_guild(guildId)
        userList = {user.id : user.name async for user in guild.fetch_members(limit=None)}

        con, cur = await loadDB()
        users = list(userList.items())
        await cur.executemany("INSERT OR REPLACE INTO usernames VALUES (?, ?)", users)
        await con.commit()

        await cur.execute("SELECT * FROM usernames")
        await closeDB(con, cur)
    except:
        traceback.print_exc()

    con, cur = await loadDB()
    for ticket in filteredTickets:
        if not userList.get(ticket.user):
            await cur.execute("SELECT * FROM usernames WHERE id = ?", (int(ticket.user),))
            row = await cur.fetchone()
            userList[int(row["id"])] = row["name"]
    await closeDB(con, cur)

    if query:
        filteredTickets = [ticket for ticket in filteredTickets if query == ticket.user or  query in str(userList.get(ticket.user))]

    start = (page - 1) * 10
    end = start + 10
    paginatedTickets = filteredTickets[start:end]
    totalPages = (len(filteredTickets) + 9) // 10

    return jsonify({"data": [{
        "guild_id": str(ticket.guild),
        "username": str(userList.get(ticket.user, ticket.user)),
        "channel_id": str(ticket.channel),
        "ticket_status": ticket.status,
        "open_time": ticket.openTime,
        "close_time": ticket.closeTime.strftime("%Y-%m-%d %H:%M") if ticket.closeTime else None
    } for ticket in paginatedTickets],
    "total_pages": totalPages,
    "current_page": page})