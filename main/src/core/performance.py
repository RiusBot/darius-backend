import os
import json
import logging
import requests
import calendar
from datetime import datetime, timedelta
from aiocache import cached
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from main.src.models import Performance, User
from main.src.models.channel import ChannelType
from main.src.models.performance import PerformanceSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.config import app_config
from main.src.core.auth import fetch_secret_token_firestore


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


@atomic()
async def _get_performance(channel: str) -> dict:
    logger.info(f"Get {channel} Performance")
    Performance_Pydantic_List = pydantic_queryset_creator(
        Performance,
        include=["channel", "start_at", "result"]
    )
    performance_list = await Performance_Pydantic_List.from_queryset(
        Performance.filter(is_del=False, channel=channel).limit(12)
    )
    performance_list = json.loads(performance_list.json())
    for performance in performance_list:
        performance["date"] = performance.pop("start_at")[:7]
        buy_result = json.loads(performance["result"])["strategy"]["riusbot"]
        sell_result = json.loads(performance["result"])["strategy"]["riusbot_sell"]

        keys = ['wins', 'losses', 'draws', "profit_total", "total_trades"]
        performance["result"] = {
            'wins': buy_result["wins"] + sell_result['losses'],
            'losses': buy_result["losses"] + sell_result['wins'],
            'draws': buy_result["draws"] + sell_result['draws'],
            'profit_total': buy_result["profit_total"] - sell_result['profit_total'],
            'total_trades': buy_result["total_trades"] + sell_result['total_trades'],
        }

    return performance_list

@cached(ttl=43200)
@atomic()
async def _get_performances() -> dict:
    logger.info(f"Get all Performance")

    channel_list = await Performance.filter(is_del=False).distinct().values_list('channel', flat=True)
    # remove channel in db if not define in models.channel
    channel_list = [i for i in channel_list if i in ChannelType]

    Performance_Pydantic_List = pydantic_queryset_creator(
        Performance,
        include=["channel", "start_at", "result"]
    )
    performance_result = {}

    for channel in channel_list:
        performance_list = await Performance_Pydantic_List.from_queryset(
            Performance.filter(is_del=False, channel=channel).limit(12)
        )
        performance_list = json.loads(performance_list.json())
        for performance in performance_list:
            performance["date"] = performance.pop("start_at")[:7]
            buy_result = json.loads(performance["result"])["strategy"]["riusbot"]
            sell_result = json.loads(performance["result"])["strategy"]["riusbot_sell"]

            keys = ['wins', 'losses', 'draws', "profit_total", "total_trades"]
            performance["result"] = {
                'wins': buy_result["wins"] + sell_result['losses'],
                'losses': buy_result["losses"] + sell_result['wins'],
                'draws': buy_result["draws"] + sell_result['draws'],
                'profit_total': buy_result["profit_total"] - sell_result['profit_total'],
                'total_trades': buy_result["total_trades"] + sell_result['total_trades'],
            }
        performance_result[channel] = performance_list

    return performance_result


def _create_performance():
    logger.info(f"Create performance")
    date = datetime.now()
    y, m, d = date.year, date.month, date.day
    start = datetime(y, m, 1)
    _, last_day = calendar.monthrange(y, m)
    end = datetime(y, m, last_day)

    start = start.strftime("%Y%m%d")
    end = end.strftime("%Y%m%d")
    url = f'{app_config["BOT_OPTIMIZER_URL"]}/backtest'
    data = {
        'timeframe': '1h',
        'timerange': f'{start}-{end}',
        'token': fetch_secret_token_firestore()
    }

    response = requests.post(
        url,
        json=data
    )

    msg = ""
    try:
        msg += f"{response.json()}"
    except Exception:
        msg += f"{response.text}"
    if response.status_code != 200:
        logging.error(f"create performance failed. {msg}")
    else:
        logging.info(f"create performance success.")


@atomic()
@permission_validator("update_performance")
async def _update_performance(user: User, performance_id: int, name: str, channel: str, price: float, day: int) -> int:
    logger.info(f"Update performance [{performance_id}]")
    performance = await Performance.filter(is_del=False).filter(id=performance_id).first()
    if performance is None:
        raise BackendException("Invalid performance_id.")

    performance.name = name
    performance.channel = channel
    performance.price = price
    performance.day = day
    await performance.save()


@atomic()
@permission_validator("delete_performance")
async def _delete_performance(user: User, performance_id: int) -> int:
    logger.info(f"Delete performance {performance_id}")
    performance = await Performance.filter(id=performance_id).filter(is_del=False).first()
    if performance is None:
        raise BackendException("Invalid performance_id")
    performance.is_del = True
    await performance.save()
