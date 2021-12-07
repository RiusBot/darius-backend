import logging
from functools import wraps
from tortoise.transactions import atomic
from main.src.models import Plan, User
from main.src.models.plan import PlanSchemaModel


logger = logging.getLogger(__name__)


def user_permission_validator(f):
    @wraps(f)
    async def wrapper(uid, *args, **kwargs):
        # validate user permission
        user = await User.filter(is_del=False).filter(uid=uid).prefetch_related("role").first()
        if user is None:
            raise Exception("Invalid uid")

        # validate permission
        service = ["plan", "all", "test"]
        permission_list = await user.role.permission.filter(is_del=False).filter(service__in=service).all()
        if not permission_list:
            raise Exception("Invalid permission")
        return await f(*args, **kwargs)

    return wrapper


@atomic()
async def _get_plan(plan_id: int) -> Plan:
    logger.info(f"Get plan {plan_id}")
    plan = await Plan.filter(is_del=False).filter(id=plan_id).first()
    if plan is None:
        raise Exception("Invalid plan.")
    plan = await PlanSchemaModel.from_tortoise_orm(plan)
    plan = plan.dict()
    plan["plan_id"] = plan.pop("id")
    return plan


@atomic()
@user_permission_validator
async def _create_plan(name: str, channel: str, price: float, day: int) -> int:
    logger.info("Create new plan")
    plan = await Plan.create(
        name=name,
        channel=channel,
        price=price,
        day=day,
    )
    logger.info(f"Create plan [{plan.id}]")
    return plan.id


@atomic()
@user_permission_validator
async def _update_plan(plan_id: int, name: str, channel: str, price: float, day: int) -> int:
    logger.info(f"Update plan [{plan_id}]")
    plan = await Plan.filter(is_del=False).filter(id=plan_id).first()
    if plan is None:
        raise Exception("Invalid plan_id.")

    plan.name = name
    plan.channel = channel
    plan.price = price
    plan.day = day
    await plan.save()


@atomic()
@user_permission_validator
async def _delete_plan(plan_id: int) -> int:
    logger.info(f"Delete plan {plan_id}")
    plan = await Plan.filter(id=plan_id).filter(is_del=False).first()
    if plan is None:
        raise Exception("Invalid api_id")
    plan.is_del = True
    await plan.save()
