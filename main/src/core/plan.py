import logging
from functools import wraps
from tortoise.transactions import atomic
from main.src.models import Plan, User
from main.src.models.plan import PlanSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_plan")
async def _get_plan(plan_id: int) -> Plan:
    logger.info(f"Get plan {plan_id}")
    plan = await Plan.filter(is_del=False).filter(id=plan_id).first()
    if plan is None:
        raise BackendException("Invalid plan.")
    plan = await PlanSchemaModel.from_tortoise_orm(plan)
    plan = plan.dict()
    plan["plan_id"] = plan.pop("id")
    return plan


@atomic()
@permission_validator("create_plan")
async def _create_plan(name: str, channel: str, price: float, day: int) -> int:
    logger.info("Create new plan")
    import pdb
    pdb.set_trace()
    plan = await Plan.create(
        name=name,
        channel=channel,
        price=price,
        day=day,
    )
    logger.info(f"Create plan [{plan.id}]")
    return plan.id


@atomic()
@permission_validator("update_plan")
async def _update_plan(plan_id: int, name: str, channel: str, price: float, day: int) -> int:
    logger.info(f"Update plan [{plan_id}]")
    plan = await Plan.filter(is_del=False).filter(id=plan_id).first()
    if plan is None:
        raise BackendException("Invalid plan_id.")

    plan.name = name
    plan.channel = channel
    plan.price = price
    plan.day = day
    await plan.save()


@atomic()
@permission_validator("delete_plan")
async def _delete_plan(plan_id: int) -> int:
    logger.info(f"Delete plan {plan_id}")
    plan = await Plan.filter(id=plan_id).filter(is_del=False).first()
    if plan is None:
        raise BackendException("Invalid api_id")
    plan.is_del = True
    await plan.save()
