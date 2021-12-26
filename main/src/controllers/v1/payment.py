import logging
from aiohttp.web import json_response
from main.src.core.payment import _get_user_payment, _create_user_payment, _delete_user_payment, _update_user_payment
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_payment(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        payment = await _get_user_payment(uid)
        return json_response(
            status=200,
            data=payment
        )
    except Exception as e:
        logger.error("Get payment error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_payment(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        plan_ids = json_payload["plan_ids"]
        payment_id = await _create_user_payment(uid, plan_ids)
        return json_response(
            status=200,
            data={
                "payment_id": payment_id
            }
        )
    except Exception as e:
        logger.error("Create payment error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_payment(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        payment_id = json_payload["payment_id"]
        remain = json_payload["remain"]
        await _update_user_payment(uid, payment_id, remain)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update payment error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_payment(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        payment_id = json_payload["payment_id"]
        await _delete_user_payment(uid, payment_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete payment error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
