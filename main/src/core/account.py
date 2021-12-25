import re
import logging
from email_validator import validate_email
from tortoise.transactions import atomic
from main.src.models import User, Role
from main.src.models.user import UserSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


def email_normalize_and_validate(email: str):
    try:
        # email normalized
        prefix, postfix = email.rsplit('@', 1)
        prefix = re.compile('[^a-zA-Z0-9]').sub('', prefix)
        norm_email = f"{prefix}@{postfix}"
        # check email format
        email = validate_email(norm_email).email
        # check email exist
        # TODO
        return email
    except Exception:
        logger.error("Validate email error")
        logger.exception("")
        raise BackendException("Invalid email")


@atomic()
@permission_validator("update_user_profile")
async def _update_user_profile(uid: str, user_name: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException("Invalid uid")
    user.user_name = user_name
    await user.save()


@atomic()
@permission_validator("get_user_profile")
async def _get_user_profile(uid: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException("Invalid uid")
    user = await UserSchemaModel.from_tortoise_orm(user)
    user = user.dict()
    return user


@atomic()
async def _create_user(uid: str):
    role = await Role.filter(is_del=False).filter(name="user").first()
    user = await User.filter(uid=uid).first()
    if user:
        logger.info("User %s was created before, will activate user", user)
        user.is_del = False
        return user.id
    user = await User.create(
        uid=uid,
        role=role,
    )
    logger.info(f"Create user [{user.id}]")
    return user.id


@atomic()
@permission_validator("delete_user")
async def _delete_user(uid: str, delete_uid: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate user permission
    # TODO: only admin
    raise BackendException("Invalid permission")

    user = await User.filter(uid=delete_uid).first()
    if delete_uid is None:
        raise BackendException("Invalid delete_uid")
    user.is_del = True
    await user.save()
