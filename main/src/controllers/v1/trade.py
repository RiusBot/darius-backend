import asyncio
import logging
from main.src.core.trade import _clean_limit_order, _clean_oco_order, _get_bot_trades, _get_bot_trades2
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_bot_trades(request: dict):
    uid = request["uid"]
    bot_id = request["bot_id"]
    logger.debug(f"Get user {uid} bot trades {bot_id}")
    trade_list = await _get_bot_trades(uid, bot_id)
    return trade_list


@error_handler()
@input_filter
async def get_bot_trades2(request: dict):
    uid = request["uid"]
    bot_id = request["bot_id"]
    logger.debug(f"Get user {uid} bot trades {bot_id}")
    page = int(request.get("page", 0))
    pagesize = int(request.get("pagesize", 20))
    trade_list = await _get_bot_trades2(uid, bot_id, page, pagesize)
    return trade_list


@error_handler()
@input_filter
async def clean_limit_order(request: dict):
    logger.info("Clean limit order")
    asyncio.create_task(_clean_limit_order())


@error_handler()
@input_filter
async def clean_oco_order(request: dict):
    logger.info("Clean oco order")
    asyncio.create_task(_clean_oco_order())
