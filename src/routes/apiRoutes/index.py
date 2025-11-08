from quart import Blueprint, jsonify

from .authApiRouter import router as authApiRouter
from .userApiRouter import router as userApiRouter
from .ticketApiRouter import router as ticketApiRouter
from .guildApiRouter import router as guildApiRouter

import services.configService as settings

router = Blueprint("api", __name__, url_prefix="/")

if not settings.api_only:
    router.register_blueprint(authApiRouter, url_prefix="/auth")
router.register_blueprint(userApiRouter, url_prefix="/users")
router.register_blueprint(ticketApiRouter, url_prefix="/tickets")
router.register_blueprint(guildApiRouter, url_prefix="/guilds")