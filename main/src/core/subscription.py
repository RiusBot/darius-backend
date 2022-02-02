import json
import logging
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Subscription, User, Plan, Telegram
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.telegram_bot import create_invite_link, revoke_invite_link, kick_user


logger = logging.getLogger(__name__)


@atomic()
async def _clean_subscription() -> List[Subscription]:
    logger.info("Clean subscription")

    # clear bots
    expire_subscription_count = 0
    closed_bot_count = 0

    async for subscription in Subscription.filter(
        is_del=False,
        expire_date__lt=datetime.now()
    ).prefetch_related("user", "plan"):
        expire_subscription_count += 1

        # clean telegram
        revoke_invite_link(subscription.plan.channel, subscription.invite_link)
        telegram = await subscription.user.telegram_user.all().first()
        kick_user(subscription.plan.channel, telegram)

        # clean bot
        async for bot in subscription.user.bot_user.filter(
            is_del=False,
            channel=subscription.plan.channel
        ).prefetch_related("config"):
            closed_bot_count += 1
            bot.is_del = True
            bot.config.is_del = True
            await bot.save()
            await bot.config.save()

    logger.info(f"{expire_subscription_count} subscription expired, {closed_bot_count} bot closed.")
    await Subscription.filter(
        is_del=False,
        expire_date__lt=datetime.now()
    ).update(is_del=True)


@atomic()
@permission_validator("get_user_subscription")
async def _get_user_subscription(user: User) -> List[Subscription]:
    uid = user.uid
    logger.info(f"Get subscription for user {uid}")

    subscription_Pydantic_List = pydantic_queryset_creator(
        Subscription,
        include=["expire_date", "status", "id", "plan", "plan_id", "invite_link"]
    )

    subscription_list = await subscription_Pydantic_List.from_queryset(
        user.subscription_user.filter(is_del=False).prefetch_related("plan")
    )
    subscription_list = json.loads(subscription_list.json())
    for subscription in subscription_list:
        subscription["subscription_id"] = subscription.pop("id")
        if subscription["expire_date"] is None:
            subscription["expire_date"] = "Life Time"

    logger.info(f"Get user [{uid}] {len(subscription_list)} subscription")
    return subscription_list


@atomic()
async def _get_tg_user_subscription(telegram_id: str) -> List[Subscription]:
    logger.info(f"Get subscription for tg user {telegram_id}")

    # validate user
    tg = await Telegram.filter(is_del=False, telegram_id=telegram_id).prefetch_related("user").first()
    if tg is None:
        raise BackendException(f"Invalid telegram_id [{telegram_id}]")
    else:
        user = tg.user
        uid = user.uid

    subscription_Pydantic_List = pydantic_queryset_creator(
        Subscription,
        include=["expire_date", "status", "id", "plan", "plan_id", "invite_link"]
    )

    subscription_list = await subscription_Pydantic_List.from_queryset(
        user.subscription_user.filter(is_del=False).prefetch_related("plan")
    )
    subscription_list = json.loads(subscription_list.json())
    for subscription in subscription_list:
        subscription["subscription_id"] = subscription.pop("id")
        if subscription["expire_date"] is None:
            subscription["expire_date"] = "Life Time"

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

    # validate duplicate subscriptions: remove because use expand expire date
    # duplicate_subscription = await user.subscription_user.filter(is_del=False, plan__channel=plan.channel).first()
    # if duplicate_subscription:
    #     raise BackendException(f"{plan.channel} channel already subscribed")

    # validate balance
    if float(user.balance) < float(plan.price):
        raise BackendException("Insufficient balance")

    # update balance
    user.balance = float(user.balance) - float(plan.price)

    # create subscription
    channel = plan.channel
    expire_date = None if (float(plan.day) == 0 or plan.day is None) else datetime.now() + timedelta(days=int(plan.day))
    user_telegram = await user.telegram_user.filter(user=user).first()
    subscription, create = await Subscription.get_or_create(
        defaults={
            "expire_date": expire_date,
            "plan": plan,
            "invite_link": create_invite_link(channel, user_telegram)
        },
        plan__channel=channel,
        is_del=False,
        user=user
    )
    subscription_id = subscription.id

    if create:
        logger.info(f"Create subscription [{subscription_id}]")

        # if first time create subscription, referrer get credit
        subscription_count = await user.subscription_user.all().count()
        if subscription_count == 1:

            # first subscription refund
            user.balance += float(plan.price) * 0.3

            # referrer credit
            referrer = await User.filter(referral_code=user.referrer, is_del=False).select_for_update().first()
            if referrer is not None:
                referrer.referrer_count += 1
                referrer.balance += float(plan.day) / 10
                await referrer.save()
    else:
        logger.info(f"Expand subscription [{subscription_id}]")
        if subscription.expire_date is None:
            raise BackendException("Life Time cannot expand expire date")
        subscription.expire_date = subscription.expire_date + timedelta(days=int(plan.day))
        await subscription.save()
        user.balance += float(plan.price) * 0.15

    await user.save()
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
        # if expire_date < datetime.now():
        #     raise
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
    subscription = await user.subscription_user.filter(id=subscription_id, is_del=False).prefetch_related("plan").first()
    if subscription is None:
        raise BackendException("Invalid subscription_id")

    # delete subscription
    subscription.is_del = True
    await subscription.save()
    revoke_invite_link(subscription.plan.channel, subscription.invite_link)
