import json
import logging
from functools import wraps
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
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException("Invalid uid")

    subscription_Pydantic_List = pydantic_queryset_creator(
        Subscription,
        include=["expire_date", "status", "id", "plan", "plan_id"]
    )

    subscription_list = await subscription_Pydantic_List.from_queryset(user.subscription_user.filter(is_del=False).prefetch_related("plan").all())
    subscription_list = json.loads(subscription_list.json())
    for subscription in subscription_list:
        subscription["subscription_id"] = subscription.pop("id")
    logger.info(f"Get user [{uid}] {len(subscription_list)} subscription")
    return subscription_list


@atomic()
@permission_validator("create_user_subscription")
async def _create_user_subscription(user: User, plan_id: int) -> int:
    uid = user.uid
    logger.info(f"Create new subscription for user [{uid}] with plan [{plan_id}]")

    # validate user
    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate plan
    plan = await Plan.filter(id=plan_id).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid plan")

    # validate duplicate channel
    # subscription_list = await user.subscription_user.filter(is_del=False).prefetch_related("plan").all()
    # all_subscribe_channel = set([i.plna.channel for i in subscription_list])
    # if plan.channel in all_subscribe_channel:
    #     raise BackendException("channel already subscribed")

    # create subscription
    subscription = await Subscription.create(
        user=user,
        plan=plan,
        expire_date=datetime.now() + timedelta(days=3)
    )
    subscription_id = subscription.id
    logger.info(f"Create subscription [{subscription_id}]")
    return subscription_id


@atomic()
@permission_validator("update_user_subscription")
async def _update_user_subscription(user: User, subscription_id: int, expire_date: str, status: str) -> int:
    uid = user.uid
    logger.info(f"Update subscription [{subscription_id}] for user [{uid}]")

    # validate user
    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate subscription
    subscription = await user.subscription_user.filter(is_del=False).filter(id=subscription_id).first()
    if subscription is None:
        raise BackendException("Invalid subscription.")

    # validate date
    expire_date = parse_date(expire_date)
    if expire_date < datetime.now():
        raise BackendException("Invalid expire date")

    # update subscription
    subscription.expire_date = expire_date
    subscription.status = status
    await subscription.save()


@atomic()
@permission_validator("delete_user_subscription")
async def _delete_user_subscription(user: User, subscription_id: int) -> int:
    uid = user.uid
    logger.info(f"Delete subscription [{subscription_id}] for user {uid}")

    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate subscription
    subscription = await user.subscription_user.filter(id=subscription_id).filter(is_del=False).first()
    if subscription is None:
        raise BackendException("Invalid subscription_id")

    # delete subscription
    subscription.is_del = True
    await subscription.save()
