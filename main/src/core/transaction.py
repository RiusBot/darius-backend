import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator

from main.src.models import User, Transaction
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.exchange import validate_transaction


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_transaction")
async def _get_user_transaction(user: User, payment_id: int = None):
    uid = user.uid
    logger.info(f"Get transaction for user {uid}")

    Transaction_Pydantic_List = pydantic_queryset_creator(
        Transaction,
        include=["wallet", "txid", "id", "amount", "date"]
    )

    query = user.transaction_user.filter(is_del=False)
    if payment_id is not None:
        query = query.filter(payment_id=payment_id)
    transaction_list = await Transaction_Pydantic_List.from_queryset(query.offset(0).limit(20))

    transaction_list = json.loads(transaction_list.json())
    for transaction in transaction_list:
        transaction["transaction_id"] = transaction.pop("id")
        transaction["date"] = transaction["date"][:10]

    logger.info(f"Get user [{uid}] {len(transaction_list)} transactions")
    return transaction_list


@atomic()
@permission_validator("create_user_transaction")
async def _create_user_transaction(user: User, wallet: str, txid: str, date: str) -> int:
    uid = user.uid
    logger.info(f"Create new transaction for user [{uid}] with txid [{txid}]")

    # acquire lock
    user = await user.filter(id=user.id).select_for_update().first()

    # validate transaction
    amount, date = validate_transaction(wallet, txid, date)

    # create transaction
    transaction, create = await Transaction.get_or_create(
        defaults={
            "user": user,
            "wallet": wallet,
            "amount": amount,
            "date": date
        },
        txid=txid,
    )
    if not create:
        raise BackendException("transaction exists")

    # update balance
    user.balance += amount
    await user.save()

    transaction_id = transaction.id
    logger.info(f"Create transaction [{transaction_id}]")
    return transaction_id


@atomic()
@permission_validator("update_user_transaction")
async def _update_user_transaction(user: User, transaction_id: int, wallet: str, txid: str, amount: float):
    uid = user.uid
    logger.info(f"Update transaction [{transaction_id}] for user [{uid}]")

    # warning amount
    if amount < 0:
        logger.warning("Negative amount")

    # validate transaction
    transaction = await user.transaction_user.filter(is_del=False, id=transaction_id).first()
    if transaction is None:
        raise BackendException("Invalid transaction_id.")

    # update transaction
    transaction.wallet = wallet
    transaction.txid = txid
    transaction.amount = amount
    await transaction.save()


@atomic()
@permission_validator("delete_user_transaction")
async def _delete_user_transaction(user: User, transaction_id: int):
    uid = user.uid
    logger.info(f"Delete transaction [{transaction_id}] for user {uid}")

    # validate transaction
    transaction = await user.transaction_user.filter(id=transaction_id).filter(is_del=False).first()
    if transaction is None:
        raise BackendException("Invalid transaction_id")

    # delete transaction
    transaction.is_del = True
    await transaction.save()
