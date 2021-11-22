from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class BotStatusType(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPEND = "SUSPEND"
    STOPPED = "STOPPED"


class BotOrder(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="bot_user")
    config = fields.OneToOneField("darius.BotConfig", related_name="bot_config")
    channel = fields.CharField(32, null=False)
    status = fields.CharEnumField(BotStatusType, max_length=16, null=False, default=BotStatusType.PENDING)

    class Meta:
        table = "bot_order"
        table_description = "bot orders"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Bot [{self.id}] {self.channel} {self.status}"


BotOrderSchemaModel = pydantic_model_creator(BotOrder, name="BotOrder")
BotOrderInSchemaModel = pydantic_model_creator(BotOrder, name="BotOrderIn", exclude_readonly=True)
