import random
import string
import logging
import asyncio
from tortoise.transactions import atomic

from main.src.models import Referral, ReferralHistory, User, Subscription, BotOrder
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


async def generate_referral_code():

    def _generate_referral_code(k=8):
        return ''.join(random.choices(
            string.ascii_uppercase + string.ascii_lowercase + string.digits,
            k=k,
        ))

    referral_code = None
    for _ in range(10):
        referral_code = _generate_referral_code()
        if (await Referral.filter(referral_code=referral_code).exists()):
            referral_code = None
            continue

    if referral_code is None:
        raise BackendException("Cannot generate referral_code")
    return referral_code


@atomic
async def create_user_referral(user: User, referrer: str) -> Referral:

    referrer, referral_code = await asyncio.gather(
        Referral.filter(is_del=False, referral_code=referrer).first(),
        generate_referral_code()
    )

    referral = await Referral.create(
        user=user,
        referrer=referrer,
        referral_code=referral_code
    )

    logger.info(f"Create referral {referral.id} for user {user.id}")
    return referral


@atomic
async def creat_user_referral_history(
    user: User,
    referral: Referral = None,
    bot: BotOrder = None,
    subscription: Subscription = None,
) -> ReferralHistory:

    if bot is None and referral is None and subscription is None:
        logger.error("create referral history failed: all reference is None")

    referral_history = await ReferralHistory.create(
        user=user,
        referral=referral,
        bot=bot,
        subscription=subscription
    )

    logger.info(f"Create refferal history for user {user.id} with r{referral.id} b{bot.id} s{subscription.id}")
    return referral_history
