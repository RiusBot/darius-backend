import os
import logging
import functools
from base64 import b64encode
from cryptography.fernet import Fernet
from main.src.core.auth import fetch_secret_token_firestore


usingProjectId = os.getenv('project_id', 'local')
logger = logging.getLogger(__name__)


def pad_seg_encode(b_api_key: bytes) -> bytes:
    # padding
    b_api_key += b" " * max((32 - len(b_api_key)), 0)
    # segment
    b_api_key = b_api_key[:32]
    # encode
    cipherkey = b64encode(b_api_key)
    return cipherkey


def encrypt(api_key: str, api_secret: str) -> str:
    b_token = fetch_secret_token_firestore().encode("utf-8")
    b_api_key = api_key.encode("utf-8")
    b_api_secret = api_secret.encode("utf-8")

    cipher_key = pad_seg_encode(b_api_key)
    cipher_suite = Fernet(cipher_key)
    ciphered_text = cipher_suite.encrypt(b_api_secret)

    cipher_key = pad_seg_encode(b_token)
    cipher_suite = Fernet(cipher_key)
    ciphered_text = cipher_suite.encrypt(ciphered_text)

    return ciphered_text.decode("utf-8")


@functools.lru_cache(maxsize=1024)
def decrypt(api_key: str, ciphered_api_secret: str) -> str:
    b_token = fetch_secret_token_firestore().encode("utf-8")
    b_api_key = api_key.encode("utf-8")
    b_ciphered_api_secret = ciphered_api_secret.encode("utf-8")

    cipher_key = pad_seg_encode(b_token)
    cipher_suite = Fernet(cipher_key)
    unciphered_text = cipher_suite.decrypt(b_ciphered_api_secret)

    cipher_key = pad_seg_encode(b_api_key)
    cipher_suite = Fernet(cipher_key)
    unciphered_text = cipher_suite.decrypt(unciphered_text)

    return unciphered_text.decode("utf-8")
