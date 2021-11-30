import logging
from aiohttp.web import json_response
from main.src.core.api import _get_user_api, _create_user_api, _delete_user_api, _update_user_api
from main.src.core.auth import authenticate


logger = logging.getLogger(__name__)


async def get_user_api(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Get user api")
        user_id = json_payload["user_id"]
        api_list = await _get_user_api(user_id)
        return json_response(
            status=200,
            data=api_list
        )
    except Exception as e:
        logger.error("Get user api error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def create_user_api(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Create user api")
        user_id = json_payload["user_id"]
        api_key = json_payload["api_key"]
        api_secret = json_payload["api_secret"]
        exchange = json_payload["exchange"]
        api_id = await _create_user_api(user_id, api_key, api_secret, exchange)
        return json_response(
            status=200,
            data={
                "api_id": api_id
            }
        )
    except Exception as e:
        logger.error("Create api error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def update_user_api(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Update user api")
        user_id = json_payload["user_id"]
        api_id = json_payload["api_id"]
        api_key = json_payload["api_key"]
        api_secret = json_payload["api_secret"]
        exchange = json_payload["exchange"]
        api_id = await _update_user_api(user_id, api_id, api_key, api_secret, exchange)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update api error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def delete_user_api(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Delete api")
        user_id = json_payload["user_id"]
        api_id = json_payload["api_id"]
        await _delete_user_api(user_id, api_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete api error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
