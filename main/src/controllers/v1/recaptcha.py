import logging
from main.src.core.recaptcha import create_recaptcha_assessment
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def recaptcha_assessment(request: dict):
    token = request['token']
    action = request['action']
    logger.info(f'Create an recaptcha assessment action: {action}')
    await create_recaptcha_assessment(token, action)
