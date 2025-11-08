from quart import Blueprint, session, jsonify, request

import services.configService as settings

from services.discordService import *

router = Blueprint("userApi", __name__, url_prefix="/")

@router.route("/me/guilds", methods=["GET"])
async def getServerList():
    userId = session.get("username")
    refresh = True if request.args.get("refresh") == "true" else False

    if not userId:
        return jsonify({"error": "Unauthorized"}), 401 if not settings.api_only else jsonify({"error": "Missing required parameters"}), 400
    
    result = await getUserGuilds(userId, refresh)
    if not result:
        return jsonify({"error": "No Data Found"}), 404
    
    return jsonify({"message": "success", "data": result})