import os
import logging
import aiohttp
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Union
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator

from main.src.config import app_config
from main.src.models import Trade, User, BotOrder
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.bot import process_bot_config
from main.src.core.notify import notify
from main.src.utils import fetch, pagination


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


@atomic()
@permission_validator("get_bot_trades")
async def _get_bot_trades(user: User, bot_id: int) -> List[Trade]:
    uid = user.uid
    logger.info(f"Get trades from bot {bot_id} for user {uid}")
    Trade_Pydantic_List = pydantic_queryset_creator(
        Trade,
        exclude=["bot"]
    )

    bot = await user.bot_user.filter(id=bot_id).first()
    if bot is None:
        raise BackendException("Invalid bot_id")

    trade_list = await Trade_Pydantic_List.from_queryset(
        bot.trade_bot.filter(
            message__is_del=False,
            is_del=False
        ).limit(20)
    )
    trade_list = trade_list.dict()['__root__']
    for trade in trade_list:
        trade["message"]["message_timestamp"] = trade["message"]["message_timestamp"].timestamp()
        trade["message"]["recieve_timestamp"] = trade["message"]["recieve_timestamp"].timestamp()

    logger.info(f"Get bot [{bot_id}] {len(trade_list)} trades")
    return trade_list


@atomic()
@permission_validator("get_bot_trades")
async def _get_bot_trades2(user: User, bot_id: int, page: int, pagesize: int) -> List[Trade]:
    uid = user.uid
    logger.info(f"Get trades from bot {bot_id} for user {uid}")
    Trade_Pydantic_List = pydantic_queryset_creator(
        Trade,
        exclude=["bot"]
    )

    bot = await user.bot_user.filter(id=bot_id).first()
    if bot is None:
        raise BackendException("Invalid bot_id")

    query = bot.trade_bot.filter(message__is_del=False, is_del=False)
    pagination_query, total_count, total_page = await pagination(query, page, pagesize)

    trade_list = await Trade_Pydantic_List.from_queryset(pagination_query)
    trade_list = trade_list.dict()['__root__']
    for trade in trade_list:
        trade["message"]["message_timestamp"] = trade["message"]["message_timestamp"].timestamp()
        trade["message"]["recieve_timestamp"] = trade["message"]["recieve_timestamp"].timestamp()

    logger.info(f"Get bot [{bot_id}] {len(trade_list)} trades")
    return {
        'trades': trade_list,
        'page': page,
        'pagesize': pagesize,
        'total_page': total_page,
        'total_count': total_count
    }


@atomic()
async def _clean_limit_order():
    logger.info("Clean limit order")
    one_hour_ago = datetime.now() - timedelta(minutes=70)
    config_list = []
    user_list = []
    trade_dict = {}
    async for trade in Trade.filter(
        created_at__gt=one_hour_ago,
        status="success",
        bot__config__order_type="LIMIT",
        bot__config__api__is_del=False,
    ).prefetch_related(
        "bot__config__api",
        "bot__config__pair",
        "bot__user",
        "message"
    ):
        if trade.open_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["open_order"] = trade.open_order
            config_dict["trade_id"] = trade.id
            config_dict["symbol"] = trade.message.symbol
            config_list.append(config_dict)
            trade_dict[trade.id] = trade
            user_list.append(trade.bot.user)

    result_list = await send_bot_executor_clean(config_list, {'type': 'limit'})

    query = []
    stats = defaultdict(int)
    for user, config, result in zip(user_list, config_list, result_list):
        trade_id = config["trade_id"]
        if isinstance(result, dict):
            status = result.get("status")
            stats[status] += 1
            if status:
                trade = trade_dict[trade_id]
                trade.status = status
                notify_info = {
                    'status': status,
                    'symbol': trade.message.symbol,
                    'bot': str(trade.bot),
                    'action': trade.message.action,
                }
                query.append(notify(user, "LIMIT", notify_info))
                query.append(trade.save())
        else:
            stats['error'] += 1

    await asyncio.gather(*query)
    logger.info(f"clean limit order stats: {stats}")


@atomic()
async def _clean_oco_order():
    logger.info("Clean oco order")

    start_date = datetime.now() - timedelta(days=7)
    config_list = []
    user_list = []
    trade_dict = {}
    async for trade in Trade.filter(
        created_at__gt=start_date,
        bot__is_del=False,
        bot__config__api__is_del=False,
        status="success",
    ).order_by(
        "created_at"
    ).prefetch_related(
        "bot__config__api",
        "bot__config__pair",
        "bot__user",
        "message"
    ):
        if trade.sl_order or trade.tp_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["symbol"] = trade.message.symbol
            config_dict["sl_order"] = trade.sl_order
            config_dict["tp_order"] = trade.tp_order
            config_dict["trade_id"] = trade.id
            config_list.append(config_dict)
            user_list.append(trade.bot.user)
            trade_dict[trade.id] = trade

    result_list = await send_bot_executor_clean(config_list, {'type': 'oco'})

    query = []
    stats = defaultdict(int)
    for user, config, result in zip(user_list, config_list, result_list):
        trade_id = config["trade_id"]
        if isinstance(result, dict):
            status = result.get("status")
            stats[status] += 1
            if status:
                trade = trade_dict[trade_id]
                trade.status = status
                notify_info = {
                    'status': status,
                    'symbol': trade.message.symbol,
                    'bot': str(trade.bot)
                }
                query.append(notify(user, "OCO", notify_info))
                query.append(trade.save())
        else:
            stats['error'] += 1
            stats[result] += 1

    await asyncio.gather(*query)
    logger.info(f"clean oco order stats: {stats}")


@atomic()
@permission_validator("clean_all_position")
async def _clean_all_position(user: User, bot_id: int):
    logger.info(f"Clean all position for bot {bot_id}")

    bot = await BotOrder.filter(
        is_del=False,
        id=bot_id
    ).prefetch_related(
        "config__api",
        "config__pair",
        "user",
    ).first()

    config_list = [process_bot_config(bot.config)]
    result_list = await send_bot_executor_clean(config_list, {'type': 'position'})

    for config, result in zip(config_list, result_list):
        if isinstance(result, dict):
            return result.get("status")
        else:
            logger.error(f"close position error {result}")
            return 'CLOSE POSITION ERROR'


async def send_bot_executor_clean(config_list: List[dict], data_dict: dict = {}, workers: int = 40) -> List[Union[Dict, str]]:
    logger.info("Start activate bot executor clean")
    url = app_config["BOT_EXECUTOR_CLEAN_ENDPOINT"]

    async with aiohttp.ClientSession(timeout=600) as session:

        sem = asyncio.Semaphore(workers)
        tasks = []
        for config in config_list:
            config.update(data_dict)
            task = asyncio.create_task(fetch(session, sem, url, config))
            tasks.append(task)
        logger.info(f"All {len(config_list)} scheduled.")

        responses = await asyncio.gather(*tasks)
        return responses
