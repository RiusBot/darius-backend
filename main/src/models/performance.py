from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel
from .channel import ChannelType


class Performance(BaseModel):

    channel = fields.CharEnumField(ChannelType, max_length=32, null=False, pk=False)
    result = fields.TextField(null=False)
    start_at = fields.DatetimeField(null=False)
    end_at = fields.DatetimeField(null=False)
    hyperopt = fields.ForeignKeyField("darius.Hyperopt", related_name="performance_hyperopt")

    class Meta:
        table = "performance"
        table_description = "channel performance"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Performance [{self.id}]"


PerformanceSchemaModel = pydantic_model_creator(Performance, name="Performance")
PerformanceInSchemaModel = pydantic_model_creator(Performance, name="PerformanceIn", exclude_readonly=True)
