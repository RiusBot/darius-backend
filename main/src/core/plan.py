import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from main.src.models import Plan, User
from main.src.models.plan import PlanSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_plan")
async def _get_plan(user: User, plan_id: int) -> Plan:
    logger.info(f"Get plan {plan_id}")
    plan = await Plan.filter(is_del=False).filter(id=plan_id).first()
    if plan is None:
        raise BackendException("Invalid plan.")
    plan = await PlanSchemaModel.from_tortoise_orm(plan)
    plan = plan.dict()
    plan["plan_id"] = plan.pop("id")
    return plan


@atomic()
@permission_validator("get_plan")
async def _get_plans(user: User) -> Plan:
    logger.info("Get plans")
    Plan_Pydantic_List = pydantic_queryset_creator(
        Plan,
        include=["id", "price", "name", "channel", "price", "day"]
    )
    plan_list = await Plan_Pydantic_List.from_queryset(Plan.filter(is_del=False))
    plan_list = json.loads(plan_list.json())
    for plan in plan_list:
        plan["plan_id"] = plan.pop("id")
    return plan_list


@atomic()
@permission_validator("create_plan")
async def _create_plan(user: User, name: str, channel: str, price: float, day: int) -> int:
    logger.info("Create plan")
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
async def _update_plan(user: User, plan_id: int, name: str, channel: str, price: float, day: int) -> int:
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
async def _delete_plan(user: User, plan_id: int) -> int:
    logger.info(f"Delete plan {plan_id}")
    plan = await Plan.filter(id=plan_id).filter(is_del=False).first()
    if plan is None:
        raise BackendException("Invalid plan_id")
    plan.is_del = True
    await plan.save()
