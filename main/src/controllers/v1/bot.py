import logging
import asyncio
import threading
from aiohttp.web import json_response
from main.src.core.bot import _execute_bot_signal, _get_user_bots, _get_bot_trades, _create_user_bot, _delete_user_bot
from main.src.core.auth import authenticate


async def execute_bot_signal(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Start bot signal thread")
        thread = threading.Thread(
            target=_execute_bot_signal,
            args=(asyncio.get_event_loop(),),
            kwargs=json_payload,
            daemon=True
        )
        thread.start()

        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logging.error("bot singal error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def get_user_bots(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Start get user bots")
        user_id = json_payload["user_id"]
        bot_list = await _get_user_bots(user_id)
        return json_response(
            status=200,
            data=bot_list
        )
    except Exception as e:
        logging.error("Get user bots error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def get_bot_trades(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Get bot trades")
        bot_id = json_payload["bot_id"]
        trade_list = await _get_bot_trades(bot_id)
        return json_response(
            status=200,
            data=trade_list
        )
    except Exception as e:
        logging.error("Get bot trades error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def create_user_bot(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Create bot")
        user_id = json_payload["user_id"]
        channel = json_payload["channel"]
        api_id = json_payload["api_id"]
        config = json_payload["config"]
        bot_id = await _create_user_bot(user_id, channel, api_id, config)
        return json_response(
            status=200,
            data={
                "bot_id": bot_id
            }
        )
    except Exception as e:
        logging.error("Create bot error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def delete_user_bot(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logging.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Delete bot")
        user_id = json_payload["user_id"]
        bot_id = json_payload["bot_id"]
        await _delete_user_bot(user_id, bot_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logging.error("Delete bot error.")
        logging.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
