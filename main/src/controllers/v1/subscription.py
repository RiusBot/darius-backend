import logging
from aiohttp.web import json_response
from main.src.core.subscription import _get_user_subscription, _create_user_subscription, _delete_user_subscription, _update_user_subscription, _clean_subscription
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def clean_subscription(request):

    json_payload = await request.json()

    try:
        await _clean_subscription()
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Get subscription error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def get_user_subscription(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        subscribe_list = await _get_user_subscription(uid)
        return json_response(
            status=200,
            data=subscribe_list
        )
    except Exception as e:
        logger.error("Get subscription error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_subscription(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        plan_id = json_payload["plan_id"]
        subscription_id = await _create_user_subscription(uid, plan_id)
        return json_response(
            status=200,
            data={
                "subscription_id": subscription_id
            }
        )
    except Exception as e:
        logger.error("Create subscription error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_subscription(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        subscription_id = json_payload["subscription_id"]
        expire_date = json_payload["expire_date"]
        await _update_user_subscription(uid, subscription_id, expire_date)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update subscription error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_subscription(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        subscription_id = json_payload["subscription_id"]
        await _delete_user_subscription(uid, subscription_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete subscription error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
