import os
import time
import enum
import ccxt
import json
import logging
import requests
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict
import concurrent.futures
from concurrent.futures import Future
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.fields.relational import ReverseRelation

from main.src.config import app_config
from main.src.models import Trade, User, BotConfig
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.core.cipher import decrypt
from main.src.core.auth import fetch_secret_token_firestore


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
    ).prefetch_related("bot__config__api"):
        if trade.open_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["open_order"] = trade.open_order
            config_dict["trade_id"] = trade.id
            config_list.append(config_dict)
            trade_dict[trade.id] = trade

    result_dict = await send_bot_executor(config_list, {'type': 'limit'})

    stats = defaultdict(int)
    for trade_id, result in result_dict.items():
        if isinstance(result, dict):
            status = result.get("status", "no_status")
            stats[status] += 1
        else:
            stats['error'] += 1

    logger.info(f"{json.dumps(stats, indent=4)}")


@atomic()
async def _clean_oco_order() -> int:
    logger.info("Clean oco order")

    start_date = datetime.now() - timedelta(days=7)
    config_list = []
    trade_dict = {}
    async for trade in Trade.filter(
        created_at__gt=start_date,
        status="success",
        bot__config__api__exchange="binance"
    ).prefetch_related("bot__config__api", "message"):
        if trade.sl_order or trade.tp_order:
            config_dict = process_bot_config(trade.bot.config)
            config_dict["symbol"] = trade.message.symbol
            config_dict["sl_order"] = trade.sl_order
            config_dict["tp_order"] = trade.tp_order
            config_dict["trade_id"] = trade.id
            config_list.append(config_dict)
            trade_dict[trade.id] = trade

    result_dict = await send_bot_executor(config_list, {'type': 'oco'})

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

    logger.info(f"{json.dumps(stats, indent=4)}")


def send_to_execute(config: dict):
    try:
        url = app_config["BOT_EXECUTOR_CLEAN_ENDPOINT"]
        if usingProjectId != "local":
            config["token"] = fetch_secret_token_firestore()

        try:
            config["api_secret"] = decrypt(config["api_key"], config["api_secret"])
        except Exception:
            logger.error(f'Decrypt error, use plain. api_id: {config["api_id"]}.')
            logger.exception("")

        max_retry = 3
        with requests.Session() as s:
            for i in range(max_retry):
                response = s.post(url, json=config, timeout=600)
                try:
                    response = response.json()
                    if "error_message" in response:
                        response = str(response["error_message"])
                    elif "error_messages" in response:
                        response = str(response["error_messages"])
                except Exception:
                    response = response.text
                if not (isinstance(response, str) and ("Rate exceeded" in response or "Too many requests" in response)):
                    break
            return response
    except Exception as e:
        logger.exception("")
        # return str(e)
        # logger.error(str(e))
        return "EXECUTE ERROR"


async def send_bot_executor(config_list: List[dict], data_dict: dict = {}, workers: int = 1) -> Dict[Future, int]:
    logger.info("Start activate bot executor")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        task_dict = dict()
        for config in config_list:
            config.update(data_dict)
            task = executor.submit(send_to_execute, config)
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


def process_bot_config(config: BotConfig):

    def type_casting(value):
        if isinstance(value, enum.Enum):
            return value.value
        elif isinstance(value, datetime):
            return value.timestamp()
        else:
            return value

    def parse(model: Model):
        config_dict = {}
        for key, value in model:
            if isinstance(value, (QuerySet, ReverseRelation)):
                continue
            elif isinstance(value, Model):
                config_dict.update(parse(value))
            else:
                config_dict[key] = type_casting(value)
        return config_dict

    return parse(config)
