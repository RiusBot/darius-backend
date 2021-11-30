import logging
from aiohttp.web import json_response
from main.src.core.plan import _get_plan, _create_plan, _delete_plan, _update_plan
from main.src.core.auth import authenticate


logger = logging.getLogger(__name__)


async def get_plan(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Get plan")
        user_id = json_payload["user_id"]
        plan_id = json_payload["plan_id"]
        plan = await _get_plan(user_id, plan_id)
        return json_response(
            status=200,
            data=plan
        )
    except Exception as e:
        logger.error("Get plan error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def create_plan(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Create plan")
        user_id = json_payload["user_id"]
        name = json_payload["name"]
        channel = json_payload["channel"]
        price = json_payload["price"]
        day = json_payload["day"]
        plan_id = await _create_plan(user_id, name, channel, price, day)
        return json_response(
            status=200,
            data={
                "plan_id": plan_id
            }
        )
    except Exception as e:
        logger.error("Create plan error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def update_plan(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Update plan")
        user_id = json_payload["user_id"]
        plan_id = json_payload["plan_id"]
        name = json_payload["name"]
        channel = json_payload["channel"]
        price = json_payload["price"]
        day = json_payload["day"]
        await _update_plan(user_id, plan_id, name, channel, price, day)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Update plan error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )


async def delete_plan(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        logger.error("access token is not valid")
        response_data = {
            "error_message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    try:
        logger.info("Delete plan")
        user_id = json_payload["user_id"]
        plan_id = json_payload["plan_id"]
        await _delete_plan(user_id, plan_id)
        return json_response(
            status=200,
            data={}
        )
    except Exception as e:
        logger.error("Delete plan error.")
        logger.exception("")
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(e)
            }
        )
