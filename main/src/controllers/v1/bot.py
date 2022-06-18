import logging
import asyncio
from datetime import datetime
from main.src.core.bot import _execute_bot_signal, _get_user_bots, _create_user_bot, _delete_user_bot, _execute_webhook_signal, _update_user_bot, _get_user_history_bots
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def execute_bot_signal(request: dict):
    logger.info("Start bot signal execute")
    asyncio.create_task(_execute_bot_signal(**request))


@error_handler()
@input_filter
async def execute_webhook_signal(request, bot_id: int):
    logger.info(f"Start webhook signal {bot_id}")
    request["bot_id"] = bot_id
    request["uid"] = request.pop('token')[::-1]
    request["message_timestamp"] = datetime.now().timestamp()
    request["recieve_timestamp"] = datetime.now().timestamp()
    request["content"] = ""
    request["channel"] = "WEBHOOK"
    asyncio.create_task(_execute_webhook_signal(**request))


@error_handler()
@input_filter
async def get_user_bots(request: dict):
    uid = request["uid"]
    logger.info(f"get user {uid} bots")
    bot_list = await _get_user_bots(uid)
    return bot_list


@error_handler()
@input_filter
async def get_user_history_bots(request: dict):
    uid = request["uid"]
    logger.info(f"Get user {uid} history bots")
    page = int(request.get("page", 0))
    pagesize = int(request.get("pagesize", 20))
    bot_history = await _get_user_history_bots(uid, page, pagesize)
    return bot_history


@error_handler()
@input_filter
async def create_user_bot(request: dict):
    uid = request["uid"]
    logger.info(f"Create user {uid} bot")
    channel = request["channel"]
    config = request["config"]
    bot_id = await _create_user_bot(uid, channel, config)
    return {"bot_id": bot_id}


@error_handler()
@input_filter
async def update_user_bot(request: dict):
    uid = request["uid"]
    bot_id = request["bot_id"]
    logger.info(f"Update user {uid} bot {bot_id}")
    config = request["config"]
    status = request.get("status")
    await _update_user_bot(uid, bot_id, config, status)


@error_handler()
@input_filter
async def delete_user_bot(request: dict):
    uid = request["uid"]
    bot_id = request["bot_id"]
    logger.info(f"Delete user {uid} bot {bot_id}")
    await _delete_user_bot(uid, bot_id)
