import logging
import asyncio
from tortoise.transactions import atomic

from main.src.models import Referral, ReferralHistory, User, Subscription, BotOrder
from main.src.models.referral import ReferralSchemaModel, ReferralHistorySchemaModel
from main.src.exception import BackendException
from main.src.utils import generate_random_string
from main.src.core.permission import permission_validator
from main.src.utils import pagination


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


@atomic()
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


@atomic()
@permission_validator("get_user_referral_history")
async def _get_user_referral_history(user: User, page: int, pagesize: int):

    referral = await user.referral_user.first()
    query = referral.referral_history_referrer.all().prefetch_related("bot", "subscription", "referral")
    pagination_query, total_count, total_page = await pagination(query, page, pagesize)
    referral_history = await pagination_query

    # adhoc solution to prevent pydantic queryset serialization with recursive relation expansion
    referral_history_list = await asyncio.gather(
        *[ReferralHistorySchemaModel.from_tortoise_orm(i) for i in referral_history]
    )
    referral_history_list = [i.dict() for i in referral_history_list]

    for record, orm in zip(referral_history_list, referral_history):
        record["referral_code"] = orm.referral.referral_code
        record["bot_id"] = orm.bot.id if orm.bot else None
        record["subscription_id"] = orm.subscription.id if orm.subscription else None

    return {
        'page': page,
        'pagesize': pagesize,
        'total_page': total_page,
        'total_count': total_count,
        'referral_history': referral_history_list
    }


@atomic()
@permission_validator("get_user_referral_info")
async def _get_user_referral_info(user: User):
    # TODO: add cache
    referral = await user.referral_user.first().prefetch_related('referrer')
    referral_info = await ReferralSchemaModel.from_tortoise_orm(referral)
    referral_info = referral_info.dict()
    referral_info["referrer_code"] = referral.referrer.referral_code
    return referral_info


@atomic()
@permission_validator("update_user_referral_info")
async def _update_user_referral_info(user: User, referrer_rebate_rate: float, referral_rebate_rate: float):
    referral = await user.referral_user.first().prefetch_related('referrer')
    coroutines = [referral.save()]

    if referrer_rebate_rate + referral_rebate_rate > referral.rebate_rate:
        raise BackendException(f"total rebate rate must <= {referral.rebate_rate}")
    else:
        referral.referrer_rebate_rate = referrer_rebate_rate
        referral.referral_rebate_rate = referral_rebate_rate

    # if referrer_code:
    #     if referral.referrer is not None:
    #         raise BackendException(f"You already have referrer {referral.referrer.referral_code}")
    #     elif referral.referral_code == referrer_code:
    #         raise BackendException("Don't referrer yourself")
    #     referrer = await Referral.filter(referral_code=referrer_code).select_for_update().first()
    #     if referrer:
    #         referral.referrer = referrer
    #         referrer.register_count += 1
    #         coroutines += [
    #             referrer.save(),
    #             create_user_referral_history(referrer, referral)
    #         ]
    #     else:
    #         raise BackendException(f"Referral code {referrer_code} not exists")

    await asyncio.gather(*coroutines)
