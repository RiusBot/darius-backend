from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class PairType(str, Enum):
    WHITE = "WHITE"
    BLACK = "BLACK"
    BUILTIN = "BUILTIN"


class Pair(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="pair_user")
    name = fields.CharField(64, null=False)
    types = fields.CharEnumField(PairType, max_length=16, null=False)
    lists = fields.TextField(null=False)

    class Meta:
        table = "pair"
        table_description = "Pair"
        unique_together = ("user_id", "name")
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del", "user", "user_id"]

    def __str__(self):
        return f"Pair [{self.id}] {self.name}"


PairSchemaModel = pydantic_model_creator(Pair, name="Pair")
PairInSchemaModel = pydantic_model_creator(Pair, name="PairIn", exclude_readonly=True)
