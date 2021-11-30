import logging
from aiohttp.web import json_response
from tortoise.transactions import atomic


logger = logging.getLogger(__name__)


async def get_health_liveness(request):
    return json_response(status=200, data={
        'message': 'The service is healthy based on liveness healthcheck'})


async def get_health_readiness(request):
    return json_response(status=200, data={'message': 'The service is healthy based on readiness healthcheck'})


async def create_test_data(request):

    @atomic()
    async def create():
        from main.src.models import BotConfig, BotOrder, User, Role, Permission, Api, Plan, Subscription
        permission = await Permission.create(
            service="test"
        )
        role = await Role.create(
            permission=permission
        )
        permission.role = role
        await permission.save()
        user = await User.create(
            user_name="test2",
            email="test2",
            password="test2",
            role=role
        )
        user = await User.first()
        api = await Api.create(
            user=user,
            api_key="test3",
            api_secret="test3",
            exchange="binance",
        )
        bot_config = await BotConfig.create(
            test=False,
            duplicate=False,
            target="FUTURE",
            quantity=10,
            api=api,
        )
        bot_order = await BotOrder.create(
            channel="test2",
            user=user,
            config=bot_config
        )
        bot_config.bot = bot_order
        await bot_config.save()
        plan = await Plan.create(
            name="test",
            channel="ROSE",
            price=50,
            day=30
        )
        subscription = await Subscription.create(
            user=user,
            plan=plan
        )
        assert subscription is not None
    try:
        await create()
        return json_response(
            status=200,
            data={},
        )
    except Exception as e:
        logger.error("bot singal error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
