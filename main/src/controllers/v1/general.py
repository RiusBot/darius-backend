import logging
from aiohttp.web import json_response


async def get_health_liveness(request):
    return json_response(status=200, data={
        'message': 'The service is healthy based on liveness healthcheck'})


async def get_health_readiness(request):
    return json_response(status=200, data={'message': 'The service is healthy based on readiness healthcheck'})


async def create_test_data(request):
    try:
        from main.src.models import BotConfig, BotOrder, User, Role, Permission

        permission = await Permission.get_or_create(
            service="test"
        )

        role = await Role.get_or_create(
            permission=permission
        )

        permission.role = role
        await permission.save()

        user = await User.get_or_create(
            user_name="test",
            email="test",
            password="test",
            role=role
        )

        bot_config = await BotConfig.get_or_create(
            test=False,
            duplicate=False,
            target="SPOT",
            quantity=10,
        )

        bot_order = await BotOrder.get_or_create(
            channel="test",
            user=user,
            config=bot_config
        )

        bot_config.bot = bot_order
        await bot_config.save()

        return json_response(
            status=200,
            data={},
        )
    except Exception as e:
        logging.error("bot singal error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
