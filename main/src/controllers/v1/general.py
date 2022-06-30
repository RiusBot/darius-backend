import secrets
import logging
from datetime import datetime
from aiohttp.web import json_response
from tortoise.transactions import atomic
from main.src.core.stats import _get_stats
from main.src.exception import BackendException
from main.src.utils import error_handler, input_filter
from main.src.models import Provider, RoiLog


logger = logging.getLogger(__name__)


async def get_health_liveness(request):
    return json_response(status=200, data={
        'message': 'The service is healthy based on liveness healthcheck'
    })


async def get_health_readiness(request):
    return json_response(status=200, data={
        'message': 'The service is healthy based on readiness healthcheck'
    })


@error_handler()
@input_filter()
async def get_stats(request: dict):
    uid = request['uid']
    logger.info("Get Riusbot stats")
    stats = await _get_stats(uid)
    return stats


@error_handler()
@input_filter()
async def roilog(request: dict):
    logger.info("Log provider roi")
    provider = request['provider']
    access_token = request['access_token']
    roi = request['roi']
    timestamp = request['timestamp']

    provider = await Provider.filter(is_del=False, name=provider).first()
    if provider is None:
        raise BackendException("Provider not found")
    if not secrets.compare_digest(provider.access_token, access_token):
        raise BackendException("invalid access token")

    await RoiLog.create(
        provider=provider,
        roi=roi,
        timestamp=datetime.fromtimestamp(timestamp),
    )
    return {"message": 'success'}


async def clean_no_subscription_bot(request):

    from datetime import datetime, timedelta
    from main.src.models import BotOrder

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


async def check_rebate(api):
    import ccxt.async_support as ccxt
    from main.src.core.cipher import decrypt
    try:
        api_key = api.api_key
        api_secret = decrypt(api.api_key, api.api_secret)
    except Exception:
        return False
    exchange = ccxt.binance({
        'apiKey': api_key,
        "secret": api_secret,
        "options": {
            "defaultType": 'spot',
        }
    })
    ifNewUser = await exchange.sapi_get_apireferral_ifnewuser(params={'apiAgentCode': 'V9ZBVGB7'})
    await exchange.close()
    if ifNewUser['rebateWorking'] and ifNewUser['ifNewUser']:
        return True
    return False


@atomic()
async def create_test_data(request):
    from main.src.models import BotConfig, BotOrder, User, Role, Permission, Api, Plan, Subscription, Referral

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

        import asyncio
        from main.src.core.referral import create_user_referral

        coroutines = []
        async for user in User.filter(is_del=False, referral=None).prefetch_related('referral').all():
            referral = await create_user_referral(user.referrer)
            referral.referral_code = user.referral_code
            referral.user = user
            user.referral = referral
            referrer = await Referral.filter(referral_code=user.referrer).select_for_update().first()
            if referrer:
                referrer.register_count += 1
                coroutines.append(referrer.save())

            coroutines.append(referral.save())
            coroutines.append(user.save())

        await asyncio.gather(*coroutines)
        logger.info("Complete")

#         import pytz
#         import datetime
#         import pandas as pd

#         df = pd.read_csv("../cta_usdt.csv")
#         df["Close_time"] = pd.to_datetime(df["Close_time"])
#         df = df[df["Close_time"] > datetime.datetime(2021, 1, 1).replace(tzinfo=pytz.utc)]
#         df.head()

#         message_list = []

#         for i in range(len(df)):

#             row = df.iloc[i]
#             timestamp = row["Close_time"]

#             for symbol, quantity in zip(df.columns[1:], row[1:]):
#                 if not pd.isna(quantity) and quantity:
#                     action = "BUY" if quantity > 0 else "SELL"

#                     message = Message(
#                         channel="CTA",
#                         content="",
#                         symbol=symbol,
#                         action=action,
#                         message_timestamp=timestamp.isoformat(),
#                         recieve_timestamp=timestamp.isoformat(),
#                         quantity=float(quantity),
#                         entry=None,
#                         stop_loss=None,
#                         take_profit=None,
#                         price=None
#                     )
#                     message_list.append(message)

#             if len(message_list) > 100:
#                 # await Message.bulk_create(message_list)
#                 message_list = []

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
