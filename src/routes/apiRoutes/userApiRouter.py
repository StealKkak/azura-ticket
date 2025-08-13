from quart import Blueprint, session, jsonify

from services.discordService import *

router = Blueprint("userApi", __name__, url_prefix="/")

@router.route("/getserverlist", methods=["POST"])
async def getServerList():
    userId = session.get("username")

    if not userId:
        return jsonify({"error": "Unauthorized"}), 401
    
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
    userId = session.get("username")

    if not userId:
        return jsonify({"error": "Unauthorized"}), 401

    result = await refreshGuildList(userId)
    if not result.get("success", False):
        error = result.get("error", {})
        code = error.get("code", 500)
        message = error.get("message", "Unknown error")
        return jsonify({"error": message}), code

    return jsonify(result.get("data", [])), 200