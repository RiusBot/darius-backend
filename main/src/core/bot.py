import enum
import time
import asyncio
import logging
import requests
import traceback
import concurrent.futures
from concurrent.futures import Future
from datetime import datetime, timedelta
from tortoise.transactions import in_transaction, atomic
from tortoise.queryset import QuerySet
from tortoise.query_utils import Prefetch
from tortoise.models import Model
from typing import List, Dict, Tuple
from main.src.models import BotOrder, BotConfig, Trade, Message, Api
from main.src.config import app_config


def execute_bot_signal(loop, **kwargs):
    task = loop.create_task(_execute_bot_signal(**kwargs))
    logging.info("execute bot signal complete.")
    

@atomic()
async def get_all_bot(channel: str) -> Dict[int, BotOrder]:
    logging.info("Get all bot")

    bot_dict = {}
    async for bot in BotOrder.filter(is_del=False).filter(channel=channel).all().prefetch_related(
        "config__api",
        "user",
    ).order_by("config__order_type"):
        bot_dict[bot.id] = bot

    logging.info(f"{len(bot_dict)} bots")
    return bot_dict


def get_all_bot_config(bot_dict: Dict[int, BotOrder]) -> List[dict]:
    logging.info("Get all bot config")

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
            if isinstance(value, QuerySet):
                continue
            elif isinstance(value, Model):
                config_dict.update(parse(value))
            else:
                config_dict[key] = type_casting(value)
        return config_dict

    config_list = []
    for bot in bot_dict.values():
        config_dict = parse(bot.config)
        config_list.append(config_dict)

    logging.info(f"{len(config_list)} bot configs")
    return config_list


def _execute(config: dict):
    try:
        url = "http://localhost:8000/"  # app_config["BOT_EXECUTOR_ENDPOINT"]
        with requests.Session() as s:
            response = s.post(url, json=config, timeout=3600)
            try:
                response = response.json()
                if "error_message" in response:
                    response = response["error_message"]
            except:
                response = response.text
            return response
    except Exception as e:
        return traceback.format_exc()
        return str(e)


async def send_bot_executor(config_list: List[dict], data_dict: dict, workers=None) -> Dict[Future, int]:
    logging.info("Start activate bot executor")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        task_dict = dict()
        for config in config_list:
            config.update(data_dict)
            task = executor.submit(_execute, config)
            task_dict[task] = config["bot_id"]
            asyncio.sleep(0.2)
        logging.info(f"All {len(config_list)} submitted.")
    return task_dict


async def recieve_execute_result(task_dict: Dict[Future, int]) -> Tuple[list, list]:
    logging.info("Receive execute result")
    result_dict = dict()
    for task in concurrent.futures.as_completed(task_dict, timeout=600):
        bot_id = task_dict[task]
        result = task.result()
        result_dict[bot_id] = result
    logging.info(f"Recieve {len(result_dict)} results")
    return result_dict


@atomic()
async def write_trade_result(message: Message, result_dict: dict, bot_dict: Dict[int, BotOrder]):
    logging.info("Write trade results")

    trade_list = []
    for bot_id, result in result_dict.items():
        bot = bot_dict[bot_id]
        error = None if isinstance(result, dict) else result
        status = result["status"] if isinstance(result, dict) else "error"
        trade = Trade(
            user=bot.user,
            bot=bot,
            message=message,
            status=status,
            error=error,
        )
        trade_list.append(trade)

    logging.info(f"write {len(trade_list)} trade results")
    await Trade.bulk_create(
        trade_list
    )


@atomic()
async def write_message(channel: str, content: str, symbol: str, action: str, message_timestamp: float, recieve_timestamp: float):
    logging.info("Write message")
    try:
        message = await Message.create(
            channel=channel,
            content=content,
            symbol=symbol,
            action=action,
            message_timestamp=message_timestamp,
            recieve_timestamp=recieve_timestamp,
        )
        return message
    except Exception as e:
        logging.error("write message error")
        logging.exception("")


async def _execute_bot_signal(channel: str, content: str, symbol: str, action: str, message_timestamp: float, recieve_timestamp: float, price: float = 0):
    logging.info("Execute bot signal")
    try:
        
        bot_dict, message = await asyncio.gather(
            get_all_bot(channel),
            write_message(channel, content, symbol, action, message_timestamp, recieve_timestamp)
        )
        
        # read bot_config with match channel
        # bot_dict = await get_all_bot(channel)
        config_list = get_all_bot_config(bot_dict)

        # sequential send to bot executor
        data_dict = {
            "symbol": symbol,
            "action": action,
            "price": price
        }
        task_dict = await send_bot_executor(config_list, data_dict)
        result_dict = await recieve_execute_result(task_dict)
        
        await write_trade_result(message, result_dict, bot_dict)
        
    except Exception as e:
        logging.error("execute bot signal error")
        logging.exception("")
