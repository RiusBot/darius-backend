import logging
from main.src.core.subscription import (
    _get_user_subscription,
    _create_user_subscription,
    _delete_user_subscription,
    _update_user_subscription,
    _clean_subscription,
    _get_tg_user_subscription,
    _get_subscription_info
)
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def clean_subscription(request: dict):
    logger.info("clean subscription")
    await _clean_subscription()


@error_handler()
@input_filter
async def get_user_subscription(request: dict):
    uid = request["uid"]
    logger.debug(f"get user {uid} subscription")
    subscribe_list = await _get_user_subscription(uid)
    return subscribe_list


@error_handler()
@input_filter
async def get_subscription_info(request: dict, channel: str):
    uid = request["uid"]
    logger.debug(f'get {channel} subscription info')
    subscribe_info = await _get_subscription_info(uid, channel)
    return subscribe_info


@error_handler()
@input_filter
async def get_tg_user_subscription(request: dict):
    telegram_id = request["telegram_id"]
    logger.info(f"get tg user {telegram_id} subscription")
    subscribe_list = await _get_tg_user_subscription(telegram_id)
    return subscribe_list


@error_handler()
@input_filter
async def create_user_subscription(request: dict):
    uid = request["uid"]
    plan_id = request["plan_id"]
    subscription_id = await _create_user_subscription(uid, plan_id)
    logger.info(f"create user {uid} subscription {subscription_id}")
    return {"subscription_id": subscription_id}


@error_handler()
@input_filter
async def update_user_subscription(request: dict):
    uid = request["uid"]
    subscription_id = request["subscription_id"]
    expire_date = request["expire_date"]
    logger.info(f"update user {uid} subscription {subscription_id}")
    await _update_user_subscription(uid, subscription_id, expire_date)


@error_handler()
@input_filter
async def delete_user_subscription(request: dict):
    uid = request["uid"]
    subscription_id = request["subscription_id"]
    logger.info(f"delete user {uid} subscription {subscription_id}")
    await _delete_user_subscription(uid, subscription_id)
