import logging
import asyncio
from main.src.core.performance import _get_performance, _create_performance, _get_performances
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter()
async def get_performance(request: dict, channel: str):
    logger.debug(f"get {channel} performance")
    performance = await _get_performance(channel)
    return performance


@error_handler()
@input_filter()
async def get_performances(request: dict):
    logger.debug("get performances")
    performances = await _get_performances()
    return performances


@error_handler()
@input_filter()
async def create_performance(request: dict):
    logger.info("create performance")
    asyncio.create_task(_create_performance())
