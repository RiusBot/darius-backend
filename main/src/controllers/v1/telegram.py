import logging
from aiohttp.web import json_response
from main.src.core.telegram import _get_user_telegram, _create_user_telegram, _delete_user_telegram, _update_user_telegram, _check_tg_user_valid
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_telegram(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        telegram_info = await _get_user_telegram(uid)
        return json_response(
            status=200,
            data=telegram_info
        )
    except Exception as e:
        logger.error("Get telegram error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def check_tg_user_valid(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        user_id = json_payload["user_id"]
        channel = json_payload["channel"]
        valid = await _check_tg_user_valid(user_id, channel)
        return json_response(
            status=200,
            data={
                "valid": valid
            }
        )
    except Exception as e:
        logger.error("Create telegram error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
    
    
async def create_user_telegram(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        token = json_payload['token']
        telegram_id = json_payload['telegram_id']
        telegram_id = await _create_user_telegram(uid, telegram_id, token)
        return json_response(
            status=200,
            data={
                "telegram_id": telegram_id
            }
        )
    except Exception as e:
        logger.error("Create telegram error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_telegram(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        telegram_id = json_payload["telegram_id"]
        await _update_user_telegram(uid, telegram_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update telegram error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_telegram(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        await _delete_user_telegram(uid)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete telegram error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
