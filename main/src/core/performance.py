import os
import json
import aiohttp
import asyncio
import logging
import calendar
from datetime import datetime
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
from main.src.utils import fetch


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


"""
收益率 profit_total
盈利金額 final_balance - starting_balance
總成交量 total_volume
手續費 total_volume * 0.002
勝率 win / (win+loss)
最大回撤 max_relative_drawdown
盈虧比
平均持倉時間 holding_avg
win
loss
交易次數 total_trades
盈利最高幣種  best_pair key
虧損最高幣種  worst_pair key
頻率 trades_per_day
====
cagr
sharperatio
annual_roi
delta market_change
"""


@atomic()
async def _get_performance(channel: str) -> dict:
    logger.info(f"Get {channel} all time Performance")

    backtest_report = {}
    all_time_performance = await Performance.filter(
        is_del=False,
        channel=channel,
        start_at=datetime(1970, 1, 1),
    ).order_by("end_at").first()
    if all_time_performance is not None:
        all_time_performance = await PerformanceSchemaModel.from_tortoise_orm(all_time_performance)
        all_time_performance = all_time_performance.dict()
        backtest_report = json.loads(all_time_performance['result'])['strategy']['riusbot_hedge']
        backtest_report = {
            'roi': backtest_report['profit_total'],
            'profit': backtest_report['final_balance'] - backtest_report['starting_balance'],
            'volume': backtest_report['total_volume'],
            'fee': backtest_report['total_volume'] * 0.001,
            'win_rate': backtest_report['wins'] / (backtest_report['wins'] + backtest_report['losses']),
            'max_drawdown': backtest_report['max_relative_drawdown'],
            'holding_avg': backtest_report['holding_avg'],
            'total_trades': backtest_report['total_trades'],
            'best_pair': backtest_report['best_pair']['key'],
            'worst_pair': backtest_report['worst_pair']['key'],
            'trades_per_day': backtest_report['trades_per_day'],
            'start': backtest_report['backtest_start'],
            'end': backtest_report['backtest_end'],
            'cagr': backtest_report['cagr'],
            'sharperatio': backtest_report['sharperatio'],
            'annual_roi': backtest_report['annual_roi'],
        }
    return {
        'channel': channel,
        'result': backtest_report,
    }


def process_backtest_report(performance: dict):
    performance["date"] = performance.pop("start_at")[:7]
    report = json.loads(performance["result"])

    if "riusbot_hedge" in report["strategy"]:
        result = json.loads(performance["result"])["strategy"]["riusbot_hedge"]

        # keys = ['wins', 'losses', 'draws', "profit_total", "total_trades"]
        performance["result"] = {
            'wins': result["wins"],
            'losses': result["losses"],
            'draws': result["draws"],
            'profit_total': result["profit_total"],
            'total_trades': result["total_trades"],
        }
    else:
        buy_result = json.loads(performance["result"])["strategy"]["riusbot"]
        sell_result = json.loads(performance["result"])["strategy"]["riusbot_sell"]

        # keys = ['wins', 'losses', 'draws', "profit_total", "total_trades"]
        performance["result"] = {
            'wins': buy_result["wins"] + sell_result['losses'],
            'losses': buy_result["losses"] + sell_result['wins'],
            'draws': buy_result["draws"] + sell_result['draws'],
            'profit_total': buy_result["profit_total"] - sell_result['profit_total'],
            'total_trades': buy_result["total_trades"] + sell_result['total_trades'],
        }

    return performance


@cached(ttl=43200)
@atomic()
async def _get_performances() -> dict:
    logger.info("Get all Performance")

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
            Performance.filter(
                is_del=False,
                channel=channel,
                start_at__gt=datetime(2021, 1, 1),
            ).order_by("-start_at").limit(12)
        )
        performance_list = json.loads(performance_list.json())
        for performance in performance_list:
            performance = process_backtest_report(performance)
        performance_result[channel] = performance_list

    return performance_result


async def _create_performance():
    logger.info("Create performance")
    date = datetime.now()
    y, m = date.year, date.month
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
    # all_time_data = {
    #     'timeframe': '1h',
    #     'timerange': f'{start}-{end}',
    #     'token': fetch_secret_token_firestore(),
    #     'all_time': True
    # }

    async with aiohttp.ClientSession(timeout=3600) as session:
        sem = asyncio.Semaphore(1)
        response = await fetch(session, sem, url, data, error="CREATE PERFORMANCE ERROR", timeout=3600)
        # response, all_time_response = await asyncio.gather(
        #     fetch(session, sem, url, data, error="CREATE PERFORMANCE ERROR", timeout=1800),
        #     fetch(session, sem, url, all_time_data, error="CREATE ALL TIME PERFORMANCE ERROR", timeout=1800),
        # )

        if isinstance(response, str):
            logging.error(f"create performance failed. {response}")
        else:
            logging.info("create performance success.")


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
