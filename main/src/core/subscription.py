import json
import logging
from datetime import datetime
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Subscription, User, Plan, Payment
from main.src.models.subscription import SubscriptionStatus
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_subscription")
async def _get_user_subscription(user: User) -> List[Subscription]:
    uid = user.uid
    logger.info(f"Get subscription for user {uid}")

    subscription_Pydantic_List = pydantic_queryset_creator(
        Subscription,
        include=["expire_date", "status", "id", "plan", "plan_id"]
    )

    subscription_list = await subscription_Pydantic_List.from_queryset(
        user.subscription_user.filter(is_del=False).filter(status=SubscriptionStatus.CONFIRM).prefetch_related("plan")
    )
    subscription_list = json.loads(subscription_list.json())
    for subscription in subscription_list:
        subscription["subscription_id"] = subscription.pop("id")
    logger.info(f"Get user [{uid}] {len(subscription_list)} subscription")
    return subscription_list


@atomic()
@permission_validator("create_user_subscription")
async def _create_user_subscription(user: User, plan_id: int, payment_id: int = None) -> List[int]:
    uid = user.uid
    logger.info(f"Create new subscription for user [{uid}] with plans [{plan_id}]")

    # validate plan exists
    plan = await Plan.filter(id=plan_id).filter(is_del=False).first()
    if plan is None:
        raise BackendException("Invalid plan_id")

    # validate duplicate subscriptions
    duplicate_subscription = await user.subscription_user.filter(is_del=False).filter(plan__channel=plan.channel).first()
    if duplicate_subscription is not None:
        raise BackendException(f"{plan.channel} channel already subscribed")

    # validate payment
    payment = None
    if payment_id:
        payment = await Payment.filter(is_del=False).filter(id=payment_id).first()
        if payment is not None:
            raise BackendException("Invalid payment_id")

    # create subscription
    subscription = await Subscription.create(
        user=user,
        plan=plan,
        payment=payment
    )
    subscription_id = subscription.id
    logger.info(f"Create subscription [{subscription_id}]")
    return subscription_id


@atomic()
@permission_validator("update_user_subscription")
async def _update_user_subscription(user: User, subscription_id: int, expire_date: float, status: str):
    uid = user.uid
    logger.info(f"Update subscription [{subscription_id}] for user [{uid}]")

    # validate subscription
    subscription = await user.subscription_user.filter(is_del=False).filter(id=subscription_id).first()
    if subscription is None:
        raise BackendException("Invalid subscription.")

    # update subscription
    subscription.expire_date = datetime.fromtimestamp(expire_date)
    subscription.status = status
    await subscription.save()


@atomic()
@permission_validator("delete_user_subscription")
async def _delete_user_subscription(user: User, subscription_id: int):
    uid = user.uid
    logger.info(f"Delete subscription [{subscription_id}] for user [{uid}]")

    # validate subscription
    subscription = await user.subscription_user.filter(id=subscription_id).filter(is_del=False).first()
    if subscription is None:
        raise BackendException("Invalid subscription_id")

    # delete subscription
    subscription.is_del = True
    await subscription.save()
