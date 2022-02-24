import json
import logging
from datetime import datetime
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from main.src.models import Performance, User
from main.src.models.performance import PerformanceSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_performance")
async def _get_performance(user: User, channel: str) -> dict:
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
        performance["result"] = json.dumps({
            'wins': buy_result["wins"] + sell_result['losses'],
            'losses': buy_result["losses"] + sell_result['wins'],
            'draws': buy_result["draws"] + sell_result['draws'],
            'profit_total': buy_result["profit_total"] - sell_result['profit_total'],
            'total_trades': buy_result["total_trades"] + sell_result['total_trades'],
        })

    return performance_list


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