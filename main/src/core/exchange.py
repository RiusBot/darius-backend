import ccxt
import functools
from firebase_admin import firestore
from main.src.core.cipher import decrypt


@functools.lru_cache(maxsize=None)
def fetch_api_firestore(exchange: str):
    db = firestore.Client()
    Secret = db.collection("config").document("backend").get().to_dict()
    api_key = Secret[f'{exchange}_api_key']
    api_secret = Secret[f'{exchange}_api_secret']
    api_secret = decrypt(api_key, api_secret)
    return (api_key, api_secret)


def init_exchange(exchange: str):
    # read only api keys
    api_key, api_secret = fetch_api_firestore(exchange)
    return getattr(ccxt, exchange)({
        "enableRateLimit": True,
        "api_key": api_key,
        "api_secret": api_secret,
        "options": {
            "defaultType": "spot"
        }
    })
    return exchange


Exchange = init_exchange('binance')
