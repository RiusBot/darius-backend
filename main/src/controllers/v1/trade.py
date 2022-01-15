import logging
from aiohttp.web import json_response
from main.src.core.trade import _clean_limit_order, _clean_oco_order
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def clean_limit_order(request):

    json_payload = await request.json()

    try:
        logger.info("Clean limit order")
        await _clean_limit_order()
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

    json_payload = await request.json()

    try:
        logger.info("Clean oco order")
        await _clean_oco_order()
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
