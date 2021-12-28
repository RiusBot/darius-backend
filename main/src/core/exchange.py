import ccxt
import logging
import functools
from typing import List
from firebase_admin import firestore
from dateutil.parser import parse as parse_date
from cachetools import cached, TTLCache

from main.src.core.cipher import decrypt
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


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
        "apiKey": api_key,
        "secret": api_secret,
        "options": {
            "defaultType": "spot"
        }
    })
    return exchange


@cached(cache=TTLCache(maxsize=256, ttl=600))
def get_deposit_history(transaction_date: str) -> List[dict]:
    global Exchange
    try:
        transaction_date = parse_date(transaction_date)
        start_timestamp = int(transaction_date.timestamp() * 1000) - (86400 * 1000)
        end_timestamp = start_timestamp + (86400 * 1000)
        deposit_history = Exchange.fetchDeposits(
            code="USDT",
            since=transaction_timestamp
            params={
                "status": 1,
                "endTime": end_timestamp,
            },
        )
        deposit_history = {i["txid"]: float(i['amount']) for i in deposit_history if (i.get("txid") and i.get('amount'))}
        return deposit_history
    except Exception as e:
        logger.error(str(e))
        logger.exception("")
        raise BackendException("get deposit history error")


def validate_transaction(exchange, wallet: str, txid: str, transaction_date: str):
    deposit_history = get_deposit_history(transaction_date)
    if txid in deposit_history:
        amount = deposit_history[txid]
        if amount <= 0:
            raise BackendException("amount less than zero")
        return amount
    else:
        raise BackendException("transaction not found")


Exchange = init_exchange('binance')
