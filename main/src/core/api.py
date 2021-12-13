import ccxt
import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Api, User
from main.src.exception import BackendException


logger = logging.getLogger(__name__)


@atomic()
async def _get_user_api(uid: str) -> List[Api]:
    logger.info(f"Get api for user {uid}")
    user = await User.filter(uid=uid).first()
    if user is None:
        raise BackendException("Invalid uid")

    Api_Pydantic_List = pydantic_queryset_creator(
        Api,
        include=["api_key", "exchange", "id"]
    )
    api_list = await Api_Pydantic_List.from_queryset(user.api_user.filter(is_del=False).all())
    api_list = json.loads(api_list.json())
    for api in api_list:
        api["api_id"] = api.pop("id")
    logger.info(f"Get user [{uid}] {len(api_list)} api")
    return api_list


def validate_api_permission(api_key: str, api_secret: str, exchange: str, subaccount: str):

    headers = {}
    if subaccount:
        if exchange == "ftx":
            headers = {
                'FTX-SUBACCOUNT': subaccount
            }
        else:
            raise BackendException(f"{exchange} does not support subaccount")

    exchange = getattr(ccxt, exchange)({
        'enableRateLimit': True,
        'apiKey': api_key,
        "secret": api_secret,
        "headers": headers
    })
    if not exchange.checkRequiredCredentials():
        raise BackendException("Invalid exchange credentials.")
    try:
        exchange.fetch_balance()
    except Exception:
        raise BackendException("Invalid API Permission.")


@atomic()
async def _create_user_api(uid: str, api_key: str, api_secret: str, exchange: str, subaccount: str) -> int:
    logger.info(f"Create new api for user [{uid}]")

    # validate user
    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate api number
    api_list = await user.api_user.all()
    valid_api_list = [api for api in api_list if not api.is_del]
    if valid_api_list and len(valid_api_list) > 3:
        raise BackendException("Maximum 3 api per user")

    # validate api permission
    validate_api_permission(api_key, api_secret, exchange, subaccount)

    # validate api duplicate
    for api in api_list:
        if (api.api_key, api.api_secret) == (api_key, api_secret):
            if api.is_del is False:
                raise BackendException("Duplicate api")
            else:
                api.is_del = False
                await api.save()
                logger.info(f"Restore api [{api.id}]")
                return api.id

    # create api
    api = await Api.create(
        user=user,
        api_key=api_key,
        api_secret=api_secret,
        exchange=exchange,
        subaccount=subaccount
    )
    api_id = api.id

    logger.info(f"Create api [{api_id}]")
    return api_id


@atomic()
async def _update_user_api(uid: str, api_id: int, api_key: str, api_secret: str, exchange: str, subaccount: str) -> int:
    logger.info(f"Update api [{api_id}] for user [{uid}]")

    # validate user
    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate api belongs to user
    api = await user.api_user.filter(is_del=False).filter(id=api_id).first()
    if api is None:
        raise BackendException("Invalid api.")

    # validate api permission
    validate_api_permission(api_key, api_secret, exchange, subaccount)

    # update api
    api.api_key = api_key
    api.api_secret = api_secret
    api.exchange = exchange
    api.subaccount = subaccount
    await api.save()


@atomic()
async def _delete_user_api(uid: str, api_id: int) -> int:
    logger.info(f"Delete api [{api_id}] for user {uid}")

    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate api belongs to user
    api = await user.api_user.filter(id=api_id).filter(is_del=False).first()
    if api is None:
        raise BackendException("Invalid api_id")

    # validate no bot using
    bot_using_this_api = await Api.config_api.filter(id=api_id).filter(is_del=False).first()
    if bot_using_this_api is not None:
        raise BackendException("API still in use.")

    # delete api
    api.is_del = True
    await api.save()
