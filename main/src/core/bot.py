from datetime import datetime, timedelta
from main.src.models import BotConfig


async def execute_bot_signal(channel: str, content: str, symbol: str, action: str, message_timestamp: float, recieve_timestamp: float):
    # read bot_config with match channel
    bot_config = await BotConfig.filter(channel="Updated name").all()

    # sequential send to bot executor


    # write message to database


    # recieve results


    # write trade results to database
