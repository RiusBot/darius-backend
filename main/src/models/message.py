from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel
from .channel import ChannelType


class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Message(BaseModel):

    channel = fields.CharEnumField(ChannelType, max_length=32, null=False)
    content = fields.CharField(1024, null=False)
    symbol = fields.CharField(16, null=True)
    action = fields.CharEnumField(ActionType, "action", 16, null=True)
    message_timestamp = fields.DatetimeField(null=False)
    recieve_timestamp = fields.DatetimeField(null=False)
    entry = fields.FloatField(null=True)
    stop_loss = fields.FloatField(null=True)
    take_profit = fields.FloatField(null=True)

    class Meta:
        table = "message"
        table_description = "telegram messages"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id", "is_del"]

    def __str__(self):
        return f"""Message [{self.id}]
channel: {self.channel}
content: {self.content}
===============================================
symbol: {self.symbol}
action: {self.action}
entry: {self.entry}
stop loss: {self.stop_loss}
take profit: {self.take_profit}
"""


MessageSchemaModel = pydantic_model_creator(Message, name="Message")
MessageInSchemaModel = pydantic_model_creator(Message, name="MessageIn", exclude_readonly=True)
