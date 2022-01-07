from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Exchange(str, Enum):
    BINANCE = "binance"
    FTX = "ftx"
    FTXUS = "ftxus"


class Api(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="api_user")
    api_key = fields.CharField(64, null=False)
    api_secret = fields.CharField(400, null=False)
    exchange = fields.CharEnumField(Exchange, max_length=16, null=False)
    subaccount = fields.CharField(32, null=True)

    class Meta:
        table = "api"
        table_description = "Api"
        unique_together = ("api_key", "api_secret")
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del", "user", "api_secret", "user_id"]

    def __str__(self):
        return f"Api [{self.id}] {self.api_key} {self.api_secret} {self.subaccount}"


ApiSchemaModel = pydantic_model_creator(Api, name="Api")
ApiInSchemaModel = pydantic_model_creator(Api, name="ApiIn", exclude_readonly=True)
