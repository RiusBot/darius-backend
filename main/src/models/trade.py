from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class TradeStatusType(str, Enum):
    OPEN = "open"
    CLOSE = "closed"
    CANCEL = "canceled"
    EXPIRE = "expired"
    ERROR = "error"


class Trade(BaseModel):

    # user = fields.ForeignKeyField("darius.User", related_name="trade_user")
    bot = fields.ForeignKeyField("darius.BotOrder", related_name="trade_bot")
    message = fields.ForeignKeyField("darius.Message", related_name="trade_message")
    status = fields.CharEnumField(TradeStatusType, "trade", 16, null=False)
    error = fields.CharField(1024, null=True)
    open_order = fields.CharField(50, null=True)
    tp_order = fields.CharField(50, null=True)
    sl_order = fields.CharField(50, null=True)

    class Meta:
        table = "trade_history"
        table_description = "trade history"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Trade: [{self.id}]"


TradeSchemaModel = pydantic_model_creator(Trade, name="Trade")
TradeInSchemaModel = pydantic_model_creator(Trade, name="TradeIn", exclude_readonly=True)
