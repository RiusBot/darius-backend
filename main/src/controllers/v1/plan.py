import logging
from aiohttp.web import json_response
from main.src.core.plan import _get_plan, _create_plan, _delete_plan, _update_plan
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


async def get_plan(request):

    json_payload = dict(request.rel_url.query)
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Get plan")
        uid = json_payload["uid"]
        plan_id = json_payload["plan_id"]
        plan = await _get_plan(uid, plan_id)
        return json_response(
            status=200,
            data=plan
        )
    except Exception as e:
        logger.error("Get plan error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def create_plan(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Create plan")
        uid = json_payload["uid"]
        name = json_payload["name"]
        channel = json_payload["channel"]
        price = json_payload["price"]
        day = json_payload["day"]
        plan_id = await _create_plan(uid, name, channel, price, day)
        return json_response(
            status=200,
            data={
                "plan_id": plan_id
            }
        )
    except Exception as e:
        logger.error("Create plan error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def update_plan(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Update plan")
        uid = json_payload["uid"]
        plan_id = json_payload["plan_id"]
        name = json_payload["name"]
        channel = json_payload["channel"]
        price = json_payload["price"]
        day = json_payload["day"]
        await _update_plan(uid, plan_id, name, channel, price, day)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update plan error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )


async def delete_plan(request):

    json_payload = await request.json()
    json_payload = filter_illegal_char(json_payload)

    try:
        logger.info("Delete plan")
        uid = json_payload["uid"]
        plan_id = json_payload["plan_id"]
        await _delete_plan(uid, plan_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete plan error.")
        logger.exception("")
        error_message = str(e) if isinstance(e, BackendException) else "Unexpected Error"
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': error_message
            }
        )
