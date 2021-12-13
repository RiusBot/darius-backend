import logging
from aiohttp.web import json_response
from main.src.core.subscription import _get_user_subscription, _create_user_subscription, _delete_user_subscription, _update_user_subscription
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


async def get_user_subscription(request):

    json_payload = dict(request.rel_url.query)

    try:
        logger.info("Get subscription")
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

    try:
        logger.info("Create subscription")
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

    try:
        logger.info("Update subscription")
        uid = json_payload["uid"]
        update_uid = json_payload["update_uid"]
        subscription_id = json_payload["subscription_id"]
        expire_date = json_payload["expire_date"]
        status = json_payload["status"]
        await _update_user_subscription(uid, update_uid, subscription_id, expire_date, status)
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

    try:
        logger.info("Delete subscription")
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
