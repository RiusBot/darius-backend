import os
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict
import concurrent.futures
from concurrent.futures import Future
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator

from main.src.config import app_config
from main.src.models import Trade, User
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.bot import process_bot_config, send_to_execute


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

    trade_list = await Trade_Pydantic_List.from_queryset(bot.trade_bot.filter(is_del=False).offset(0).limit(20))
    trade_list = trade_list.dict()['__root__']
    for trade in trade_list:
        trade["message"]["message_timestamp"] = trade["message"]["message_timestamp"].timestamp()
        trade["message"]["recieve_timestamp"] = trade["message"]["recieve_timestamp"].timestamp()

    # trade_list = json.loads(trade_list.json())
    logger.info(f"Get bot [{bot_id}] {len(trade_list)} trades")
    return trade_list


@atomic()
async def _clean_limit_order() -> int:
    logger.info("Clean limit order")
    one_hour_ago = datetime.now() - timedelta(minutes=70)
    config_list = []
    trade_dict = {}
    async for trade in Trade.filter(
        created_at__gt=one_hour_ago,
        status="success",
        bot__config__order_type="LIMIT"
    ).prefetch_related("bot__config__api", "message"):
        if trade.open_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["open_order"] = trade.open_order
            config_dict["trade_id"] = trade.id
            config_dict["symbol"] = trade.message.symbol
            config_list.append(config_dict)
            trade_dict[trade.id] = trade

    result_dict = await send_bot_executor_clean(config_list, {'type': 'limit'})

    stats = defaultdict(int)
    for trade_id, result in result_dict.items():
        if isinstance(result, dict):
            status = result.get("status", "no_status")
            stats[status] += 1
        else:
            stats['error'] += 1

    logger.info(f"clean limit order stats: {json.dumps(stats)}")


@atomic()
async def _clean_oco_order() -> int:
    logger.info("Clean oco order")

    start_date = datetime.now() - timedelta(days=7)
    config_list = []
    trade_dict = {}
    async for trade in Trade.filter(
        created_at__gt=start_date,
        status="success",
    ).prefetch_related(
        "bot__config__api",
        "bot__config__pair",
        "message"
    ):
        if trade.sl_order or trade.tp_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["symbol"] = trade.message.symbol
            config_dict["sl_order"] = trade.sl_order
            config_dict["tp_order"] = trade.tp_order
            config_dict["trade_id"] = trade.id
            config_list.append(config_dict)
            trade_dict[trade.id] = trade

    result_dict = await send_bot_executor_clean(config_list, {'type': 'oco'})

    stats = defaultdict(int)
    for trade_id, result in result_dict.items():
        if isinstance(result, dict):
            status = result.get("status")
            stats[status] += 1
            if status:
                trade = trade_dict[trade_id]
                trade.status = status
                await trade.save()
        else:
            stats['error'] += 1

    logger.info(f"clean oco order stats: {json.dumps(stats)}")


async def send_bot_executor_clean(config_list: List[dict], data_dict: dict = {}, workers: int = 1) -> Dict[Future, int]:
    logger.info("Start activate bot executor")
    url = app_config["BOT_EXECUTOR_CLEAN_ENDPOINT"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        task_dict = dict()
        for config in config_list:
            config.update(data_dict)
            task = executor.submit(send_to_execute, url, config)
            task_dict[task] = config["trade_id"]
            # time.sleep(0.5)
        logger.info(f"All {len(config_list)} submitted.")

    result_dict = dict()
    for task in concurrent.futures.as_completed(task_dict, timeout=60):
        trade_id = task_dict[task]
        result = task.result()
        result_dict[trade_id] = result
    logger.info(f"Recieve {len(result_dict)} results")
    return result_dict
