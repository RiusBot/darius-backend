from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Telegram(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="telegram_user")
    telegram_id = fields.IntField(pk=False, null=False, unique=True)

    class Meta:
        table = "telegram"
        table_description = "Telegram"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del", "id"]

    def __str__(self):
        return f"User [{self.id}] {self.telegram_id}"


TelegramSchemaModel = pydantic_model_creator(Telegram, name="Telegram")
TelegramInSchemaModel = pydantic_model_creator(Telegram, name="TelegramIn", exclude_readonly=True)
