import logging

from aiohttp import web
from connexion import AioHttpApp
from tortoise.contrib.aiohttp import register_tortoise

from main.src.config import app_config, db_config
from main.src.controllers.v1.general import get_health_liveness, get_health_readiness

logger = logging.getLogger(__name__)


async def debug(request):
    import tortoise
    print(tortoise.Tortoise.apps)
    print(tortoise.Tortoise.apps.get('darius'))
    print(tortoise.Tortoise.apps.keys())

    from main.src.models import User
    users = await User.all()
    return web.json_response({"users": [str(user) for user in users]})


def main():
    app = AioHttpApp(__name__, port=app_config['PORT'], specification_dir='openapi/')

    app.add_api(
        'specification.yaml',
        pass_context_arg_name='request',
        strict_validation=True,
        validate_responses=True,
        auth_all_paths=False,
    )

    # Use openapi spec, no need add routes
    # app.app.router.add_routes([
    #     web.get('/health_liveness', get_health_liveness),
    #     web.get('/health_readiness', get_health_readiness),
    #     web.get("/", debug)
    # ])

    register_tortoise(
        app.app,
        db_config,
        # generate_schemas=True,
        # modules={"models": ["models"]},
    )

    app.run()


if __name__ == '__main__':
    main()
