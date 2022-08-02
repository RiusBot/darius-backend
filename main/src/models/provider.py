from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel


class Provider(BaseModel):

    name = fields.CharField(16, null=False, unique=True)
    access_token = fields.CharField(32, null=False, unique=True)

    class Meta:
        table = "provider"
        table_description = "provider"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"Provider [{self.id}]"


ProviderSchemaModel = pydantic_model_creator(Provider, name="Provider")
ProviderInSchemaModel = pydantic_model_creator(Provider, name="ProviderIn", exclude_readonly=True)


class RoiLog(BaseModel):

    provider = fields.ForeignKeyField("darius.Provider", related_name="provider_roilog", null=True)
    roi = fields.FloatField(null=False)
    timestamp = fields.DatetimeField(null=True, auto_now_add=True)

    class Meta:
        table = "roi_log"
        table_description = "provider roi log"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"RoiLog [{self.id}]"


RoiLogSchemaModel = pydantic_model_creator(RoiLog, name="RoiLog")
RoiLogInSchemaModel = pydantic_model_creator(RoiLog, name="RoiLogIn", exclude_readonly=True)
