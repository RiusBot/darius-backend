import json
import logging
from typing import List
from datetime import datetime, timedelta
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator

from main.src.models import User, Transaction
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_transaction")
async def _get_user_transaction(user: User, payment_id: int = None):
    uid = user.uid
    logger.info(f"Get transaction for user {uid}")

    Transaction_Pydantic_List = pydantic_queryset_creator(
        Transaction,
        include=["wallet", "txid", "id", "amount"]
    )

    query = user.transaction_user.filter(is_del=False)
    if payment_id is not None:
        query = query.filter(payment_id=payment_id)
    transaction_list = await Transaction_Pydantic_List.from_queryset(query.offset(0).limit(20))

    transaction_list = json.loads(transaction_list.json())
    for transaction in transaction_list:
        transaction["transaction_id"] = transaction.pop("id")
    logger.info(f"Get user [{uid}] {len(transaction_list)} transactions")
    return transaction_list


@atomic()
@permission_validator("create_user_transaction")
async def _create_user_transaction(user: User, wallet: str, txid: str, payment_id: int, transaction_date: str) -> int:
    uid = user.uid
    logger.info(f"Create new transaction for user [{uid}] with plans [{plan_ids}]")

    # validate payment: apply lock here
    payment = await user.payment_user.filter(is_del=False).select_for_update(nowait=True).first()
    if payment is None:
        raise BackendException("Invalid payment_id")

    # validate transaction
    amount = validate_transaction(wallet, txid, transaction_date)  

    # create transaction
    transaction, create = await Transaction.get_or_create(
        defaults={
            "user": user,
            "payment": payment,
            "wallet": wallet,
            "txid": txid,
            "amount": amount,
        },
        txid=txid,
    )
    if not create:
        raise BackendException("transaction exists")

    # update payment
    remain = max(payment.remain - amount, 0)
    payment.remain = remain

    if remain == 0:

        # delete payment
        payment.is_del = True

        # activate subscription
        async for subscription in payment.subscription_payment.filter(is_del=False).prefetch_related("plan"):
            subscription.status = SubscriptionStatus.CONFIRM
            subscription.expire_date = datetime.now() + timedelta(days=subscription.plan.day)
            await subscription.save()
        # update query at once, but cannot customize expire_date
        # await payment.subscription_payment.filter(is_del=False).update(
        #     status=SubscriptionStatus.CONFIRM,
        #     expire_date=datetime.now() + timedelta(days=)
        # )

    await payment.save()

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
        logger.warning(f"Negative amount")

    # validate transaction
    transaction = await user.transaction_user.filter(is_del=False).filter(id=transaction_id).first()
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
