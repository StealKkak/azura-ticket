import traceback

import discord

from quart import Blueprint, jsonify, session, request


from models.ticketTypeModel import *

import services.configService as settigns

from services.discordService import *

from bot import bot

router = Blueprint("guildApiRouter", __name__, url_prefix="/")

@router.route("/<guildId>/ticket-settings", methods=["GET", "PUT"])
async def getTicketSettings(guildId):
    if not settigns.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
        
    tickets = await TicketType.findByGuildId(guildId)

    if request.method == "GET":
        if not tickets:
            ticket = await TicketType.createInstance(guildId, "기본 티켓", True, 1, None, None, None, None)

            return jsonify({
                "data": [
                    {
                        "name": "기본 티켓"
                    }
                ]
            })
        
        return jsonify({"data": [
            {
                "name": ticket.name
            } for ticket in tickets
        ]})
    
    elif request.method == "PUT":
        body = await request.get_json()
        name = body.get("name")
        description = body.get("description")

        if not name:
            return jsonify({"error": "티켓 이름을 입력해주세요!"})

        if not name:
            return jsonify({"error": "Missing required paramter: name"}), 400
        
        try:
            await TicketType.createInstance(guildId, name, description, True, 0, [])
            return jsonify({"message": "success"}), 201
        except ValueError:
            return jsonify({"error": "이미 존재하는 티켓 이름입니다!"}), 400
        except:
            traceback.print_exc()
            return jsonify({"error": "알 수 없는 오류입니다!"}), 500

@router.route("/<guildId>/ticket-settings/<index>", methods=["GET", "POST", "DELETE"])
async def handelTicketSetting(guildId, index):
    if not settigns.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
        
    try:
        index = int(index)
    except:
        return jsonify({"error": "index must be integer!"}), 400
    
    tickets = await TicketType.findByGuildId(guildId)
    if index > len(tickets) - 1:
        return jsonify({"error": "index out of range!"}), 400
    
    ticket = tickets[index]
    
    if request.method == "GET":
        return jsonify({"data": {
            "name": ticket.name,
            "description": ticket.description,
            "survey1": ticket.survey1,
            "survey2": ticket.survey2,
            "survey3": ticket.survey3,
            "role": ticket.role,
            "dup_ticket": bool(ticket.dupTicket),
            "ticket_category": str(ticket.ticketCategory),
            "closed_ticket_category": str(ticket.closedTicketCategory),
            "user_close": bool(ticket.userClose)
        }})
    
    if request.method == "POST":
        body = await request.get_json()

        roles = body.get("roles")
        if roles and len(roles) > 0:
            for role in roles:
                try:
                    int(role)
                except:
                    return jsonify({"역할 값은 양수여야 합니다!"}), 400

        try:
            ticket.name = body.get("name")
            ticket.description = body.get("description")
            ticket.survey1 = body.get("survey1")
            ticket.survey2 = body.get("survey2")
            ticket.survey3 = body.get("survey3")
            ticket.role = body.get("role")
            ticket.dupTicket = bool(body.get("dup_ticket"))
            ticket.ticketCategory = body.get("ticket_category")
            ticket.closedTicketCategory = body.get("closed_ticket_category")
            ticket.userClose = bool(body.get("user_close"))
            await ticket.save()
        except ValueError:
            return jsonify({"error": "티켓 이름은 중복될 수 없습니다!"}), 400
        except NameError:
            return jsonify({"error": "티켓 이름을 입력해주세요!"}), 400
        except:
            traceback.print_exc()
            return jsonify({"error": "알 수 없는 서버 오류입니다!"}), 500
        
        return jsonify({"message": "success"}), 201
    
    if request.method == "DELETE":
        await ticket.delete()
        return jsonify({"message": "success"}), 201
    
@router.route("/<guildId>/roles", methods=["GET"])
async def getGuildRoles(guildId):
    if not settigns.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
    
    try:
        roles = await bot.http.get_roles(guildId)
    except discord.Forbidden:
        return jsonify({"error": "봇이 권한이 없어 역할을 가져올 수 없습니다!"}), 500
    except discord.NotFound:
        return jsonify({"error": "봇이 해당 서버에 존재하지 않아 역할을 가져올 수 없습니다!"}), 404
    
    return jsonify({"message": "success", "data": roles})

@router.route("/<guildId>/channels", methods=["GET"])
async def getGuildChannels(guildId):
    if not settigns.api_only:
        username = session.get("username")
        if not username:
            return jsonify({"error": "Unauthorized"}), 401
        
        if not await isGuildAdmin(guildId, username):
            return jsonify({"error": "You don't have permission to perform this action"}), 403
    
    try:
        channels = await bot.http.get_all_guild_channels(guildId)
    except discord.Forbidden:
        return jsonify({"error": "봇이 권한이 없어 채널을 가져올 수 없습니다!"}), 500
    except discord.NotFound:
        return jsonify({"error": "봇이 해당 서버에 존재하지 않아 채널을 가져올 수 없습니다!"}), 404
    
    return jsonify({"message": "success", "data": channels})