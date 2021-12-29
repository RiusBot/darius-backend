import logging
from aiohttp.web import json_response
from main.src.core.transaction import _get_user_transaction, _create_user_transaction, _delete_user_transaction, _update_user_transaction
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_transaction(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        transaction = await _get_user_transaction(uid)
        return json_response(
            status=200,
            data=transaction
        )
    except Exception as e:
        logger.error("Get transaction error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_transaction(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        wallet = json_payload["wallet"]
        txid = json_payload["txid"]
        date = json_payload["date"]
        transaction_id = await _create_user_transaction(uid, wallet, txid, date)
        return json_response(
            status=200,
            data={
                "transaction_id": transaction_id
            }
        )
    except Exception as e:
        logger.error("Create transaction error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_transaction(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        transaction_id = json_payload["transaction_id"]
        wallet = json_payload["wallet"]
        txid = json_payload["txid"]
        amount = json_payload["amount"]
        await _update_user_transaction(uid, transaction_id, wallet, txid, amount)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update transaction error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_transaction(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        transaction_id = json_payload["transaction_id"]
        await _delete_user_transaction(uid, transaction_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete transaction error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
