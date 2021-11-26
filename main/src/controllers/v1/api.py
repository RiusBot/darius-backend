import logging
from aiohttp.web import json_response
from main.src.core.api import _get_user_api, _create_user_api, _delete_user_api
from main.src.core.auth import authenticate


async def get_user_api(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Get user api")
        user_id = json_payload["user_id"]
        api_list = await _get_user_api(user_id)
        return json_response(
            status=200,
            data=api_list
        )
    except Exception as e:
        logging.error("Get user api error.")
        logging.exception("")
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
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Create user api")
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
        logging.error("Create api error.")
        logging.exception("")
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
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Delete api")
        user_id = json_payload["user_id"]
        api_id = json_payload["api_id"]
        await _delete_user_api(user_id, api_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logging.error("Delete api error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
