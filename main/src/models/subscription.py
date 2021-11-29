from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Subscription(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="subscription_user")
    plan = fields.ForeignKeyField("darius.Plan", related_name="subscription_plan")
    expire_date = fields.DatetimeField(null=True)
    comfirm = fields.BooleanField(null=False, default=False)

    class Meta:
        table = "subscription"
        table_description = "Subscription"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Subscription [{self.id}]"


SubscriptionSchemaModel = pydantic_model_creator(Subscription, name="Subscription")
SubscriptionInSchemaModel = pydantic_model_creator(Subscription, name="SubscriptionIn", exclude_readonly=True)
