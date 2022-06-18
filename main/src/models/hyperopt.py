from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel
from .channel import ChannelType


class LossType(str, Enum):
    OnlyProfitHyperOptLoss = 'OnlyProfitHyperOptLoss',
    SharpeHyperOptLoss = 'SharpeHyperOptLoss',
    MaxDrawDownHyperOptLoss = 'MaxDrawDownHyperOptLoss'
    DEFAULT = 'default'


class Hyperopt(BaseModel):

    channel = fields.CharEnumField(ChannelType, max_length=32, null=False)
    params = fields.TextField(null=False)
    start_at = fields.DatetimeField(null=False)
    end_at = fields.DatetimeField(null=False)
    days = fields.IntField()
    loss = fields.CharEnumField(LossType, max_length=32, null=False)

    class Meta:
        table = "hyperopt"
        table_description = "channel hyperopt"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"Hyperopt [{self.id}]"


HyperoptSchemaModel = pydantic_model_creator(Hyperopt, name="Hyperopt")
HyperoptInSchemaModel = pydantic_model_creator(Hyperopt, name="HyperoptIn", exclude_readonly=True)
