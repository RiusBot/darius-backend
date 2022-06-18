import logging
from main.src.core.referral import _get_user_referral_info, _get_user_referral_history, _update_user_referral_info
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_user_referral_info(request: dict):
    uid = request["uid"]
    logger.info("Get user {uid} referral info")
    referral_info = await _get_user_referral_info(uid)
    return referral_info


@error_handler()
@input_filter
async def get_user_referral_history(request: dict):
    uid = request["uid"]
    logger.info(f"Get user {uid} referral history")
    page = int(request.get("page", 0))
    pagesize = int(request.get("pagesize", 20))
    referral_history = await _get_user_referral_history(uid, page, pagesize)
    return referral_history


@error_handler()
@input_filter
async def update_user_referral_info(request: dict):
    uid = request["uid"]
    logger.info(f"update user {uid} referral info")
    referrer_rebate_rate = request["referrer_rebate_rate"]
    referral_rebate_rate = request["referral_rebate_rate"]
    await _update_user_referral_info(uid, referrer_rebate_rate, referral_rebate_rate)
