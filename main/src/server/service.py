import logging

from aiohttp import web
from connexion import AioHttpApp
from tortoise.contrib.aiohttp import register_tortoise

from main.src.config import app_config, db_config
from main.src.controllers.v1.general import get_health_liveness, get_health_readiness

logger = logging.getLogger(__name__)


def main():
    app = AioHttpApp(__name__, port=app_config['PORT'], specification_dir='openapi/')

    app.add_api('specification.yaml', pass_context_arg_name='request')

    app.app.router.add_routes([
        web.get('/health_liveness', get_health_liveness),
        web.get('/health_readiness', get_health_readiness),
    ])
    register_tortoise(app.app, db_config, generate_schemas=True)
    app.run()


if __name__ == '__main__':
    main()
