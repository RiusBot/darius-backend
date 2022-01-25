import logging
import asyncio
import threading
from datetime import datetime
from collections import defaultdict
from aiohttp.web import json_response
from main.src.core.bot import _execute_bot_signal, _get_user_bots, _get_bot_trades, _create_user_bot, _delete_user_bot, _execute_webhook_signal
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)
ThreadID = 0
BotStatus = defaultdict(dict)


async def get_executing_status(request):
    try:
        logger.info("Get execution thread status")
        return json_response(
            status=200,
            data={
                "bot_status": BotStatus
            }
        )
    except Exception as e:
        logger.error("Get bot status error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def execute_bot_signal(request):
    global ThreadID, BotStatus
    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Start bot signal thread")
        thread = threading.Thread(
            target=_execute_bot_signal,
            args=(asyncio.get_event_loop(), ThreadID, BotStatus),
            kwargs=json_payload,
            daemon=True
        )
        thread.start()
        ThreadID += 1

        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("bot singal error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def execute_webhook_signal(request, uid: str):
    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Start webhook signal")
        json_payload["uid"] = uid[::-1]
        json_payload["message_timestamp"] = datetime.now().timestamp()
        json_payload["recieve_timestamp"] = datetime.now().timestamp()
        json_payload["content"] = ""
        json_payload["channel"] = "WEBHOOK"
        await _execute_webhook_signal(**json_payload)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("webhook singal error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def get_user_bots(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Start get user bots")
        uid = json_payload["uid"]
        bot_list = await _get_user_bots(uid)
        return json_response(
            status=200,
            data=bot_list
        )
    except Exception as e:
        logger.error("Get user bots error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def get_bot_trades(request):

    json_payload = json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get bot trades")
        uid = json_payload["uid"]
        bot_id = json_payload["bot_id"]
        trade_list = await _get_bot_trades(uid, bot_id)
        return json_response(
            status=200,
            data=trade_list
        )
    except Exception as e:
        logger.error("Get bot trades error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_bot(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Create bot")
        uid = json_payload["uid"]
        channel = json_payload["channel"]
        config = json_payload["config"]
        bot_id = await _create_user_bot(uid, channel, config)
        return json_response(
            status=200,
            data={
                "bot_id": bot_id
            }
        )
    except Exception as e:
        logger.error("Create bot error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_bot(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Delete bot")
        uid = json_payload["uid"]
        bot_id = json_payload["bot_id"]
        await _delete_user_bot(uid, bot_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete bot error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
