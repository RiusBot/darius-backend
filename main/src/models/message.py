from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Message(BaseModel):

    channel = fields.CharField(32, null=False)
    content = fields.CharField(1024, null=False)
    symbol = fields.CharField(16, null=True)
    action = fields.CharEnumField(Action, "action", 16, null=True)

    class Meta:
        table = "message"
        table_description = "telegram messages"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Message [{self.id}]\nchannel: {self.channel}\n{self.content}\n\nsymbol: {self.symbol}\naction: {self.action}"


MessageSchemaModel = pydantic_model_creator(Message, name="Message")
MessageInSchemaModel = pydantic_model_creator(Message, name="MessageIn", exclude_readonly=True)
