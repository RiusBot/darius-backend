import json
import logging
import aiohttp
import functools
from firebase_admin import firestore
from tortoise.transactions import atomic

from main.src.models import User, Telegram
from main.src.models.telegram import TelegramSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.models.channel import ChannelID
from main.src.core.telegram_bot import get_chat_info, send_message


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def fetch_telegram_bot_token_firestore():
    db = firestore.Client()
    config = db.collection("config").document("backend").get().to_dict()
    doc = "telegram_bot_token"
    if doc not in config:
        raise BackendException("Fetch telegram bot token from firestore failed")
    return config[doc]


async def _user_telegram_send_message(uid: str, msg: str):
    logger.info(f"Send telegram msg to user {uid}")
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException(f"Invalid uid {uid}")
    bind_telegram = await user.telegram_user.all().first()
    if bind_telegram is None:
        raise BackendException("User has no bind telegram")
    send_message(bind_telegram.telegram_id, msg=msg)


@atomic()
@permission_validator("update_user_telegram")
async def _update_user_telegram(user: User, telegram_id: int):
    logger.info(f"Update telegram info user {user.uid}")
    bind_telegram = await user.telegram_user.all().first()
    if bind_telegram is None:
        raise BackendException("User has no bind telegram")

    logger.info(f"Update telegram for user [{user.uid}], {bind_telegram.telegram_id} --> {telegram_id}")
    bind_telegram.telegram_id = telegram_id
    await bind_telegram.save()


@atomic()
@permission_validator("get_user_telegram")
async def _get_user_telegram(user: User):
    logger.info(f"Get telegram info user {user.uid}")
    bind_telegram = await user.telegram_user.all().first()
    if bind_telegram is None:
        return {}

    bind_telegram = await TelegramSchemaModel.from_tortoise_orm(bind_telegram)
    telegram_info = bind_telegram.dict()

    # add addition info
    chat = get_chat_info(telegram_info["telegram_id"])
    telegram_info["username"] = chat.get("username")
    telegram_info["name"] = chat.get("first_name", "") + " " + chat.get("last_name", "")
    telegram_info.pop("created_at")
    return telegram_info


async def _check_tg_user_valid(telegram_id: str, chat_id: str):
    logger.info(f"Check telegram user_id: {telegram_id}")

    # get user with this user_id
    tg = await Telegram.filter(telegram_id=telegram_id).prefetch_related("user").first()
    if tg is None:
        raise BackendException(f"{telegram_id} not found.")

    try:
        channel = ChannelID(chat_id).name
        valid = await tg.user.subscription_user.filter(plan__channel=channel, is_del=False).exists()
        return valid
    except Exception:
        raise BackendException(f"Invalid chat_id {chat_id}")


async def fetch_alphashark(telegram_id: int):
    try:
        url = "https://us-central1-alpha-shark-bot.cloudfunctions.net/checkHasShark"
        params = {'tg_id': telegram_id}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                resp_text = await response.text()
                resp_json = json.loads(resp_text)
                logger.info(f'{resp_json}')
                return resp_json.get("has_shark", False)
    except Exception:
        logger.exception("")
        logger.error("Fetch alphashark error")


@atomic()
async def alphashark_campaign(user: User, telegram_id: int):
    if await fetch_alphashark(telegram_id):
        logger.info(f"user [{user.id}] is alphashark holder !")
        # acquire lock
        user = await user.filter(id=user.id).select_for_update().first()
        user.balance += 100
        await user.save()


@atomic()
@permission_validator("create_user_telegram")
async def _create_user_telegram(user: User, telegram_id: int):
    uid = user.uid
    logger.info(f"Bind telegram for user [{uid}]")

    # validate telegram_id is already bind
    if (await Telegram.filter(telegram_id=telegram_id).exists()):
        raise BackendException(f"Telegram_id {telegram_id} already bind.")

    # create
    bind_telegram, create = await Telegram.get_or_create(
        defaults={
            "telegram_id": telegram_id
        },
        user=user,
    )
    if not create:
        raise BackendException(f"User already bind {bind_telegram.telegram_id}")

    await alphashark_campaign(user, telegram_id)

    logger.info(f"Create telegram [{bind_telegram.telegram_id}]")
    return bind_telegram.telegram_id


@atomic()
@permission_validator("delete_user_telegram")
async def _delete_user_telegram(user: User):
    uid = user.uid
    bind_telegram = await user.telegram_user.all().first()
    if bind_telegram is None:
        raise BackendException("User has no bind telegram")

    logger.info(f"Delete telegram [{bind_telegram.telegram_id}] for user {uid}")
    await bind_telegram.delete()
