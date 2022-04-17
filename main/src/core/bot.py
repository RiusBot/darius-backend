import os
import time
import enum
import json
import asyncio
import logging
import requests
import traceback
import concurrent.futures
from concurrent.futures import Future
from datetime import datetime, timedelta
from tortoise.transactions import atomic
from tortoise.queryset import QuerySet
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.fields.relational import ReverseRelation
from typing import List, Dict, Tuple
from main.src.models import BotOrder, BotConfig, Trade, Message, User, Hyperopt
from main.src.models.channel import ChannelType
from main.src.config import app_config
from main.src.exception import BackendException
from main.src.core.auth import fetch_secret_token_firestore
from main.src.core.cipher import decrypt
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


def _execute_bot_signal(loop, *args, **kwargs):
    loop.create_task(execute(*args, **kwargs))
    logger.info("execute bot signal complete.")


async def _execute_webhook_signal(*args, **kwargs):
    result = await execute_webhook(*args, **kwargs)
    logger.info("execute webhook signal complete.")
    return result


@atomic()
async def get_all_bot(channel: str) -> Dict[int, BotOrder]:
    logger.info("Get all bot")
    try:
        bot_dict = {}
        async for bot in BotOrder.filter(is_del=False, status="RUNNING", channel=channel).prefetch_related(
            "config__api",
            "user",
        ).order_by("config__order_type"):
            bot_dict[bot.id] = bot

        logger.info(f"{len(bot_dict)} bots")
        return bot_dict
    except Exception as e:
        logger.error(f"get all bot error. {e}")
        logger.exception("")


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


async def get_all_bot_config(channel: str, bot_dict: Dict[int, BotOrder]) -> List[dict]:
    logger.info("Get all bot config")

    hyperopt = await get_hyperopt(channel)

    config_list = []
    for bot in bot_dict.values():
        config_dict = process_bot_config(bot.config)
        config_dict = fill_hyperopt(hyperopt, config_dict)
        config_list.append(config_dict)

    
    logger.info(f"{len(config_list)} bot configs")
    return config_list


def send_to_execute(config: dict):
    try:
        url = app_config["BOT_EXECUTOR_ENDPOINT"]
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
                if not (isinstance(response, str) and ("Rate exceeded" in response or "DDoSProtection" in response)):
                    break
            return response
    except Exception as e:
        logger.exception("")
        # return str(e)
        # logger.error(str(e))
        return "EXECUTE ERROR"


async def send_bot_executor(config_list: List[dict], data_dict: dict, workers: int = 1) -> Dict[Future, int]:
    logger.info("Start activate bot executor")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        task_dict = dict()
        for config in config_list:
            config.update(data_dict)
            task = executor.submit(send_to_execute, config)
            task_dict[task] = config["bot_id"]
            # await asyncio.sleep(1)
            time.sleep(1)
        logger.info(f"All {len(config_list)} submitted.")
    return task_dict


async def recieve_execute_result(task_dict: Dict[Future, int]) -> Tuple[list, list]:
    logger.info("Receive execute result")
    result_dict = dict()
    for task in concurrent.futures.as_completed(task_dict, timeout=60):
        bot_id = task_dict[task]
        result = task.result()
        result_dict[bot_id] = result
    logger.info(f"Recieve {len(result_dict)} results")
    return result_dict


@atomic()
async def write_trade_result(message: Message, result_dict: dict, bot_dict: Dict[int, BotOrder]):
    logger.info("Write trade results")

    trade_list = []
    for bot_id, result in result_dict.items():
        bot = bot_dict[bot_id]
        logger.info(json.dumps(result, indent=4))

        if isinstance(result, str):  # error
            trade = Trade(
                user=bot.user,
                bot=bot,
                message=message,
                status="error",
                error=result,
            )
        else:
            trade = Trade(
                user=bot.user,
                bot=bot,
                message=message,
                status=result.get("status", "unknown"),
                open_order=result.get("open_order"),
                sl_order=result.get("sl_order"),
                tp_order=result.get("tp_order"),
            )

        trade_list.append(trade)

    logger.info(f"write {len(trade_list)} trade results")
    await Trade.bulk_create(
        trade_list
    )


@atomic()
async def write_message(
    channel: str,
    content: str,
    symbol: str,
    action: str,
    message_timestamp: datetime,
    recieve_timestamp: datetime,
    entry: float,
    stop_loss: float,
    take_profit: float
):
    logger.info("Write message")
    logger.info(json.dumps({
        "channel": channel,
        "content": content,
        "symbol": symbol,
        "action": action,
        "message_timestamp": message_timestamp.isoformat(),
        "recieve_timestamp": recieve_timestamp.isoformat(),
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }, indent=4))
    try:
        message = await Message.create(
            channel=channel,
            content=content,
            symbol=symbol,
            action=action,
            message_timestamp=message_timestamp,
            recieve_timestamp=recieve_timestamp,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return message
    except Exception as e:
        logger.error(f"write message error. {e}")
        logger.exception("")


async def execute(
    thread_id: int,
    BotStatus: dict,
    channel: str,
    content: str,
    symbol: str,
    action: str,
    message_timestamp: float,
    recieve_timestamp: float,
    entry: float = None,
    stop_loss: float = None,
    take_profit: float = None,
    price: float = None,
):
    try:
        status_logger = ThreadStatusLogger(thread_id, BotStatus)
        status_logger.log("Starting execute bot signal")
        bot_dict, message = None, None

        try:
            status_logger.log("Get all bot and write message.")
            bot_dict, message = await asyncio.gather(
                get_all_bot(channel),
                write_message(
                    channel,
                    content,
                    symbol,
                    action,
                    datetime.fromtimestamp(message_timestamp),
                    datetime.fromtimestamp(recieve_timestamp),
                    entry,
                    stop_loss,
                    take_profit
                )
            )
        except Exception as e:
            error_msg = f"get all bot and write message error. {e}"
            status_logger.log(
                json.dumps(
                    {
                        "error": error_msg,
                        "traceback": traceback.format_exc()
                    },
                    indent=4
                )
            )

        if bot_dict is not None and message is not None and action is not None:
            try:
                status_logger.log("Prepare data")
                config_list = await get_all_bot_config(channel, bot_dict)
                data_dict = {
                    "symbol": symbol,
                    "action": action,
                    "scalp_entry": entry,
                    "scalp_stop_loss": stop_loss,
                    "scalp_take_profit": take_profit,
                    "price": price,
                }
                status_logger.log_data(data_dict)
                task_dict = await send_bot_executor(config_list, data_dict)
                result_dict = await recieve_execute_result(task_dict)
            except Exception as e:
                error_msg = f"send and receive data error. {e}"
                status_logger.log(
                    json.dumps(
                        {
                            "error": error_msg,
                            "traceback": traceback.format_exc()
                        },
                        indent=4
                    )
                )
                result_dict = {bot_id: 'EXECUTE ERROR' for bot_id in bot_dict}

            try:
                status_logger.log("write trade result.")
                await write_trade_result(message, result_dict, bot_dict)
            except Exception as e:
                error_msg = f"write trade result error. {e}"
                status_logger.log(
                    json.dumps(
                        {
                            "error": error_msg,
                            "traceback": traceback.format_exc()
                        },
                        indent=4
                    )
                )

    except Exception as e:
        error_msg = f"Unexpected error. {e}"
        status_logger.log(
            json.dumps(
                {
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                },
                indent=4
            )
        )
    finally:
        status_logger.log("Complete")
        BotStatus.pop(thread_id)


async def execute_webhook(
    channel: str,
    content: str,
    symbol: str,
    action: str,
    uid: str,
    bot_id: int,
    message_timestamp: float,
    recieve_timestamp: float,
    entry: float = None,
    stop_loss: float = None,
    take_profit: float = None,
    price: float = None,
):
    try:
        bot_dict, message = None, None

        try:
            logger.info("Get webhook bot and write message.")
            bot = await BotOrder.filter(
                is_del=False,
                status="RUNNING",
                channel=channel,
                user__uid=uid,
            ).prefetch_related(
                "config__api",
                "user",
            ).first()
            
            if bot is None:
                logger.info(f"No such webhook Bot {channel} {uid}")
                return
            
            bot_dict = {bot.id: bot}
            if bot_id != bot.id:
                raise BackendException("Bot ID not match")

            message = await write_message(
                channel,
                content,
                symbol,
                action,
                datetime.fromtimestamp(message_timestamp),
                datetime.fromtimestamp(recieve_timestamp),
                entry,
                stop_loss,
                take_profit
            )
        except Exception as e:
            error_msg = f"get webhook bot and write message error. {e}"
            logger.error(
                json.dumps(
                    {
                        "error": error_msg,
                        "traceback": traceback.format_exc()
                    },
                    indent=4
                )
            )

        if bot_dict is not None and message is not None and action is not None:
            try:
                logger.info("Prepare data")
                config_list = await get_all_bot_config(channel, bot_dict)
                data_dict = {
                    "symbol": symbol,
                    "action": action,
                    "scalp_entry": entry,
                    "scalp_stop_loss": stop_loss,
                    "scalp_take_profit": take_profit,
                    "price": price,
                }
                logger.info(json.dumps(data_dict, indent=4))
                task_dict = await send_bot_executor(config_list, data_dict)
                result_dict = await recieve_execute_result(task_dict)
            except Exception as e:
                error_msg = f"send and receive data error. {e}"
                logger.error(
                    json.dumps(
                        {
                            "error": error_msg,
                            "traceback": traceback.format_exc()
                        },
                        indent=4
                    )
                )
                result_dict = {bot_id: 'EXECUTE ERROR' for bot_id in bot_dict}

            try:
                logger.info("write trade result.")
                await write_trade_result(message, result_dict, bot_dict)
            except Exception as e:
                error_msg = f"write trade result error. {e}"
                logger.error(
                    json.dumps(
                        {
                            "error": error_msg,
                            "traceback": traceback.format_exc()
                        },
                        indent=4
                    )
                )

    except Exception as e:
        error_msg = f"Unexpected error. {e}"
        logger.error(
            json.dumps(
                {
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                },
                indent=4
            )
        )
    finally:
        logger.info("Complete")


@atomic()
@permission_validator("get_user_bots")
async def _get_user_bots(user: User) -> List[BotOrder]:
    uid = user.uid
    logger.info(f"Get bots for user {uid}")
    Bot_Pydantic_List = pydantic_queryset_creator(
        BotOrder,
        include=["id", "config", "status", "channel", "config_id", "is_trial", "trial_expired_at"]
    )
    bot_list = await Bot_Pydantic_List.from_queryset(user.bot_user.filter(is_del=False))
    bot_list = json.loads(bot_list.json())
    for bot in bot_list:
        bot["bot_id"] = bot.pop("id")
        bot["config"]["api_id"] = bot["config"]["api"]["id"]
        bot["config"].pop("api")

    logger.info(f"Get user [{uid}] {len(bot_list)} bots")
    return bot_list


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

    trade_list = await Trade_Pydantic_List.from_queryset(bot.trade_bot.filter(message__is_del=False, is_del=False).offset(0).limit(20))
    trade_list = trade_list.dict()['__root__']
    for trade in trade_list:
        trade["message"]["message_timestamp"] = trade["message"]["message_timestamp"].timestamp()
        trade["message"]["recieve_timestamp"] = trade["message"]["recieve_timestamp"].timestamp()

    # trade_list = json.loads(trade_list.json())
    logger.info(f"Get bot [{bot_id}] {len(trade_list)} trades")
    return trade_list


@atomic()
async def get_hyperopt(channel: str) -> dict:
    hyperopt = await Hyperopt.filter(
        is_del=False,
        channel=channel,
        loss="SharpeHyperOptLoss"
    ).first()
    if hyperopt is None:
        hyperopt = await Hyperopt.filter(is_del=False, channel="DEFAULT").first()

    return json.loads(hyperopt.params)


def fill_hyperopt(hyperopt: dict, config: dict):
    if config.get('hyperopt'):
        config["take_profit"] = float(hyperopt["take_profit"])
        config["stop_loss"] = float(hyperopt["stop_loss"])
    return config


@atomic()
@permission_validator("create_user_bot")
async def _create_user_bot(user: User, channel: str, config: dict) -> int:
    uid = user.uid
    is_trial = False
    trial_expired_at = None
    logger.info(f"Create new bot for user [{uid}]")

    # validate api belongs to user
    api_id = config["api_id"]
    api = await user.api_user.filter(id=api_id).filter(is_del=False).first()
    if api is None:
        raise BackendException("Invalid api_id")

    # check channel from code base
    if channel not in ChannelType._value2member_map_:
        raise BackendException("Invalid channel")

    # validate channel subscription
    subscription = await user.subscription_user.filter(
        is_del=False, plan__channel__in=[channel, "DARIUS"]
    ).exists()
    if not subscription:

        # check if trial
        telegram = await user.telegram_user.filter(is_del=False).first()
        trial_expired_at = telegram.created_at + timedelta(days=30)
        if telegram and trial_expired_at.timestamp() < datetime.now().timestamp():
            # not trial period
            raise BackendException("No subscription")
        else:
            # no subscription, but trial period
            config["quantity"] = 30
            config["leverage"] = 1
            is_trial = True

            # validate bot number (1 per channel)
            bot_list = await user.bot_user.filter(is_del=False, channel=channel)
            if bot_list and len(bot_list) >= 1 and user.role.name != "admin":
                raise BackendException("Maximum 1 bot per subscription when trial")

    else:
        # validate bot number (2 per channel)
        bot_list = await user.bot_user.filter(is_del=False, channel=channel)
        if bot_list and len(bot_list) >= 2 and user.role.name != "admin":
            raise BackendException("Maximum 2 bot per subscription")

    # validate trailing order
    validate_trailing(api, config)

    # create bot
    config["api"] = api
    if channel == ChannelType.WEBHOOK:

        bot_config = await BotConfig.create(
            **config
        )

        bot_order, create = await BotOrder.get_or_create(
            defaults={
                "config": bot_config,
                "status": "RUNNING",
                "is_trial": is_trial,
                "trial_expired_at": trial_expired_at
            },
            channel=channel,
            is_del=False,
            user=user,
        )
        if create:
            bot_config.bot = bot_order
            await bot_config.save()
        else:
            raise BackendException("Webhook bot exists !! One per account.")
    else:
        bot_config = await BotConfig.create(
            **config
        )

        bot_order = await BotOrder.create(
            channel=channel,
            user=user,
            config=bot_config,
            status="RUNNING"
        )

        bot_config.bot = bot_order
        await bot_config.save()

    bot_id = bot_order.id
    logger.info(f"Create bot [{bot_id}]")
    return bot_id


@atomic()
@permission_validator("update_user_bot")
async def _update_user_bot(user: User, bot_id: int, config: dict, status: str) -> int:
    uid = user.uid
    logger.info(f"Update bot [{bot_id}]")

    # validate api belongs to user
    api_id = config["api_id"]
    api = await user.api_user.filter(id=api_id).filter(is_del=False).first()
    if api is None:
        raise BackendException("Invalid api_id")

    # validate trailing
    validate_trailing(api, config)

    # update bot
    config["api"] = api
    bot_order = await BotOrder.filter(is_del=False, id=bot_id).prefetch_related("config").first()
    if bot_order is None:
        raise BackendException(f"No Bot {bot_id}")
    if status:
        bot_order.status = status
    for key, value in config.items():
        setattr(bot_order.config, key, value)
    await bot_order.save()
    await bot_order.config.save()


def validate_trailing(api, config):

    params = {}

    if (config["stop_loss_type"] == "TRAILING" or config["take_profit_type"] == "TRAILING"):

        if api.exchange == "binance":

            if config["target"] != "FUTURE":
                raise BackendException("Binance can only use trailing stop in future trading.")

        if config["stop_loss_type"] == "TRAILING":

            if float(config["stop_loss"]) < 0.001 or float(config["stop_loss"]) > 0.05:
                raise BackendException(" 0.1 < stop_loss < 5 %")

        if config["take_profit_type"] == "TRAILING":

            if float(config["take_profit"]) < 0.001 or float(config["take_profit"]) > 0.05:
                raise BackendException(" 0.1 < take_profit < 5 %")

    if config['stop_loss_type'] != "TRAILING":
        if config['stop_loss'] < 0 or config['stop_loss'] > 1:
            raise BackendException(" 0 < stop loss < 100 %")

    if config['take_profit_type'] != "TRAILING":
        if config['take_profit'] < 0 or config['take_profit'] > 5:
            raise BackendException(" 0 < take profit < 500 %")

    return params


@atomic()
@permission_validator("delete_user_bot")
async def _delete_user_bot(user: User, bot_id: int) -> int:
    uid = user.uid
    logger.info(f"Delete bot[{bot_id}] for user {uid}")

    user = await User.filter(uid=uid).filter(is_del=False).first()
    if user is None:
        raise BackendException("Invalid uid")

    # validate bot
    bot = await user.bot_user.filter(id=bot_id).filter(is_del=False).prefetch_related("config").first()
    if bot is None:
        raise BackendException("Invalid bot_id")

    # delete bot
    bot.is_del = True
    bot.config.is_del = True
    await bot.config.save()
    await bot.save()


class ThreadStatusLogger():
    def __init__(self, thread_id: int, BotStatus: dict):
        self.id = thread_id
        self.status_dict = BotStatus[thread_id]
        self.status_dict["log"] = []
        self.status_dict["data"] = {}

    def log(self, msg: str, level: str = "info"):
        log_func = getattr(logger, level)
        log_func(msg)
        self.status_dict["log"].append(msg)

    def log_data(self, data: dict):
        self.status_dict["data"] = data
