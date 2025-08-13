from quart import Blueprint

router = Blueprint("userApi", __name__, url_prefix="/")

router.route("/serverlist", methods=["GET"])
async def serverList():
    return "/api/user/serverlist"