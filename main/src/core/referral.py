import logging
import asyncio
from tortoise.transactions import atomic

from main.src.models import Referral, ReferralHistory, User, Subscription, BotOrder
from main.src.exception import BackendException
from main.src.utils import generate_random_string


logger = logging.getLogger(__name__)


async def generate_referral_code():

    referral_code = None
    for _ in range(10):
        referral_code = generate_random_string(8)
        if (await Referral.filter(referral_code=referral_code).exists()):
            referral_code = None
            continue

    if referral_code is None:
        raise BackendException("Cannot generate referral_code")
    return referral_code


async def create_user_referral(referrer_code: str) -> Referral:

    referrer, referral_code = await asyncio.gather(
        Referral.filter(
            is_del=False,
            referral_code=referrer_code
        ).select_for_update().prefetch_related('user').first(),
        generate_referral_code()
    )
    if referrer_code and not referrer:
        logger.error(f"Referrer code {referrer_code} not exists")

    referral = await Referral.create(
        referrer=referrer,
        referral_code=referral_code
    )

    if referrer:
        referrer.register_count += 1
        await asyncio.gather(
            referrer.save(),
            create_user_referral_history(referrer, referral)
        )

    logger.info(f"Create referral {referral.id}")
    return referral


async def create_user_referral_history(
    referrer: Referral,
    referral: Referral,
    bot: BotOrder = None,
    subscription: Subscription = None,
    rebate: float = 0,
    referrer_rebate_rate: float = 0.1,
    referral_rebate_rate: float = 0.0,
) -> ReferralHistory:

    referral_history = await ReferralHistory.create(
        referrer=referrer,
        referral=referral,
        bot=bot,
        subscription=subscription,
        rebate=rebate,
        referrer_rebate_rate=referrer_rebate_rate,
        referral_rebate_rate=referral_rebate_rate
    )

    logger.info(f"Create referral history for {referrer} {referral}")
    return referral_history


@atomic
async def validate_referral_with_history(user: User):
    referral = user.referral
    referral_history_query = ReferralHistory.filter(user=user, is_del=False)
    register_count = await referral_history_query.filter(referral__not=None).count()
    bot_count = await referral_history_query.filter(bot__not=None).count()
    subscription_count = await referral_history_query.filter(subscription__not=None).count()
    total_rebate = await referral_history_query.annotate(total_rebate=sum('rebate')).first()
    try:
        assert register_count == referral.register_count
        assert bot_count == referral.bot_count
        assert subscription_count == referral.subscription_count
        assert total_rebate == referral.total_rebate
    except AssertionError:
        raise BackendException("referral history validation failed")
