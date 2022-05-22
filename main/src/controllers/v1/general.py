import logging
from aiohttp.web import json_response
from tortoise.transactions import atomic
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char
from main.src.core.stats import _get_stats


logger = logging.getLogger(__name__)


async def get_health_liveness(request):
    return json_response(status=200, data={
        'message': 'The service is healthy based on liveness healthcheck'})


async def get_health_readiness(request):
    return json_response(status=200, data={'message': 'The service is healthy based on readiness healthcheck'})


async def get_stats(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload['uid']
        stats = await _get_stats(uid)
        return json_response(
            status=200,
            data=stats,
        )
    except Exception as e:
        logger.error("avaiable balance error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def clean_no_subscription_bot(request):

    from datetime import datetime, timedelta
    from main.src.models import BotConfig, BotOrder, User, Role, Permission, Api, Plan, Subscription, Message

    async for bot in BotOrder.filter(is_del=False).prefetch_related("user__telegram_user"):

        user = bot.user
        has_subscription = await user.subscription_user.filter(is_del=False, plan__channel=bot.channel).exists()
        if has_subscription:
            continue

        telegram = await bot.user.telegram_user.filter(is_del=False).first()

        if not telegram:
            bot.is_del = True
            await bot.save()
        elif (telegram.created_at + timedelta(days=30)).timestamp() < datetime.now().timestamp():
            # not trial period
            bot.is_del = True
            await bot.save()
    
    return json_response(
        status=200,
        data={},
    )

    
async def create_test_data(request):
    from main.src.models import BotConfig, BotOrder, User, Role, Permission, Api, Plan, Subscription, Message

    @atomic()
    async def create():
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
        # await create()
        return json_response(
            status=200,
            data={},
        )
    except Exception as e:
        logger.error("create test data error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
