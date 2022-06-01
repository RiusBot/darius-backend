import asyncio
import logging
from aiohttp.web import json_response
from main.src.core.trade import _clean_limit_order, _clean_oco_order, _get_bot_trades
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_bot_trades(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get bot trades")
        uid = json_payload["uid"]
        bot_id = json_payload["bot_id"]
        page = int(json_payload.get("page", 0))
        pagesize = int(json_payload.get("pagesize", 20))
        trade_list = await _get_bot_trades(uid, bot_id, page, pagesize)
        return json_response(
            status=200,
            data=trade_list
        )
    except Exception as e:
        logger.error("Get bot trades error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )

async def clean_limit_order(request):

    try:
        logger.info("Clean limit order")
        asyncio.create_task(_clean_limit_order())
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Clean limit order error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def clean_oco_order(request):

    try:
        logger.info("Clean oco order")
        asyncio.create_task(_clean_oco_order())
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Clean oco order error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
