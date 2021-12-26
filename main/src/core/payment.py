import json
import logging
from functools import wraps
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from tortoise.transactions import atomic
from typing import List
from main.src.models import Subscription, User, Plan, Payment
from main.src.models.payment import PaymentSchemaModel
from main.src.models.plan import PlanSchemaModel
from main.src.models.subscription import SubscriptionStatus
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_payment")
async def _get_user_payment(user: User) -> PaymentSchemaModel:
    uid = user.uid
    logger.info(f"Get payment for user {uid}")

    payment = await user.payment_user.filter(is_del=False).first()
    if payment:
        payment_dict = (await PaymentSchemaModel.from_tortoise_orm(payment)).dict()
        payment_dict["payment_id"] = payment_dict.pop("id")

        subscription_list = await payment.subscription_payment.filter(is_del=False).prefetch_related("plan")
        payment_dict["plans"] = [
            (await PlanSchemaModel.from_tortoise_orm(i.plan)).dict() for i in subscription_list
        ]
        return payment_dict
    else:
        return {}


@atomic()
@permission_validator("create_user_payment")
async def _create_user_payment(user: User, plan_ids: List[int]) -> int:
    uid = user.uid
    logger.info(f"Create new payment for user [{uid}] with plans [{plan_ids}]")

    # validate payment
    payment = await user.payment_user.filter(is_del=False).first()
    if payment is not None:
        raise BackendException("unconfirmed payment exists")

    # validate duplicate plan_ids
    if len(set(plan_ids)) != len(plan_ids):
        raise BackendException("duplicate plan_ids")
    
    # validate plan exists
    plans = await Plan.filter(id__in=plan_ids).filter(is_del=False)
    valid_plan_ids = set([plan.id for plan in plans])
    invalid_plan_ids = set(plan_ids) - valid_plan_ids
    if invalid_plan_ids:
        raise BackendException(f"Invalid plans: {invalid_plan_ids}")
    
    # validate duplicate channel
    subscribe_channels = set([plan.channel for plan in plans])
    if len(subscribe_channels) != len(plan_ids):
        raise BackendException("duplicate channels")
    
    # validate duplicate subscriptions
    duplicate_subscription = await user.subscription_user.filter(is_del=False).filter(plan__channel__in=subscribe_channels).first()
    if duplicate_subscription is not None:
        raise BackendException(f"{duplicate_subscription.channel} channel already subscribed")

    # create payment
    remain = sum([plan.price for plan in plans])
    if remain < 0:
        raise BackendException(f"negative remain: {remain} with plan_ids: {plan_ids}")

    payment = await Payment.create(
        user=user,
        remain=remain,
    )

    # create subscriptions
    subscription_list = []
    for plan in plans:
        subscription = Subscription(
            user=user,
            plan=plan,
            payment=payment,
        )
        if remain == 0:
            subscription.status = SubscriptionStatus.CONFIRM
        subscription_list.append(subscription)

    logger.info(f"create {len(subscription_list)} subscriptions")
    await Subscription.bulk_create(
        subscription_list
    )

    payment_id = payment.id
    logger.info(f"Create payment [{payment_id}]")
    return payment_id


@atomic()
@permission_validator("update_user_payment")
async def _update_user_payment(user: User, payment_id: int, remain: float):
    uid = user.uid
    logger.info(f"Update payment [{payment_id}] for user [{uid}]")

    # validate remain
    if remain < 0:
        raise BackendException("Negative remain")

    # validate payment
    payment = await user.payment_user.filter(is_del=False).filter(id=payment_id).first()
    if payment is None:
        raise BackendException("Invalid payment_id.")

    # update payment
    payment.remain = remain
    await payment.save()

    if remain == 0:
        await payment.subscription_payment.filter(is_del=False).update(status=SubscriptionStatus.CONFIRM)
        


@atomic()
@permission_validator("delete_user_payment")
async def _delete_user_payment(user: User, payment_id: int):
    uid = user.uid
    logger.info(f"Delete payment [{payment_id}] for user {uid}")

    # validate payment
    payment = await user.payment_user.filter(id=payment_id).filter(is_del=False).first()
    if payment is None:
        raise BackendException("Invalid payment_id")

    # delete payment
    payment.is_del = True
    await payment.save()
