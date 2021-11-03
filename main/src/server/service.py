import logging

from aiohttp import web
from connexion import AioHttpApp

from main.src.config import app_config
from main.src.controllers.v1.general import get_health_liveness, get_health_readiness
from main.src.db import start_db_connection, close_db_connection

logger = logging.getLogger(__name__)


async def init_tortoise(app):
    # Starup phase
    logger.info('Starting DB connection')
    await start_db_connection(app_config)
    yield

    # Cleanup phase
    logger.info('Shutting down DB connection')
    await close_db_connection()


def main():
    app = AioHttpApp(__name__, port=app_config['PORT'], specification_dir='openapi/')

    app.add_api('specification.yaml', pass_context_arg_name='request')

    app.app.router.add_routes([
        web.get('/health_liveness', get_health_liveness),
        web.get('/health_readiness', get_health_readiness),
    ])
    app.app.cleanup_ctx.append(init_tortoise)
    app.run()


if __name__ == '__main__':
    main()
