import logging
import threading
from aiohttp.web import json_response
from main.src.core.hyperopt import _get_hyperopt, _create_hyperopt
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_hyperopt(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        uid = json_payload["uid"]
        channel = json_payload["channel"]
        hyperopt = await _get_hyperopt(uid, channel)
        return json_response(
            status=200,
            data=hyperopt
        )
    except Exception as e:
        logger.error("Get hyperopt error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_hyperopt(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        thread = threading.Thread(
            target=_create_hyperopt,
            kwargs=json_payload,
            daemon=True
        )
        thread.start()
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Create hyperopt error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
