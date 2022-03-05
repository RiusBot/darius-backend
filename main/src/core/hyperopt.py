import json
import logging
import requests
from datetime import datetime, timedelta
from tortoise.transactions import atomic
from tortoise.contrib.pydantic import pydantic_queryset_creator
from main.src.models import Hyperopt, User
from main.src.models.hyperopt import HyperoptSchemaModel
from main.src.exception import BackendException
from main.src.core.permission import permission_validator
from main.src.config import app_config
from main.src.core.auth import fetch_secret_token_firestore


logger = logging.getLogger(__name__)


@atomic()
@permission_validator("get_hyperopt")
async def _get_hyperopt(user: User, channel: str) -> dict:
    logger.info(f"Get {channel} hyperopt")
    return {
        'take_profit': 0.1,
        'stop_loss': 0.1,
    }


def _create_hyperopt() -> dict:
    logger.info(f"Create hyperopt")
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
        logging.error(f"create hyperopt failed. {msg}")
    else:
        logging.info(f"create hyperopt success.")
