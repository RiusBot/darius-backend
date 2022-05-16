import ccxt
import json
import logging
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from typing import List
from main.src.models import Pair, User
from main.src.exception import BackendException
from main.src.core.cipher import encrypt, decrypt
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_user_pair")
async def _get_user_pair(user: User) -> List[Pair]:
    uid = user.uid
    logger.info(f"Get pair for user {uid}")

    Pair_Pydantic_List = pydantic_queryset_creator(
        Pair,
        include=["name", "types", "id", "lists"]
    )
    pair_list = await Pair_Pydantic_List.from_queryset(user.pair_user.filter(is_del=False))
    pair_list = json.loads(pair_list.json())
    for pair in pair_list:
        pair["pair_id"] = pair.pop("id")
        pair["lists"] = json.loads(pair["lists"])
    logger.info(f"Get user [{uid}] {len(pair_list)} pair")
    return pair_list


async def validate_pair_number(user: User, lists: List[str]):
    # inf for admin, 3 apir for each user, 1 for trial

    pair_number_limit = 1
    has_subscription = await user.subscription_user.filter(is_del=False).exists()
    if has_subscription:
        pair_number_limit = 3

    # validate pair number
    pair_list = await user.pair_user.filter(is_del=False)
    valid_pair_list = [pair for pair in pair_list if not pair.is_del]
    if valid_pair_list and len(valid_pair_list) >= pair_number_limit and user.role.name != "admin":
        raise BackendException(f"Maximum {pair_number_limit} pair")


async def validate_pair(lists: List[str]):
    lists = [i.upper() for i in lists if isinstance(i, str)]
    return lists


@atomic()
@permission_validator("create_user_pair")
async def _create_user_pair(user: User, name :str, types: str, lists: List[str]) -> int:
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
async def _update_user_pair(user: User, pair_id, name :str, types: str, lists: List[str]) -> int:
    uid = user.uid
    logger.info(f"Update pair [{pair_id}] for user [{uid}]")

    # validate pair belongs to user
    pair = await user.pair_user.filter(is_del=False, id=pair_id).first()
    if pair is None:
        raise BackendException("Invalid pair.")

    # validate name duplicate
    duplicate = await user.pair_user.filter(is_del=False, name=name).exists()
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
            raise BackendException("API still in use.")

    # delete pair
    pair.is_del = True
    await pair.save()
