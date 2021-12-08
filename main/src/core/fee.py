import logging
from datetime import datetime, timedelta
from main.src.core.exchange import exchange
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


def confirm_user_payment(uid: str, address: str, txid: str, referal: str, plan: str):

    plan_fee_mapping = {
        "1 month": {
            "fee": 50,
            "extend": timedelta(days=30)
        },
        "6 month": {
            "fee": 250,
            "extend": timedelta(days=180)
        },
        "year": {
            "fee": 400,
            "extend": timedelta(days=365)
        },
    }
    if plan not in plan_fee_mapping:
        raise BackendException("purchase plan malformed.")

    last_payment_timestamp = get_user_last_payment_timestamp(uid)
    deposit_history = exchange.fetchDeposits(
        code="USDT",
        since=last_payment_timestamp,
        params={
            'status': 1
        }
    )

    for deposit in deposit_history:
        if deposit.get("deposit") == address and deposit.get("txid") == txid:
            if deposit.get("type") == "deposit" and deposit.get("status") == "ok":
                fee = plan_fee_mapping[plan]["fee"]
                extend = plan_fee_mapping[plan]["extend"]
                if deposit.get("ammount") >= fee:
                    new_due_date = extend_user_due_date(uid, address, txid, extend, deposit)
                    return True, new_due_date

    return False, None


def update_user_payment_record(uid: str, deposit: dict):
    pass


def update_user_due_date(uid, new_due_date: datetime):
    pass


def extend_user_due_date(uid: str, address: str, txid: str, extend: timedelta, deposit: dict):
    old_due_date = get_user_due_date(uid)
    new_due_date = old_due_date + extend
    update_user_payment_record(uid, deposit)
    update_user_due_date(uid, new_due_date)
    return new_due_date


def get_user_last_payment_timestamp(uid: str):
    pass


def get_user_due_date(uid: str):
    pass
