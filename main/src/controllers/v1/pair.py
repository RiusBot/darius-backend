import logging
from main.src.core.pair import _get_user_pair, _create_user_pair, _delete_user_pair, _update_user_pair, _get_all_pair
from main.src.core.pair import _get_builtin_pair, _create_builtin_pair, _delete_builtin_pair, _update_builtin_pair
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_all_pair(request: dict):
    uid = request["uid"]
    logger.info(f"Get user {uid} pair")
    all_pair_list = await _get_all_pair(uid)
    return all_pair_list


@error_handler()
@input_filter
async def get_user_pair(request):
    uid = request["uid"]
    logger.info(f"Get user {uid} pair")
    pair_list = await _get_user_pair(uid)
    return pair_list


@error_handler()
@input_filter
async def create_user_pair(request: dict):
    uid = request["uid"]
    logger.info(f"Create user {uid} pair")
    name = request["name"]
    types = request["types"]
    lists = request.get("lists")
    pair_id = await _create_user_pair(uid, name, types, lists)
    return {"pair_id": pair_id}


@error_handler()
@input_filter
async def update_user_pair(request: dict):
    uid = request["uid"]
    logger.info(f"Update user {uid} pair")
    pair_id = request["pair_id"]
    name = request["name"]
    types = request["types"]
    lists = request.get("lists")
    pair_id = await _update_user_pair(uid, pair_id, name, types, lists)


@error_handler()
@input_filter
async def delete_user_pair(request: dict):
    uid = request["uid"]
    logger.info(f"Delete user {uid} pair")
    pair_id = request["pair_id"]
    await _delete_user_pair(uid, pair_id)


@error_handler()
@input_filter
async def get_builtin_pair(request: dict):
    logger.debug("Get builtin pair")
    uid = request["uid"]
    pair_list = await _get_builtin_pair(uid)
    return pair_list


@error_handler()
@input_filter
async def create_builtin_pair(request: dict):
    logger.info("Create builtin pair")
    uid = request["uid"]
    name = request["name"]
    types = request["types"]
    lists = request.get("lists")
    pair_id = await _create_builtin_pair(uid, name, types, lists)
    return {"pair_id": pair_id}


@error_handler()
@input_filter
async def update_builtin_pair(request: dict):
    uid = request["uid"]
    pair_id = request["pair_id"]
    name = request["name"]
    types = request["types"]
    lists = request.get("lists")
    logger.info(f"Update builtin pair {pair_id}")
    pair_id = await _update_builtin_pair(uid, pair_id, name, types, lists)


@error_handler()
@input_filter
async def delete_builtin_pair(request: dict):
    uid = request["uid"]
    pair_id = request["pair_id"]
    logger.info(f"Delete builtin pair {pair_id}")
    await _delete_builtin_pair(uid, pair_id)
