from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Payment(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="payment_user")
    remain = fields.FloatField(null=False)

    class Meta:
        table = "payment"
        table_description = "Payment"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Payment [{self.id}]"


PaymentSchemaModel = pydantic_model_creator(Payment, name="Payment")
PaymentInSchemaModel = pydantic_model_creator(Payment, name="PaymentIn", exclude_readonly=True)
