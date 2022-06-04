import ccxt
import json
import logging
from cachetools import cached, TTLCache
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Pair, User
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@cached(cache=TTLCache(maxsize=256, ttl=86400))
def load_all_token():
    binance_spot = ccxt.binance({
        "enableRateLimit": True,
        'options': {
            "defaultType": 'spot',
            "adjustForTimeDifference": True,
        }
    })
    binance_future = ccxt.binance({
        "enableRateLimit": True,
        'options': {
            "defaultType": 'future',
            "adjustForTimeDifference": True,
        }
    })
    ftx = ccxt.ftx({
        "enableRateLimit": True,
        'options': {
            "adjustForTimeDifference": True,
        }
    })

    binance_markets = set()
    binance_markets.update(binance_spot.loadMarkets().keys())
    binance_markets.update(binance_future.loadMarkets().keys())
    ftx_markets = ftx.loadMarkets().keys()

    all_token = set()
    for symbol in binance_markets:
        try:
            token, base = symbol.split('/')
        except Exception:
            continue
        if base != "USDT":
            continue
        elif token[-4:] == "DOWN" or token[-2:] == "UP" or token[-4:] == "BULL" or token[-4:] == "BEAR":
            continue
        all_token.add(token)

    for symbol in ftx_markets:
        try:
            if '-MOVE' in symbol:
                continue
            elif '/' in symbol:
                token, base = symbol.split('/')
            elif '-' in symbol:
                token, base = symbol.split('-')
            else:
                continue
        except Exception:
            continue

        if base != "USD":
            continue
        elif "BEAR" in token or "BULL" in token or "HEDGE" in token or 'HALF' in token:
            continue
        all_token.add(token)

    logger.info(f'Get all binance/ftx market pair {len(all_token)}')
    return list(all_token), all_token


@permission_validator("get_all_pair")
async def _get_all_pair(user: User) -> List[Pair]:
    logger.info(f"Get all pair for user {user.uid}")
    return load_all_token()[0]


async def validate_pair_number(user: User, lists: List[str]):

    # basic & trial
    role = 'trial'

    if user.role.name == "vip":
        role = 'vip'
    elif user.role.name == "admin":
        role = 'admin'
    else:
        # subscriber
        has_subscription = await user.subscription_user.filter(is_del=False).exists()
        if has_subscription:
            role = 'subscriber'

    pair_number_limit = {
        'trial user': 1,
        'vip': 3,
        'admin': 100,
        'subscriber': 3
    }.get(role, 0)

    # validate pair number
    pair_list = await user.pair_user.filter(is_del=False)
    valid_pair_list = [pair for pair in pair_list if not pair.is_del]
    if valid_pair_list and len(valid_pair_list) >= pair_number_limit:
        raise BackendException(f"Maximum {pair_number_limit} pair for {role}")


async def validate_pair(lists: List[str]):
    all_market_token_set = load_all_token()[1]
    valid_lists = []

    for i in lists:
        if isinstance(i, str):
            i = i.upper()
            if i in all_market_token_set:
                valid_lists.append(i)

    ignore_token = list(set(lists) - set(valid_lists))
    logger.info(f"Ignore following token: {ignore_token}")
    return valid_lists


@atomic()
@permission_validator("get_user_pair")
async def _get_user_pair(user: User) -> List[Pair]:
    uid = user.uid
    logger.info(f"Get pair for user {uid}")

    Pair_Pydantic_List = pydantic_queryset_creator(
        Pair,
        include=["name", "types", "id", "lists"]
    )
    pair_list = await Pair_Pydantic_List.from_queryset(user.pair_user.filter(is_del=False, types__not="BUILTIN"))
    pair_list = json.loads(pair_list.json())
    for pair in pair_list:
        pair["pair_id"] = pair.pop("id")
        pair["lists"] = json.loads(pair["lists"])
    logger.info(f"Get user [{uid}] {len(pair_list)} pair")
    return pair_list


@atomic()
@permission_validator("create_user_pair")
async def _create_user_pair(user: User, name: str, types: str, lists: List[str]) -> int:
    uid = user.uid
    logger.info(f"Create new pair for user [{uid}]")

    await validate_pair_number(user, lists)
    lists = await validate_pair(lists)

    # validate name duplicate
    duplicate = await user.pair_user.filter(is_del=False, name=name).exists()
    if duplicate:
        raise BackendException("Name duplicate.")

    # create pair
    pair = await Pair.create(
        user=user,
        name=name,
        types=types,
        lists=json.dumps(lists),
    )
    pair_id = pair.id

    logger.info(f"Create pair [{pair_id}]")
    return pair_id


@atomic()
@permission_validator("update_user_pair")
async def _update_user_pair(user: User, pair_id: int, name: str, types: str, lists: List[str]) -> int:
    uid = user.uid
    logger.info(f"Update pair [{pair_id}] for user [{uid}]")

    # validate pair belongs to user
    pair = await user.pair_user.filter(is_del=False, id=pair_id).first()
    if pair is None:
        raise BackendException("Invalid pair.")

    # validate name duplicate
    duplicate = await user.pair_user.filter(is_del=False, name=name, id__not=pair_id).exists()
    if duplicate:
        raise BackendException("Name duplicate.")

    # validate pair
    lists = await validate_pair(lists)

    # update pair
    pair.name = name
    pair.types = types
    pair.lists = json.dumps(lists)
    await pair.save()


@atomic()
@permission_validator("delete_user_pair")
async def _delete_user_pair(user: User, pair_id: int) -> int:
    uid = user.uid
    logger.info(f"Delete pair [{pair_id}] for user {uid}")

    # validate pair belongs to user
    pair = await user.pair_user.filter(id=pair_id, is_del=False).first()
    if pair is None:
        raise BackendException("Invalid pair_id")

    # validate no bot using
    async for config_using_this_pair in pair.config_pair.filter(is_del=False).prefetch_related("bot"):
        if config_using_this_pair.bot.is_del:

            # check if config is somehow not deleted
            if config_using_this_pair.is_del:
                config_using_this_pair.is_del = True
                await config_using_this_pair.save()
        else:
            raise BackendException("Pair still in use by Bot.")

    # delete pair
    # pair.is_del = True
    # await pair.save()
    await pair.delete()


@atomic()
@permission_validator("get_builtin_pair")
async def _get_builtin_pair(user: User) -> List[Pair]:
    uid = user.uid
    logger.info(f"Get builtin pair for user {uid}")

    Pair_Pydantic_List = pydantic_queryset_creator(
        Pair,
        include=["name", "types", "id", "lists"]
    )
    pair_list = await Pair_Pydantic_List.from_queryset(Pair.filter(is_del=False, types="BUILTIN"))
    pair_list = json.loads(pair_list.json())
    for pair in pair_list:
        pair["pair_id"] = pair.pop("id")
        pair["lists"] = json.loads(pair["lists"])
    logger.info(f"Get builtin {len(pair_list)} pair")
    return pair_list


@atomic()
@permission_validator("create_builtin_pair")
async def _create_builtin_pair(user: User, name: str, types: str, lists: List[str]) -> int:
    logger.info("Create new builtin pair")
    lists = await validate_pair(lists)

    # validate name duplicate
    duplicate = await Pair.filter(is_del=False, name=name, types=types).exists()
    if duplicate:
        raise BackendException("Name duplicate.")

    # create pair
    pair = await Pair.create(
        user=user,
        name=name,
        types=types,
        lists=json.dumps(lists),
    )
    logger.info(f"Create builtin pair [{pair.id}]")
    return pair.id


@atomic()
@permission_validator("update_builtin_pair")
async def _update_builtin_pair(user: User, pair_id: int, name: str, types: str, lists: List[str]) -> int:
    logger.info(f"Update builtin pair [{pair_id}]")

    # validate pair is builtin
    pair = await Pair.filter(is_del=False, id=pair_id, types=types).first()
    if pair is None:
        raise BackendException("Invalid pair.")

    # validate name duplicate
    duplicate = await Pair.filter(is_del=False, name=name, id__not=pair_id, types=types).exists()
    if duplicate:
        raise BackendException("Name duplicate.")

    # validate pair
    lists = await validate_pair(lists)

    # update pair
    pair.name = name
    pair.lists = json.dumps(lists)
    await pair.save()


@atomic()
@permission_validator("delete_builtin_pair")
async def _delete_builtin_pair(user: User, pair_id: int) -> int:
    logger.info(f"Delete builtin pair [{pair_id}]")

    # validate pair is builtin
    pair = await Pair.filter(is_del=False, id=pair_id, types='BUILTIN').first()
    if pair is None:
        raise BackendException("Invalid pair.")

    # validate no bot using
    async for config_using_this_pair in pair.config_pair.filter(is_del=False).prefetch_related("bot"):
        if config_using_this_pair.bot.is_del:
            # check if config is somehow not deleted
            if config_using_this_pair.is_del:
                config_using_this_pair.is_del = True
                await config_using_this_pair.save()
        else:
            raise BackendException("Pair still in use by Bot.")

    # delete pair
    # pair.is_del = True
    # await pair.save()
    await pair.delete()
