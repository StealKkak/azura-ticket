from quart import Blueprint

import services.configService as settings

from .mainRouter import router as mainRouter
from .apiRoutes.index import router as apiRouter
from .ticketRouter import router as ticketRouter

router = Blueprint("root", __name__, url_prefix="/")

if not settings.api_only:
    router.register_blueprint(mainRouter, url_prefix="/")

router.register_blueprint(apiRouter, url_prefix="/api")
router.register_blueprint(ticketRouter, url_prefix="/ticket")