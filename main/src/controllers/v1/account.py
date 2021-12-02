import logging
from aiohttp.web import json_response
from main.src.core.account import _update_user_profile, _get_user_profile, _create_user_profile, _delete_user_profile
from main.src.core.auth import authenticate


logger = logging.getLogger(__name__)


async def update_user_profile(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Update user profile %s", json_payload)
        user_id = json_payload["user_id"]
        user_name = json_payload["user_name"]
        email = json_payload["email"]
        await _update_user_profile(user_id, user_name, email)
        return json_response(status=200, data={})
    except Exception as ex:
        logger.exception("Unexpected error when updating user profile, due to: %s", ex)
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(ex)
            }
        )


async def get_user_profile(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Get user profile %s", json_payload)
        user_id = json_payload["user_id"]
        user_profile = await _get_user_profile(user_id)
        return json_response(
            status=200,
            data=user_profile
        )
    except Exception as e:
        logger.error("Get user profile error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def create_user_profile(request):

    json_payload = await request.json()

    try:
        logger.info("Create user profile")
        user_name = json_payload["user_name"]
        email = json_payload["email"]
        password = json_payload["password"]
        user_id = await _create_user_profile(user_name, email, password)
        return json_response(
            status=200,
            data={
                "user_id": user_id
            }
        )
    except Exception as e:
        logger.error("Create user profile error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def delete_user_profile(request):

    json_payload = await request.json()

    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Delete user profile %s", json_payload)
        user_id = json_payload["user_id"]
        await _delete_user_profile(user_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete user profile error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
