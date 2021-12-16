import logging
from aiohttp.web import json_response
from main.src.core.api import _get_user_api, _create_user_api, _delete_user_api, _update_user_api
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_api(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get user api")
        uid = json_payload["uid"]
        api_list = await _get_user_api(uid)
        return json_response(
            status=200,
            data=api_list
        )
    except Exception as e:
        logger.error("Get user api error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_api(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Create user api")
        uid = json_payload["uid"]
        api_key = json_payload["api_key"]
        api_secret = json_payload["api_secret"]
        exchange = json_payload["exchange"]
        subaccount = json_payload.get("subaccount")
        api_id = await _create_user_api(uid, api_key, api_secret, exchange, subaccount)
        return json_response(
            status=200,
            data={
                "api_id": api_id
            }
        )
    except Exception as e:
        logger.error("Create api error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_api(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Update user api")
        uid = json_payload["uid"]
        api_id = json_payload["api_id"]
        api_key = json_payload["api_key"]
        api_secret = json_payload["api_secret"]
        exchange = json_payload["exchange"]
        subaccount = json_payload.get("subaccount")
        api_id = await _update_user_api(uid, api_id, api_key, api_secret, exchange, subaccount)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update api error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_api(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Delete api")
        uid = json_payload["uid"]
        api_id = json_payload["api_id"]
        await _delete_user_api(uid, api_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete api error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
