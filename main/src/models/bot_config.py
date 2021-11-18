from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class TargetType(str, Enum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURE = "FUTURE"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class BotConfig(BaseModel):

    bot = fields.OneToOneField("darius.BotOrder", related_name="config_bot")
    test = fields.BooleanField(null=False, default=False)
    duplicate = fields.BooleanField(null=True, default=False)
    target = fields.CharEnumField(TargetType, null=False, max_length=16)
    quantity = fields.FloatField(null=False)
    leverage = fields.FloatField(null=False, default=1.0)
    margin = fields.FloatField(null=True)
    minimum_volume = fields.FloatField(null=True)
    stop_loss = fields.FloatField(null=True)
    take_profit = fields.FloatField(null=True)
    order_type = fields.CharEnumField(OrderType, null=False, default="MARKET")
    stop_loss_type = fields.CharEnumField(OrderType, null=False, default="MARKET")
    take_profit_type = fields.CharEnumField(OrderType, null=False, default="MARKET")

    class Meta:
        table = "bot_config"
        table_description = "bot config"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Bot Config [{self.id}]"


BotConfigSchemaModel = pydantic_model_creator(BotConfig, name="BotConfig")
BotConfigInSchemaModel = pydantic_model_creator(BotConfig, name="BotConfigIn", exclude_readonly=True)
