import secrets
import logging
from datetime import datetime
from google.cloud import logging as cloud_logging
from tortoise.transactions import atomic

from main.src.core.exchange import Exchange
from main.src.exception import BackendException
from main.src.utils import error_handler, input_filter
from main.src.models import Provider, RoiLog


logger = logging.getLogger(__name__)


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
