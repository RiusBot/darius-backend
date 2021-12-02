import logging
from tortoise.transactions import atomic
from main.src.models import User, Role
from main.src.models.user import UserSchemaModel


logger = logging.getLogger(__name__)


def validate_email(email: str):
    # email normalized
    # check email exist
    return True


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
async def _create_user_profile(user_name: str, email: str, password: str):

    validate_email(email)

    role = await Role.filter(is_del=False).filter(name="user").first()
    user = await User.create(
        user_name=user_name,
        email=email,
        password=password,
        role=role,
    )
    logger.info(f"Create user [{user.id}]")
    return user.id


@atomic()
async def _delete_user_profile(user_id: int):
    user = await User.filter(id=user_id).first()
    if user is None:
        raise Exception("Invalid user_id")
    user.is_del = True
    await user.save()
