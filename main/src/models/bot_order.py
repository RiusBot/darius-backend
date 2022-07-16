from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel
from .channel import ChannelType


class BotStatusType(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPEND = "SUSPEND"
    STOPPED = "STOPPED"


class BotOrder(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="bot_user")
    config = fields.OneToOneField("darius.BotConfig", related_name="bot_config")
    channel = fields.CharEnumField(ChannelType, max_length=32, null=False)
    status = fields.CharEnumField(BotStatusType, max_length=16, null=False, default=BotStatusType.PENDING)
    is_trial = fields.BooleanField(null=False, default=False)
    trial_expired_at = fields.DatetimeField(null=True)

    class Meta:
        table = "bot_order"
        table_description = "bot orders"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"BOT [{self.channel} {self.id}]"


BotOrderSchemaModel = pydantic_model_creator(BotOrder, name="BotOrder")
BotOrderInSchemaModel = pydantic_model_creator(BotOrder, name="BotOrderIn", exclude_readonly=True)
