import logging
from aiohttp.web import json_response
from main.src.core.pair import _get_user_pair, _create_user_pair, _delete_user_pair, _update_user_pair
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_user_pair(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get user pair")
        uid = json_payload["uid"]
        pair_list = await _get_user_pair(uid)
        return json_response(
            status=200,
            data=pair_list
        )
    except Exception as e:
        logger.error("Get user pair error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_user_pair(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Create user pair")
        uid = json_payload["uid"]
        name = json_payload["name"]
        types = json_payload["types"]
        lists = json_payload.get("lists")
        pair_id = await _create_user_pair(uid, name, types, lists)
        return json_response(
            status=200,
            data={
                "pair_id": pair_id
            }
        )
    except Exception as e:
        logger.error("Create pair error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_user_pair(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Update user pair")
        uid = json_payload["uid"]
        pair_id = json_payload["pair_id"]
        name = json_payload["name"]
        types = json_payload["types"]
        lists = json_payload.get("lists")
        pair_id = await _update_user_pair(uid, pair_id, name, types, lists)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update pair error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_user_pair(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Delete pair")
        uid = json_payload["uid"]
        pair_id = json_payload["pair_id"]
        await _delete_user_pair(uid, pair_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete pair error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
