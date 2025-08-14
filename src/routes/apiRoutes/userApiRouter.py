from quart import Blueprint, session, jsonify, request

import services.configService as settings

from services.discordService import *

router = Blueprint("userApi", __name__, url_prefix="/")

@router.route("/getserverlist", methods=["POST"])
async def getServerList():
    if settings.api_only:
        body = await request.get_json()

    userId = session.get("username") if not settings.api_only else body.get("username")

    if not userId:
        return jsonify({"error": "Unauthorized"}), 401 if not settings.api_only else jsonify({"error": "Missing required parameters"}), 400
    
    result = await getUserGuilds(userId)
    if not result:
        return jsonify({"error", "Internal server error"}), 500
    
    if not result.get("success"):
        error = result.get("error")
        code = error.get("code", 500)
        message = error.get("message", "Internal server error")
        return jsonify({"error": message}), code
    
    data = result.get("data")
    return jsonify(data)

@router.route("/refreshserverlist", methods=["POST"])
async def refreshServerList():
    if settings.api_only:
        body = await request.get_json()

    userId = session.get("username") if not settings.api_only else body.get("username")

    if not userId:
        return jsonify({"error": "Unauthorized"}), 401 if not settings.api_only else jsonify({"error": "Missing required parameters"}), 400

    result = await refreshGuildList(userId)
    if not result.get("success", False):
        error = result.get("error", {})
        code = error.get("code", 500)
        message = error.get("message", "Unknown error")
        return jsonify({"error": message}), code

    return jsonify(result.get("data", [])), 200