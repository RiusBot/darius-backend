import logging
from main.src.core.notify import _get_user_notify, _update_user_notify
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter()
async def get_user_notify(request: dict):
    uid = request["uid"]
    logger.info(f"Get user {uid} notify")
    notify_config = await _get_user_notify(uid)
    return notify_config


@error_handler()
@input_filter()
async def update_user_notify(request: dict):
    uid = request["uid"]
    logger.info(f"update user {uid} notify")
    notify_config = request["config"]
    await _update_user_notify(uid, notify_config)
