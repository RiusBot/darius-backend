import logging

from aiohttp.web import json_response

from main.src.core.recaptcha import create_recaptcha_assessment
from main.src.core.validator import filter_illegal_char
from main.src.exception import BackendException

logger = logging.getLogger(__name__)


async def recaptcha_assessment(request):
    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        token = json_payload['token']
        action = json_payload['action']
        logger.info('Create an recaptcha assessment action: %s', action)
        await create_recaptcha_assessment(token, action)
        return json_response(
            status=200,
            data={}
        )
    except Exception as ex:
        logger.exception("Recaptcha assessment error. due to: %s", ex)
        error_message = str(ex) if isinstance(ex, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
