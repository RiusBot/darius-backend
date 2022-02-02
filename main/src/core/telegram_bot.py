import logging
import telegram
import functools
from firebase_admin import firestore

from main.src.models.channel import ChannelID
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=None)
def fetch_secret_token_firestore():
    db = firestore.Client()
    Secret = db.collection("config").document("backend").get().to_dict()
    Token = Secret['tg_token']
    return Token


TGBot = telegram.Bot(token=fetch_secret_token_firestore())


def create_invite_link(channel: str, telegram) -> str:
    try:
        chat_id = getattr(ChannelID, channel, "")
        if chat_id == "":
            logger.info(f"{channel} channel has no chat_id")
            return
            raise BackendException(f"{channel} channel has no chat_id")

        if telegram is not None:
            if not TGBot.unban_chat_member(chat_id, telegram.telegram_id, only_if_banned=True):
                logger.info(f"{channel} unban user failed")

        invite_link = TGBot.create_chat_invite_link(chat_id, creates_join_request=True)
        return invite_link.invite_link
    except Exception:
        raise BackendException("Create invite link failed")


def revoke_invite_link(channel: str, invite_link: str):
    if not invite_link:
        return
    try:
        chat_id = getattr(ChannelID, channel, None)
        if chat_id is None:
            logger.info(f"{channel} channel has no chat_id")
            return
        TGBot.revoke_chat_invite_link(chat_id, invite_link)
    except Exception:
        raise BackendException("Revoke invite link failed")


def kick_user(channel: str, telegram):
    if telegram is None:
        return
    try:
        chat_id = getattr(ChannelID, channel, None)
        if chat_id is None:
            logger.info(f"{channel} channel has no chat_id")
            return
        if not TGBot.ban_chat_member(chat_id, telegram.telegram_id):
            raise BackendException(f"ban chat {chat_id} member {telegram.telegram_id} failed")
    except Exception:
        raise BackendException(f"kick user {telegram.telegram_id} from chat {chat_id} failed")
