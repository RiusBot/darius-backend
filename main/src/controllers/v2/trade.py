import logging
from main.src.core.trade import _get_bot_trades2
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter()
async def get_bot_trades(request: dict):
    uid = request["uid"]
    bot_id = request["bot_id"]
    logger.debug(f"Get user {uid} bot trades {bot_id}")
    page = int(request.get("page", 0))
    pagesize = int(request.get("pagesize", 20))
    trade_list = await _get_bot_trades2(uid, bot_id, page, pagesize)
    return trade_list
