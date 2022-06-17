import logging
from aiohttp.web import json_response
from main.src.core.account import _update_user_profile, _get_user_profile, _create_user, _delete_user
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def update_user_profile(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Update user profile %s", json_payload)
        uid = json_payload["uid"]
        user_name = json_payload["user_name"]
        await _update_user_profile(uid, user_name)
        return json_response(status=200, data={})
    except Exception as e:
        logger.exception("Unexpected error when updating user profile, due to: %s", e)
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def get_user_profile(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get user profile %s", json_payload)
        uid = json_payload["uid"]
        user_profile = await _get_user_profile(uid)
        return json_response(
            status=200,
            data=user_profile
        )
    except Exception as e:
        logger.error("Get user profile error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        referrer = json_payload.get("referrer")
        logger.info(f"Create user profile with referrer {referrer}")
        user_id = await _create_user(uid, referrer)
        return json_response(
            status=200,
            data={
              "user_id": user_id
            }
        )
    except Exception as ex:
        logger.exception("Create user profile error. due to: %s", ex)
        error_message = str(ex) if isinstance(ex, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Delete user profile %s", json_payload)
        uid = json_payload["uid"]
        delete_uid = json_payload["delete_uid"]
        await _delete_user(uid, delete_uid)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete user profile error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
