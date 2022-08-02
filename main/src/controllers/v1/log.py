import secrets
import logging
import asyncio
from datetime import datetime
from google.cloud import logging as cloud_logging
from tortoise.transactions import atomic

from main.src.core.exchange import Exchange
from main.src.exception import BackendException
from main.src.utils import error_handler, input_filter
from main.src.models import Provider, RoiLog, BotOrder, Trade


logger = logging.getLogger(__name__)


@error_handler()
@input_filter()
@atomic()
async def botlog(request: dict):
    logger.info("Log bot stats")
    logging_client = cloud_logging.Client()
    cloud_logger = logging_client.logger("bot_stats")

    bot_cnt = BotOrder.filter(
        status="RUNNING",
        is_del=False,
        user_id__not_in=(27, 34, 700),
        config__test=False
    ).count()

    date = datetime.now()
    y, m, d = date.year, date.month, date.day
    trade_volume = Trade.filter(
        created_at__gt=datetime(y, m, d),
        status__not='error',
        bot__user_id__not_in=(27, 34, 700),
        is_del=False,
        quantity__isnull=False
    ).values_list('quantity', flat=True)

    bot_cnt, trade_volume = await asyncio.gather(
        bot_cnt,
        trade_volume
    )

    bot_stats = {
        'bot_count': bot_cnt,
        'trade_volume': sum(trade_volume),
    }
    logger.info(f"{bot_stats}")
    cloud_logger.log_struct(bot_stats)
    return {"message": 'success'}


@error_handler()
@input_filter()
@atomic()
async def roilog(request: dict):
    provider = request['provider']
    access_token = request['access_token']
    roi = request['roi']
    timestamp = request['timestamp']
    logger.info(f"Log {provider} roi")

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

    logging_client = cloud_logging.Client()
    log_name = "roi"
    roi_logger = logging_client.logger(log_name)
    roi_info = {
        'roi': roi,
        'provider': provider.name,
        'timestamp': timestamp
    }
    roi_logger.log_struct(roi_info)

    return {"message": 'success'}


@error_handler()
@input_filter()
async def rebatelog(request: dict):
    logger.info("Log rebate")

    logging_client = cloud_logging.Client()
    log_name = "rebate_v2"
    rebate_logger = logging_client.logger(log_name)
    rebate_info = Exchange.fapiPrivate_get_apireferral_overview()
    rebate_info['exchange'] = 'binance'

    for key in ['totalTradeVol', 'totalTradeUser', 'totalRebateVol']:
        rebate_info[key] = float(rebate_info[key])

    rebate_logger.log_struct(rebate_info)

    # for entry in rebate_logger.list_entries():
    #     timestamp = entry.timestamp.isoformat()
    #     print("* {}: {}".format(timestamp, entry.payload))

    return {"message": 'success'}
