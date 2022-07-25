from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from collections import defaultdict

from main.src.models import BaseModel


class ServiceType(str, Enum):
    OCO = "OCO"
    LIMIT = "LIMIT"
    OPEN = "OPEN"


class NotifyType(str, Enum):
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    SMS = "SMS"


def MessageTemplate(service: str, info: dict):

    if service == "OCO":
        return f"""{info.get('bot')} OCO order
        {info['symbol']} {info.get('action')} closed with status {info.get('status')}
        """
    elif service == "LIMIT":
        return f"{info.get('bot')} {info.get('symbol')} LIMIT order status {info.get('status')}"
    elif service == "OPEN":
        return f"{info.get('bot')} open {info.get('symbol')} {info.get('action')} order {info.get('status')}"


def ConfigTemplate():
    notify_config = defaultdict(dict)
    for i in NotifyType:
        for j in ServiceType:
            notify_config[i.value][j.value] = False
    return notify_config


class Notify(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="notify_user", null=False)
    service = fields.CharEnumField(ServiceType, max_length=32, null=False)
    notify = fields.CharEnumField(NotifyType, max_length=32, null=False)

    class Meta:
        table = "notify"
        table_description = "Notify"
        unique_together = ("user_id", "name")
        ordering = ["-created_at", "id"]
        unique_together = ("user", "service", "notify")

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del", "user", "user_id"]

    def __str__(self):
        return f"Notify [{self.id}] {self.name}"


NotifySchemaModel = pydantic_model_creator(Notify, name="Notify")
NotifyInSchemaModel = pydantic_model_creator(Notify, name="NotifyIn", exclude_readonly=True)
