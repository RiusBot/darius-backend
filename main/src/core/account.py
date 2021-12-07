import re
import logging
from email_validator import validate_email
from tortoise.transactions import atomic
from main.src.models import User, Role
from main.src.models.user import UserSchemaModel


logger = logging.getLogger(__name__)


def email_normalize_and_validate(email: str):
    try:
        # email normalized
        prefix, postfix = email.rsplit('@', 1)
        prefix = re.compile('[^a-zA-Z0-9]').sub('', prefix)
        norm_email = f"{prefix}@{postfix}"
        # check email format
        email = validate_email(email).email
        # check email exist
        # TODO
        return email
    except Exception:
        logger.error("Validate email error")
        logger.exception("")
        raise Exception("Invalid email")


@atomic()
async def _update_user_profile(uid: str, user_name: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise Exception("Invalid uid")
    user.user_name = user_name
    await user.save()


@atomic()
async def _get_user_profile(uid: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise Exception("Invalid uid")
    user = await UserSchemaModel.from_tortoise_orm(user)
    user = user.dict()
    return user


@atomic()
async def _create_user_profile(uid: str, user_name: str, email: str):

    email = email_normalize_and_validate(email)

    role = await Role.filter(is_del=False).filter(name="user").first()
    user = await User.create(
        uid=uid,
        user_name=user_name,
        email=email,
        role=role,
    )
    logger.info(f"Create user [{user.id}]")
    return user.id


@atomic()
async def _delete_user_profile(uid: str, delete_uid: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise Exception("Invalid uid")
    
    # validate user permission
    # TODO
    
    user = await User.filter(uid=delete_uid).first()
    if delete_uid is None:
        raise Exception("Invalid delete_uid")
    user.is_del = True
    await user.save()
