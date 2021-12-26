import os
import logging

from connexion import AioHttpApp
import aiohttp_cors
from tortoise.contrib.aiohttp import register_tortoise
from firebase_admin import initialize_app

from main.src.config import app_config, db_config, configure_logging


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


def main():
    configure_logging()

    options = {"swagger_ui": (usingProjectId == "local")}
    app = AioHttpApp(__name__, port=app_config['PORT'], specification_dir='openapi/', options=options)
    cors_allow_origin_dict = {
        domain: aiohttp_cors.ResourceOptions(
            allow_headers='*',
            allow_methods='*'
        )
        for domain in app_config['CORS_ALLOW_ORIGIN']
    }
    cors = aiohttp_cors.setup(app.app, defaults=cors_allow_origin_dict)

    app.add_api(
        'specification.yaml',
        pass_context_arg_name='request',
        strict_validation=True,
        validate_responses=True,
        auth_all_paths=False,
    )
    for route in list(app.app.router.routes()):
        cors.add(route)

    register_tortoise(
        app.app,
        db_config,
    )

    initialize_app()
    app.run()


if __name__ == '__main__':
    main()
