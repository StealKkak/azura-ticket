from quart import Blueprint, request

router = Blueprint("authApi", __name__, url_prefix="/")

@router.route("/login", methods=["GET"])
async def login():
    return "/api/auth/login"