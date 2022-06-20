import logging
from main.src.core.plan import _get_plan, _get_plans, _create_plan, _delete_plan, _update_plan
from main.src.utils import error_handler, input_filter


logger = logging.getLogger(__name__)


@error_handler()
@input_filter
async def get_plan(request: dict, plan_id: int):
    logger.debug(f"get plan {plan_id}")
    uid = request["uid"]
    plan = await _get_plan(uid, plan_id)
    return plan


@error_handler()
@input_filter
async def get_plans(request: dict):
    uid = request["uid"]
    plan = await _get_plans(uid)
    return plan


@error_handler()
@input_filter
async def create_plan(request: dict):
    uid = request["uid"]
    name = request["name"]
    channel = request["channel"]
    price = request["price"]
    day = request["day"]
    plan_id = await _create_plan(uid, name, channel, price, day)
    logger.info(f"create plan {plan_id}")
    return {"plan_id": plan_id}


@error_handler()
@input_filter
async def update_plan(request: dict):
    uid = request["uid"]
    plan_id = request["plan_id"]
    name = request["name"]
    channel = request["channel"]
    price = request["price"]
    day = request["day"]
    logger.info(f"update plan {plan_id}")
    await _update_plan(uid, plan_id, name, channel, price, day)


@error_handler()
@input_filter
async def delete_plan(request: dict):
    uid = request["uid"]
    plan_id = request["plan_id"]
    logger.info(f"delete plan {plan_id}")
    await _delete_plan(uid, plan_id)
