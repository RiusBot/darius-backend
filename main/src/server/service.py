import logging

from aiohttp import web
from connexion import AioHttpApp

from main.src.controllers.v1.general import get_health_liveness

logger = logging.getLogger(__name__)


def main():
    app = AioHttpApp(__name__, port=8080, specification_dir='openapi/')

    app.add_api('specification.yaml', pass_context_arg_name='request')

    app.app.router.add_routes([
        web.get('/health_liveness', get_health_liveness),
    ])
    app.run()


if __name__ == '__main__':
    main()
