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


def create_invite_link(channel: str) -> str:
    try:
        chat_id = getattr(ChannelID, channel, None)
        if chat_id is None:
            raise BackendException(f"{channel} channel has no chat_id")
        invite_link = TGBot.create_chat_invite_link(chat_id, member_limit=1)
        return invite_link.invite_link
    except Exception:
        raise BackendException("Create invite link failed")


def revoke_invite_link(channel: str, invite_link: str):
    if not invite_link:
        return
    try:
        chat_id = getattr(ChannelID, channel, None)
        if chat_id is None:
            raise BackendException(f"{channel} channel has no chat_id")
        TGBot.revoke_chat_invite_link(chat_id, invite_link)
    except Exception:
        raise BackendException("Revoke invite link failed")
