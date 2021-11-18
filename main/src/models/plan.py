from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Plan(BaseModel):

    price = fields.FloatField()
    day = fields.IntField()

    class Meta:
        table = "plan"
        table_description = "Plan"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id"]

    def __str__(self):
        return f"Plan [{self.id}]"


PlanSchemaModel = pydantic_model_creator(Plan, name="Plan")
PlanInSchemaModel = pydantic_model_creator(Plan, name="PlanIn", exclude_readonly=True)
