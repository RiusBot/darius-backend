import json
import logging
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Subscription, User, Plan
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
        user.subscription_user.filter(is_del=False).prefetch_related("plan")
    )
    subscription_list = json.loads(subscription_list.json())
    for subscription in subscription_list:
        subscription["subscription_id"] = subscription.pop("id")

    logger.info(f"Get user [{uid}] {len(subscription_list)} subscription")
    return subscription_list


@atomic()
@permission_validator("create_user_subscription")
async def _create_user_subscription(user: User, plan_id: int) -> List[int]:
    uid = user.uid
    logger.info(f"Create new subscription for user [{uid}] with plan [{plan_id}]")

    # acquire lock
    user = await user.filter(id=user.id).select_for_update().first()

    # validate plan exists
    plan = await Plan.filter(id=plan_id, is_del=False).first()
    if plan is None:
        raise BackendException("Invalid plan_id")

    # validate duplicate subscriptions
    duplicate_subscription = await user.subscription_user.filter(is_del=False, plan__channel=plan.channel).exists()
    if duplicate_subscription:
        raise BackendException(f"{plan.channel} channel already subscribed")

    # validate balance
    if float(user.balance) < float(plan.price):
        raise BackendException("Insufficient balance")

    # create subscription
    expire_date = None if float(plan.day) == 0 else datetime.now() + timedelta(days=int(plan.day))
    subscription, create = await Subscription.get_or_create(
        defaults={
            "expire_date": expire_date,
        },
        plan=plan,
        is_del=False,
        user=user
    )
    if not create:
        raise BackendException("subscription exists")

    subscription_id = subscription.id
    logger.info(f"Create subscription [{subscription_id}]")

    # update balance
    user.balance = float(user.balance) - float(plan.price) + float(plan.day / 3)
    await user.save()

    # if first time create subscription, referrer
    if (await user.subscription_user.all().count()) == 1:
        referrer = User.filter(referral_code=user.referrer, is_del=False).select_for_update().first()
        if referrer is not None:
            referrer.balance += float(plan.day / 10)
            await referrer.save()

    return subscription_id


@atomic()
@permission_validator("update_user_subscription")
async def _update_user_subscription(user: User, subscription_id: int, expire_date: float):
    uid = user.uid
    logger.info(f"Update subscription [{subscription_id}] for user [{uid}]")

    # validate subscription
    subscription = await user.subscription_user.filter(is_del=False, id=subscription_id).first()
    if subscription is None:
        raise BackendException("Invalid subscription.")
    
    # validate date
    try:
        expire_date = parse_date(expire_date)
        if expire_date < datetime.now():
            raise
    except Exception:
        raise BackendException("Invalid date")

    # update subscription
    subscription.expire_date = expire_date
    await subscription.save()


@atomic()
@permission_validator("delete_user_subscription")
async def _delete_user_subscription(user: User, subscription_id: int):
    uid = user.uid
    logger.info(f"Delete subscription [{subscription_id}] for user [{uid}]")

    # validate subscription
    subscription = await user.subscription_user.filter(id=subscription_id, is_del=False).first()
    if subscription is None:
        raise BackendException("Invalid subscription_id")

    # delete subscription
    subscription.is_del = True
    await subscription.save()
