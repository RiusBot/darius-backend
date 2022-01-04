import logging
import telegram
import functools
from firebase_admin import firestore
from tortoise.transactions import atomic

from main.src.models import User, Telegram
from main.src.models.telegram import TelegramSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def fetch_telegram_bot_token_firestore():
    db = firestore.Client()
    config = db.collection("config").document("backend").get().to_dict()
    doc = "telegram_bot_token"
    if doc not in config:
        raise BackendException("Fetch telegram bot token from firestore failed")
    return config[doc]


TGBot = telegram.Bot(token=fetch_telegram_bot_token_firestore())


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
    try:
        chat = TGBot.get_chat(telegram_info["telegram_id"]).to_dict()
    except Exception:
        chat = {}
    telegram_info["username"] = chat.get("username")
    return telegram_info


@atomic()
@permission_validator("create_user_telegram")
async def _create_user_telegram(user: User, telegram_id: int, token: str):
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
