import ccxt
import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Api, User


@atomic()
async def _get_user_api(user_id: int) -> List[Api]:
    logging.info(f"Get api for user {user_id}")
    Api_Pydantic_List = pydantic_queryset_creator(
        Api,
        include=["api_key", "api_secret", "exchange", "id"]
    )
    user = await User.filter(id=user_id).first()
    api_list = await Api_Pydantic_List.from_queryset(user.api_user.filter(is_del=False).all())
    api_list = json.loads(api_list.json())
    for api in api_list:
        api["api_id"] = api.pop("id")
    logging.info(f"Get user [{user_id}] {len(api_list)} api")
    return api_list


def validate_api(api_key: str, api_secret: str, exchange: str):
    exchange = getattr(ccxt, exchange)({
        'enableRateLimit': True,
        'apiKey': api_key,
        "secret": api_secret,
    })
    if not exchange.checkRequiredCredentials():
        raise Exception("Invalid exchange credentials.")
    try:
        exchange.fetch_balance()
    except Exception:
        raise Exception("Invalid API Permission.")


@atomic()
async def _create_user_api(user_id: int, api_key: str, api_secret: str, exchange: str) -> int:
    logging.info(f"Create new api for user [{user_id}]")

    user = await User.filter(id=user_id).filter(is_del=False).first()
    if user is None:
        raise Exception("Invalid user_id")

    # validate api number
    api_list = await user.api_user.filter(is_del=False).all()
    if api_list and len(api_list) > 3:
        raise Exception("Maximum 3 api per user")

    # validate api
    validate_api(api_key, api_secret, exchange)

    # create api
    api = Api.create(
        user=user,
        api_key=api_key,
        api_secret=api_secret,
        exhcange=exchange
    )
    api_id = api.id

    logging.info(f"Create api [{api_id}]")
    return api_id


@atomic()
async def _delete_user_api(user_id: int, api_id: int) -> int:
    logging.info(f"Delete api [{api_id}] for user {user_id}")

    user = await User.filter(id=user_id).filter(is_del=False).first()
    if user is None:
        raise Exception("Invalid user_id")

    # validate api
    api = await user.api_user.filter(id=api_id).filter(is_del=False).first()
    if api is None:
        raise Exception("Invalid api_id")

    # delete api
    api.is_del = True
    await api.save()
