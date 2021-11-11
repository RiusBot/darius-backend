from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel


class Trade(BaseModel):

    user_id = fields.ForeignKeyField("models.User", related_name="user")
    bot_id = fields.ForeignKeyField("models.BotOrder", related_name="Bot")
    message_id = fields.ForeignKeyField("models.Message", related_name="message")
    status = fields.CharField(16, null=False)
    error = fields.CharField(1024, null=True)

    class Meta:
        table = "trade_history"
        table_description = "trade history"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Trade: [{self.id}]"


TradeSchemaModel = pydantic_model_creator(Trade, name="Trade")
TradeInSchemaModel = pydantic_model_creator(Trade, name="TradeIn", exclude_readonly=True)
