import logging
from main.src.core.transaction import _get_user_transaction, _create_user_transaction, _delete_user_transaction, _update_user_transaction
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_user_transaction(request: dict):
    uid = request["uid"]
    logger.debug(f"get user {uid} transaction")
    transaction = await _get_user_transaction(uid)
    return transaction


@error_handler()
@input_filter
async def create_user_transaction(request: dict):
    uid = request["uid"]
    wallet = request["wallet"]
    txid = request["txid"]
    date = request["date"]
    logger.info(f"create user {uid} transaction {txid}")
    transaction_id = await _create_user_transaction(uid, wallet, txid, date)
    return {"transaction_id": transaction_id}


@error_handler()
@input_filter
async def update_user_transaction(request: dict):
    uid = request["uid"]
    transaction_id = request["transaction_id"]
    logger.info(f"update user {uid} transaction {transaction_id}")
    wallet = request["wallet"]
    txid = request["txid"]
    amount = request["amount"]
    await _update_user_transaction(uid, transaction_id, wallet, txid, amount)


@error_handler()
@input_filter
async def delete_user_transaction(request: dict):
    uid = request["uid"]
    transaction_id = request["transaction_id"]
    logger.info(f"delete user {uid} transaction {transaction_id}")
    await _delete_user_transaction(uid, transaction_id)
