import logging
from main.src.core.account import _update_user_profile, _get_user_profile, _create_user, _delete_user
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def update_user_profile(request: dict):
    uid = request["uid"]
    user_name = request["user_name"]
    logger.debug(f"Update user {uid} profile")
    await _update_user_profile(uid, user_name)


@error_handler()
@input_filter
async def get_user_profile(request: dict):
    uid = request["uid"]
    logger.info(f"Get user {uid} profile")
    user_profile = await _get_user_profile(uid)
    return user_profile


@error_handler()
@input_filter
async def create_user(request: dict):
    uid = request["uid"]
    referrer = request.get("referrer")
    logger.info(f"Create user {uid} with referrer {referrer}")
    user_id = await _create_user(uid, referrer)
    return {"user_id": user_id}


@error_handler()
async def delete_user(request: dict):
    uid = request["uid"]
    delete_uid = request["delete_uid"]
    logger.info(f"User {uid} delete user {delete_uid}")
    await _delete_user(uid, delete_uid)
