from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):

    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    is_del = fields.BooleanField(null=False, default=False)

    class Meta:
        abstract = True
