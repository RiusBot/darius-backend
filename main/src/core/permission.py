import logging
from tortoise.transactions import atomic
from main.src.models import Permission, User, Role
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


def permission_validator(f, service):
    @wraps(f)
    @atomic()
    async def wrapper(uid, *args, **kwargs):
        # validate user
        user = await User.filter(is_del=False).filter(uid=uid).prefetch_related("role").first()
        if user is None:
            raise BackendException("Invalid uid")

        # validate permission
        permission_list = await user.role.permission.filter(is_del=False).filter(service__in=[service, "all"]).all()
        if not permission_list:
            raise BackendException("Invalid permission")
        return await f(*args, **kwargs)

    return wrapper


@atomic()
async def create_permission(api):
    role = await Role.filter(name="user").first()
    for path, endpoints in api.specification._spec["paths"].items():
        for method, endpoint in endpoints.items():
            operationId = endpoint['operationId']
            func_name = operationId.split('.')[-1]
            
            permission = await Permission.filter(service=func_name).filter(is_del=False).first()
            if permission is None:
                logger.info(func_name)
                await Permission.create(
                    role=role,
                    service=func_name
                )
