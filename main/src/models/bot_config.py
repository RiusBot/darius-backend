from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel


class BotConfig(BaseModel):

    bot_id = fields.ForeignKeyField("models.BotOrder", related_name="bot")
    test = fields.BooleanField(null=False, default=False)
    duplicate_position = fields.BooleanField(null=True, default=False)
    target = fields.CharEnumField(null=False)
    quantity = fields.FloatField(null=False)
    leverage = fields.FloatField(null=False, default=1.0)
    margin = fields.FloatField(null=True)
    minimum_volume = fields.FloatField(null=True)
    stop_loss = fields.FloatField(null=True)
    take_profit = fields.FloatField(null=True)
    order_type = fields.CharEnumField(null=False, default="MARKET")
    stop_loss_type = fields.CharEnumField(null=False, default="MARKET")
    take_profit_type = fields.CharEnumField(null=False, default="MARKET")

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
