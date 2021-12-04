import logging
from email_validator import validate_email
from tortoise.transactions import atomic
from main.src.models import User, Role
from main.src.models.user import UserSchemaModel


logger = logging.getLogger(__name__)


def my_validate_email(email: str):
    try:
        # email normalized
        prefix, postfix = email.rsplit('@', 1)
        prefix = re.compile('[^a-zA-Z0-9]').sub('', prefix)
        norm_email = f"{prefix}@{postfix}"
        # check email format
        email = validate_email(email).email
        # check email exist
        return True
    except Exception:
        logger.error("Validate email error")
        logger.exception("")
        raise Exception("Invalid email")


@atomic()
async def _update_user_profile(user_id: int, user_name: str, email: str):
    user = await User.filter(id=user_id).first()
    if user is None:
        raise Exception("Invalid user_id")
    user.user_name = user_name
    user.email = email
    await user.save()


@atomic()
async def _get_user_profile(user_id: int):
    user = await User.filter(id=user_id).first()
    if user is None:
        raise Exception("Invalid user_id")
    user = await UserSchemaModel.from_tortoise_orm(user)
    user = user.dict()
    user["user_id"] = user.pop("id")
    return user


@atomic()
async def _create_user(uid: str):

    role = await Role.filter(is_del=False).filter(name="user").first()
    user = await User.filter(uid=uid).first()
    if user:
        logger.info("User %s was created before, will activate user", user)
        user.is_del = False
        return user
    user = await User.create(
        uid=uid,
        role=role,
    )
    logger.info(f"Create user [{user.id}]")
    return user.id


@atomic()
async def _delete_user(uid: str):
    user = await User.filter(uid=uid).first()
    if user is None:
        raise Exception("Invalid user_id")
    user.is_del = True
    await user.save()
