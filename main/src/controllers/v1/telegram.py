import logging
from main.src.core.telegram import _get_user_telegram, _create_user_telegram, _delete_user_telegram, _update_user_telegram, _check_tg_user_valid, _user_telegram_send_message
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_user_telegram(request: dict):
    uid = request["uid"]
    logger.debug(f"get user {uid} telegram")
    telegram_info = await _get_user_telegram(uid)
    return telegram_info


@error_handler()
@input_filter
async def check_tg_user_valid(request: dict):
    telegram_id = request["telegram_id"]
    chat_id = request["chat_id"]
    logger.debug(f"check tg user {chat_id} valid")
    valid = await _check_tg_user_valid(telegram_id, chat_id)
    return {"valid": valid}


@error_handler()
@input_filter
async def create_user_telegram(request: dict):
    uid = request["uid"]
    telegram_id = request['telegram_id']
    logger.info(f"create user {uid} telegram {telegram_id}")
    telegram_id = await _create_user_telegram(uid, telegram_id)
    return {"telegram_id": telegram_id}


@error_handler()
@input_filter
async def update_user_telegram(request: dict):
    uid = request["uid"]
    telegram_id = request["telegram_id"]
    logger.info(f"update user {uid} telegram {telegram_id}")
    await _update_user_telegram(uid, telegram_id)


@error_handler()
@input_filter
async def delete_user_telegram(request: dict):
    uid = request["uid"]
    logger.info(f"delete user {uid} telegram")
    await _delete_user_telegram(uid)


@error_handler()
@input_filter
async def user_telegram_send_message(request: dict):
    uid = request["uid"]
    msg = request["msg"]
    logger.info(f"send telegram message to user {uid}")
    await _user_telegram_send_message(uid, msg)
