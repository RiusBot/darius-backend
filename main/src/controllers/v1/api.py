import logging
from main.src.core.api import _get_user_api, _create_user_api, _delete_user_api, _update_user_api, _clean_api
from . import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_user_api(request: dict):
    uid = request["uid"]
    logger.debug(f"Get user {uid} api")
    api_list = await _get_user_api(uid)
    return api_list


@error_handler()
@input_filter
async def create_user_api(request: dict):
    uid = request["uid"]
    logger.debug(f"Create user {uid} api")
    api_key = request["api_key"]
    api_secret = request["api_secret"]
    password = request.get("password")
    exchange = request["exchange"]
    subaccount = request.get("subaccount")
    api_id = await _create_user_api(uid, api_key, api_secret, password, exchange, subaccount)
    return {"api_id": api_id}


@error_handler()
@input_filter
async def update_user_api(request: dict):
    uid = request["uid"]
    api_id = request["api_id"]
    logger.debug(f"Update user {uid} api {api_id}")
    api_key = request["api_key"]
    api_secret = request["api_secret"]
    exchange = request["exchange"]
    subaccount = request.get("subaccount")
    api_id = await _update_user_api(uid, api_id, api_key, api_secret, exchange, subaccount)


@error_handler()
@input_filter
async def delete_user_api(request: dict):
    uid = request["uid"]
    api_id = request["api_id"]
    logger.debug(f"Delete user {uid} api {api_id}")
    await _delete_user_api(uid, api_id)


@error_handler()
@input_filter
async def clean_api(request: dict):
    logger.info("Clean api")
    await _clean_api()
