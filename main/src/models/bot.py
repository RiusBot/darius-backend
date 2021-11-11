from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class BotOrder(BaseModel):

    user_id = fields.ForeignKeyField("models.User", related_name="user")
    config_id = fields.ForeignKeyField("models.BotConfig", related_name="config")
    signal = fields.CharField(32, null=False)

    class Meta:
        table = "bot_order"
        table_description = "bot orders"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Bot [{self.id}]"


BotOrderSchemaModel = pydantic_model_creator(BotOrder, name="BotOrder")
BotOrderInSchemaModel = pydantic_model_creator(BotOrder, name="BotOrderIn", exclude_readonly=True)
