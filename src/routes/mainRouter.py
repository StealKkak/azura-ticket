from quart import Blueprint, redirect, render_template

router = Blueprint("main", __name__, url_prefix="/")

@router.route("/")
async def index():
    return redirect("/dashboard")

@router.route("/dashboard")
async def guildList():
    return "/dashboard"

@router.route("/dashboard/<parameter>")
async def dashboard(parameter):
    return f"/dashboard/{parameter}"