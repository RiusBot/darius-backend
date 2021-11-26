from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class ChannelType(str, Enum):
    ROSE = "ROSE"
    PERPETUAL = "PERPETUAL"
    WHALE = "WHALE"
    DAILYSCALP = "DAILYSCALP"
    TEST2 = "test2"
    TEST = "test"


class Plan(BaseModel):

    name = fields.CharField(50, null=False, unique=True)
    channel = fields.CharEnumField(ChannelType, max_length=32, null=False)
    price = fields.FloatField()
    day = fields.IntField()

    class Meta:
        table = "plan"
        table_description = "Plan"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id", "is_del"]

    def __str__(self):
        return f"Plan [{self.id}]"


PlanSchemaModel = pydantic_model_creator(Plan, name="Plan")
PlanInSchemaModel = pydantic_model_creator(Plan, name="PlanIn", exclude_readonly=True)
