import logging
import threading
from main.src.core.hyperopt import _get_hyperopt, _create_hyperopt
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_hyperopt(request: dict):
    uid = request["uid"]
    channel = request["channel"]
    logger.info(f"get {channel} hyperopt")
    hyperopt = await _get_hyperopt(uid, channel)
    return hyperopt


@error_handler()
@input_filter
async def create_hyperopt(request: dict):
    logger.info("Create hyperopt")
    thread = threading.Thread(
        target=_create_hyperopt,
        daemon=True
    )
    thread.start()
