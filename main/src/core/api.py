import ccxt
import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Api, User
from main.src.exception import BackendException
from main.src.core.cipher import encrypt, decrypt
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_api")
async def _get_user_api(user: User) -> List[Api]:
    uid = user.uid
    logger.info(f"Get api for user {uid}")

    Api_Pydantic_List = pydantic_queryset_creator(
        Api,
        include=["api_key", "exchange", "id", "subaccount"]
    )
    api_list = await Api_Pydantic_List.from_queryset(user.api_user.filter(is_del=False))
    api_list = json.loads(api_list.json())
    for api in api_list:
        api["api_id"] = api.pop("id")
    logger.info(f"Get user [{uid}] {len(api_list)} api")
    return api_list


def validate_api_permission(api_key: str, api_secret: str, exchange: str, subaccount: str):

    if exchange in ["ftx", "ftxus"]:
        if len(api_key) != 40 or len(api_secret) != 40:
            raise BackendException("Invalid length")
    elif exchange == "binance":
        if len(api_key) != 64 or len(api_secret) != 64:
            raise BackendException("Invalid length")

    headers = {}
    if subaccount:
        if exchange in ["ftx", "ftxus"]:
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
@permission_validator("create_user_api")
async def _create_user_api(user: User, api_key: str, api_secret: str, exchange: str, subaccount: str) -> int:
    uid = user.uid
    logger.info(f"Create new api for user [{uid}]")

    # validate api number
    api_list = await user.api_user.filter(is_del=False)
    valid_api_list = [api for api in api_list if not api.is_del]
    if valid_api_list and len(valid_api_list) >= 3:
        raise BackendException("Maximum 3 api per user")

    # validate api permission
    validate_api_permission(api_key, api_secret, exchange, subaccount)

    # encrypt api_secret
    api_secret = encrypt(api_key, api_secret)

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
@permission_validator("update_user_api")
async def _update_user_api(user: User, api_id: int, api_key: str, api_secret: str, exchange: str, subaccount: str) -> int:
    uid = user.uid
    logger.info(f"Update api [{api_id}] for user [{uid}]")

    # validate api belongs to user
    api = await user.api_user.filter(is_del=False, id=api_id).first()
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
@permission_validator("delete_user_api")
async def _delete_user_api(user: User, api_id: int) -> int:
    uid = user.uid
    logger.info(f"Delete api [{api_id}] for user {uid}")

    # validate api belongs to user
    api = await user.api_user.filter(id=api_id, is_del=False).first()
    if api is None:
        raise BackendException("Invalid api_id")

    # validate no bot using
    bot_using_this_api = await api.config_api.filter(is_del=False).first()
    if bot_using_this_api is not None:
        raise BackendException("API still in use.")

    # delete api
    api.is_del = True
    await api.save()


@atomic()
async def _clean_api() -> int:
    logger.info(f"Clean api")
    remove_bot_count = 0
    remove_api_count = 0

    async for api in Api.filter(is_del=False).all():
        try:
            api_secret = decrypt(api.api_key, api.api_secret)
            validate_api_permission(api.api_key, api_secret, api.exchange, api.subaccount)
        except Exception as e:

            # remove running bot
            async for config in api.config_api.filter(is_del=False).prefetch_related('bot'):
                config.is_del = True
                config.bot.is_del = True
                await config.save()
                await config.bot.save()
                remove_bot_count += 1

            # delete api
            api.is_del = True
            await api.save()
            remove_api_count += 1

    logger.info(f"Remove {remove_api_count} api, remove {remove_bot_count} bots.")
