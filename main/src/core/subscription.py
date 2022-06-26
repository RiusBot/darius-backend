import json
import asyncio
import logging
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List

from main.src.models import Subscription, User, Plan, Telegram, BotOrder, Referral, ReferralHistory
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.telegram_bot import create_invite_link, revoke_invite_link, kick_user
from main.src.core.referral import create_user_referral_history


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
        try:
            kick_user(subscription.plan.channel, telegram)
        except Exception:
            continue

        # clean bot
        # async for bot in subscription.user.bot_user.filter(
        #     is_del=False,
        #     channel=subscription.plan.channel
        # ).prefetch_related("config"):
        #     closed_bot_count += 1
        #     bot.is_del = True
        #     bot.config.is_del = True
        #     await bot.save()
        #     await bot.config.save()

    logger.info(f"{expire_subscription_count} subscription expired, {closed_bot_count} bot closed.")
    await Subscription.filter(
        is_del=False,
        expire_date__lt=datetime.now()
    ).update(is_del=None)

    # clean trial expired bot
    await BotOrder.filter(
        is_del=False,
        is_trial=True,
        trial_expired_at__lt=datetime.now()
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
@permission_validator("get_subscription_info")
async def _get_subscription_info(user: User, channel: str) -> dict:
    uid = user.uid
    logger.info(f"Get {channel} subscription info for user {uid}")

    count = await Subscription.filter(
        is_del=False,
        channel=channel,
        user_id__not_in=(27, 34, 700),  # my testing accounts
        user__balance__lt=3000,
        expire_date__gt=datetime.now(),
    ).count()

    info = {
        'count': count
    }

    logger.info(f"{channel} subscription info {info}")
    return info


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


async def referrer_subscribe_rebate(user: User, price: float, subscription: Subscription):
    referral, sub_exist = await asyncio.gather(
        user.referral_user.prefetch_related('referrer').first(),
        ReferralHistory.filter(subscription=subscription).exists()  # expand dont give rebate
    )

    if referral.referrer and (not sub_exist):
        referrer = await Referral.filter(id=referral.referrer.id).prefetch_related('user').select_for_update().first()
        referrer.subscribe_count += 1
        referrer.total_rebate += price * referrer.referrer_rebate_rate
        referral.total_rebate += price * referrer.referral_rebate_rate
        total_rebate = price * referrer.rebate_rate

        await asyncio.gather(
            create_user_referral_history(
                referrer,
                referral,
                subscription=subscription,
                rebate=total_rebate,
                referrer_rebate_rate=referrer.referrer_rebate_rate,
                referral_rebate_rate=referrer.referral_rebate_rate
            ),
            referrer.save(),
            referral.save()
        )


@atomic()
@permission_validator("create_user_subscription")
async def _create_user_subscription(user: User, plan_id: int) -> List[int]:
    uid = user.uid
    role = user.role.name
    user, plan = await asyncio.gather(
        user.filter(id=user.id).select_for_update().first(),  # acquire lock
        Plan.filter(id=plan_id, is_del=False).first()
    )

    # validate plan exists
    if plan is None:
        raise BackendException("Invalid plan_id")

    if role != 'vip':
        # validate balance
        if float(user.balance) < float(plan.price):
            raise BackendException("Insufficient balance")

        # update balance
        user.balance = float(user.balance) - float(plan.price)

    # create subscription
    channel = plan.channel
    expire_date = None if (float(plan.day) == 0 or plan.day is None) else datetime.now() + timedelta(days=int(plan.day))
    subscription, create = await Subscription.get_or_create(
        defaults={
            "expire_date": expire_date,
            "plan": plan,
        },
        channel=channel,
        is_del=False,
        user=user
    )

    subscription, user_telegram = await asyncio.gather(
        Subscription.filter(id=subscription.id).select_for_update().first(),  # acquire lock
        user.telegram_user.filter(user=user).first()
    )

    if create:
        logger.info(f"Create subscription {subscription} for user [{uid}] with plan [{plan_id}]")

        # dont use default param for get_or_create because it will create invite link first
        subscription.invite_link = create_invite_link(channel, user_telegram)

        # first subscription refund
        subscription_count = await user.subscription_user.all().count()
        if subscription_count == 1:
            if role != 'vip':
                # first subscription refund 30%
                user.balance += float(plan.price) * 0.3
    else:
        new_expire_date = subscription.expire_date + timedelta(days=int(plan.day))
        logger.info(f"Expand subscription {subscription} for user {uid} with plan [{plan_id}] to {new_expire_date}")
        if subscription.expire_date is None:
            raise BackendException("Life Time cannot expand expire date")
        subscription.expire_date = new_expire_date

        if role != 'vip':
            # renew (expand) refund 10%
            user.balance += float(plan.price) * 0.15

    # referrer get rebate from user subscription
    await asyncio.gather(
        referrer_subscribe_rebate(user, float(plan.price), subscription),
        user.save(),
        subscription.save()
    )
    return subscription.id


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
    subscription.is_del = None
    await subscription.save()
    revoke_invite_link(subscription.plan.channel, subscription.invite_link)

    # is_del = None
    # so that unique constraint (user, channel, is_del) will not trigger after deleted
    # only is_del=True will be constrainted
    # to avoid duplicate subscription created
