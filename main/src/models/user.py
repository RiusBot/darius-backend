from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class User(BaseModel):

    user_name = fields.CharField(16, null=True)
    email = fields.CharField(32, null=True, unique=True)
    role = fields.ForeignKeyField("darius.Role", related_name="user_role")
    uid = fields.CharField(28, null=False)
    balance = fields.FloatField(null=False, default=0.0)
    referrer = fields.CharField(8, null=True)
    referral_code = fields.CharField(8, null=False, unique=True)
    referrer_count = fields.IntField(null=False, default=0)
    referral = fields.OneToOneField("darius.Referral", related_name="user_referral", null=True, unqiue=True)

    class Meta:
        table = "user"
        table_description = "User"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del", "id"]

    def __str__(self):
        return f"User [{self.id}] {self.user_name} {self.email}"


UserSchemaModel = pydantic_model_creator(User, name="User")
UserInSchemaModel = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
