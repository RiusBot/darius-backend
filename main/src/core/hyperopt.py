import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from tortoise.transactions import atomic
from main.src.models import User
from main.src.core.permission import permission_validator
from main.src.config import app_config
from main.src.core.auth import fetch_secret_token_firestore
from main.src.utils import fetch


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_hyperopt")
async def _get_hyperopt(user: User, channel: str) -> dict:
    logger.info(f"Get {channel} hyperopt")
    return {
        'take_profit': 0.1,
        'stop_loss': 0.1,
    }


async def _create_hyperopt() -> dict:
    logger.info("Create hyperopt")
    date = datetime.now()
    start = (date - timedelta(days=180)).strftime("%Y%m%d")
    end = date.strftime("%Y%m%d")

    url = f'{app_config["BOT_OPTIMIZER_URL"]}/hyperopt'
    data = {
        'timeframe': '1h',
        'days': 90,
        'timerange': f'{start}-{end}',
        'token': fetch_secret_token_firestore()
    }

    async with aiohttp.ClientSession(timeout=3600) as session:
        sem = asyncio.Semaphore(1)
        response = await fetch(session, sem, url, data, error="CREATE HYPEROPT ERROR", timeout=1800)

        if isinstance(response, str):
            logger.error(f"create hyperopt failed. {response}")
        else:
            logger.info("create hyperopt success.")
