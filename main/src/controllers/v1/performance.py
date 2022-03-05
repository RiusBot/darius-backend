import logging
import threading
from aiohttp.web import json_response
from main.src.core.performance import _get_performance, _create_performance
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_performance(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        channel = json_payload["channel"]
        performance = await _get_performance(channel)
        return json_response(
            status=200,
            data=performance
        )
    except Exception as e:
        logger.error("Get performance error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_performance(request):

    try:
        thread = threading.Thread(
            target=_create_performance,
            daemon=True
        )
        thread.start()
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Create performance error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
