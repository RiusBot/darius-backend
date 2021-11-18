import logging
import threading
from aiohttp.web import json_response
from main.src.core.bot import execute_bot_signal
from main.src.core.auth import authenticate


async def bot_signal(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logging.info("Start bot signal thread")
        threading.Thread(target=execute_bot_signal, kwargs=json_payload, daemon=True).start()
        return json_response(
            status=200,
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
