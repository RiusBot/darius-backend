import re
import random
import string
import logging
from datetime import datetime, timedelta
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


def generate_referral_code(k=8):
    return ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits,
        k=k,
    ))


@atomic()
@permission_validator("update_user_profile")
async def _update_user_profile(user: User, user_name: str, referrer: str):
    logger.info(f"Update profile user {user.uid}")
    user.user_name = user_name

    if referrer:
        if user.referrer is not None:
            raise BackendException("Referrer exists")
        if user.referral_code == referrer:
            raise BackendException("Don't referrer yourself")
        if (await User.filter(referrer=referrer, is_del=False).exists()):
            user.referrer = referrer
        else:
            raise BackendException(f"Referrer code {referrer} not exists")

    await user.save()


@atomic()
@permission_validator("get_user_profile")
async def _get_user_profile(user: User):
    logger.info(f"Get profile user {user.uid}")

    # get referral count
    referral_code = user.referral_code
    referral_cnt = await User.filter(is_del=False, referrer=referral_code).count()
    telegram = await user.telegram_user.filter(is_del=False).first()

    role = user.role.name
    user = await UserSchemaModel.from_tortoise_orm(user)
    user = user.dict()
    user["role"] = role
    user["referral_count"] = referral_cnt

    user["is_trial"] = False
    user["trial_period"] = None
    if telegram and (telegram.created_at + timedelta(days=30)).timestamp() > datetime.now().timestamp():
        user["trial_period"] = (telegram.created_at + timedelta(days=30)).strftime("%Y-%m-%d")
        user["is_trial"] = True
    return user


@atomic()
async def _create_user(uid: str, referrer: str = None):
    user = await User.filter(uid=uid).first()
    if user:
        logger.info("User %s was created before, will activate user", user)
        user.is_del = False
        return user.id

    referral_code = None
    for _ in range(10):
        referral_code = generate_referral_code()
        if (await User.filter(referral_code=referral_code).exists()):
            continue
    if referral_code is None:
        raise BackendException("Cannot generate referral_code")

    if not (await User.filter(referrer=referrer, is_del=False).exists()):
        logger.error(f"Referrer code {referrer} not exists")
        referrer = None

    role = await Role.filter(is_del=False, name="user").first()
    user = await User.create(
        uid=uid,
        role=role,
        referrer=referrer,
        referral_code=referral_code,
        referrer_count=0
    )
    logger.info(f"Create user [{user.id}]")
    return user.id


@atomic()
@permission_validator("delete_user")
async def _delete_user(user: User, delete_uid: str):
    logger.info(f"Delete user [{delete_uid}]")
    user = await User.filter(uid=delete_uid).first()
    if delete_uid is None:
        raise BackendException("Invalid delete_uid")
    user.is_del = True
    await user.save()
