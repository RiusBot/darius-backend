import ccxt
import asyncio
import logging
from collections import defaultdict
from tortoise.functions import Sum
from main.src.models import Api, BotConfig, User, BotOrder, Transaction
from main.src.core.cipher import decrypt
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@permission_validator("get_stats")
async def _get_stats(user: User):

    user_balance_stats, bot_quantity_stats, user_stats, bot_stats = await asyncio.gather(
        get_user_balance_stats(),
        get_bot_quantity_stats(),
        get_user_stats(),
        get_bot_stats(),
    )

    return {
        'user_balance_stats': user_balance_stats,
        'bot_quantity_stats': bot_quantity_stats,
        'user_stats': user_stats,
        'bot_stats': bot_stats,
        # 'transaction_stats': await get_transaction_stats(),
    }


async def get_transaction_stats():
    try:
        return {
            'transaction_number': await Transaction.filter(is_del=False).count(),
            'amount': await Transaction.filter(is_del=False).annotate(total_amount=Sum('amount'))
        }
    except Exception as e:
        logger.error('get user stats error')
        logger.exception("")
        return str(e)


async def get_bot_stats():
    try:
        return {
            'active_bot_number': await BotOrder.filter(is_del=False).count(),
            'total_bot_number': await BotOrder.all().count(),
        }
    except Exception as e:
        logger.error('get bot stats error')
        logger.exception("")
        return str(e)


async def get_user_stats():
    try:
        return {
            'user_number': await User.filter(is_del=False).count()
        }
    except Exception as e:
        logger.error('get user stats error')
        logger.exception("")
        return str(e)


async def get_user_balance_stats():
    try:
        total_balance = defaultdict(float)

        # parallel this to speed up
        async for api in Api.all():
            try:
                api_secret = decrypt(api.api_key, api.api_secret)
                if api.exchange == "ftx":
                    exchange = getattr(ccxt, api.exchange)({
                        "enableRateLimit": True,
                        "apiKey": api.api_key,
                        "secret": api_secret,
                        "options": {
                            "defaultType": "spot"
                        },
                        "headers": {"FTX-SUBACCOUNT": api.subaccount} if api.subaccount else {}
                    })
                    total_balance['ftx'] += exchange.fetchBalance()['USD']['total']
                elif api.exchange == "binance":
                    exchange = getattr(ccxt, api.exchange)({
                        "enableRateLimit": True,
                        "apiKey": api.api_key,
                        "secret": api_secret,
                        "options": {
                            "defaultType": "spot"
                        },
                    })
                    total_balance['binance_spot'] += exchange.fetchBalance()['USDT']['total']
                    exchange = getattr(ccxt, api.exchange)({
                        "enableRateLimit": True,
                        "apiKey": api.api_key,
                        "secret": api_secret,
                        "options": {
                            "defaultType": "margin"
                        },
                    })
                    total_balance['binance_margin'] += exchange.fetchBalance()['USDT']['total']
                    exchange = getattr(ccxt, api.exchange)({
                        "enableRateLimit": True,
                        "apiKey": api.api_key,
                        "secret": api_secret,
                        "options": {
                            "defaultType": "future"
                        },
                    })
                    total_balance['binance_future'] += exchange.fetchBalance()['USDT']['total']
            except KeyboardInterrupt as e:
                raise e
            except Exception:
                logger.exception("")
                continue
        return total_balance
    except Exception as e:
        logger.error('get user balance error')
        logger.exception("")
        return str(e)


async def get_bot_quantity_stats():
    try:
        quantity_stats = defaultdict(float)
        async for config in BotConfig.filter(is_del=False, test=False).prefetch_related("api", "bot"):
            quantity = config.quantity * config.leverage
            quantity_stats[config.bot.channel] += quantity
            quantity_stats[config.api.exchange] += quantity
            quantity_stats[config.target] += quantity
        return quantity_stats
    except Exception as e:
        logger.error('get bot quantity error')
        logger.exception("")
        return str(e)
