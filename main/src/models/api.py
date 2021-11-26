from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Exchange(str, Enum):
    BINANCE = "binance"
    FTX = "ftx"


class Api(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="api_user")
    api_key = fields.CharField(50, null=False, unique=True)
    api_secret = fields.CharField(50, null=False, unique=True)
    exchange = fields.CharEnumField(Exchange, max_length=16, null=False)

    class Meta:
        table = "api"
        table_description = "Api"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Api [{self.id}] {self.api_key} {self.api_secret}"


ApiSchemaModel = pydantic_model_creator(Api, name="Api")
ApiInSchemaModel = pydantic_model_creator(Api, name="ApiIn", exclude_readonly=True)
