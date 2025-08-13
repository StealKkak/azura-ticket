from quart import Blueprint, jsonify

from .authApiRouter import router as authApiRouter
from .userApiRouter import router as userApiRouter

import services.configService as settings

router = Blueprint("api", __name__, url_prefix="/")

if not settings.api_only:
    router.register_blueprint(authApiRouter, url_prefix="/auth")
router.register_blueprint(userApiRouter, url_prefix="/user")