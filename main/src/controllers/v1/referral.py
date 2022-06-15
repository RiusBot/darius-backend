import asyncio
import logging
from aiohttp.web import json_response
from main.src.core.referral import _get_user_referral_info, _get_user_referral_history
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_referral_info(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get user referral info")
        uid = json_payload["uid"]
        referral_info = await _get_user_referral_info(uid)
        return json_response(
            status=200,
            data=referral_info
        )
    except Exception as e:
        logger.error("Get user referral info error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def get_user_referral_history(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get user referral history")
        uid = json_payload["uid"]
        page = int(json_payload.get("page", 0))
        pagesize = int(json_payload.get("pagesize", 20))
        referral_history = await _get_user_referral_history(uid, page, pagesize)
        return json_response(
            status=200,
            data=referral_history
        )
    except Exception as e:
        logger.error("Get user referral history error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
