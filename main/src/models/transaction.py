from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Transaction(BaseModel):

    user = fields.ForeignKeyField("darius.User", related_name="transaction_user")
    wallet = fields.CharField(96, null=False)
    txid = fields.CharField(96, null=False, unique=True)
    amount = fields.FloatField(null=False)
    date = fields.DatetimeField(null=False)

    class Meta:
        table = "transaction"
        table_description = "Transaction"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"Transaction [{self.id}]"


TransactionSchemaModel = pydantic_model_creator(Transaction, name="Transaction")
TransactionInSchemaModel = pydantic_model_creator(Transaction, name="TransactionIn", exclude_readonly=True)
