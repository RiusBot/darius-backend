from enum import Enum
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class RoleType(str, Enum):
    ADMIN = "admin"
    TEST = "test"
    USER = "user"
    VIP = "vip"
    GUEST = 'guest'


class Role(BaseModel):

    name = fields.CharEnumField(RoleType, max_length=50, null=False)

    class Meta:
        table = "role"
        table_description = "Role"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "is_del"]

    def __str__(self):
        return f"Role [{self.id}]"


RoleSchemaModel = pydantic_model_creator(Role, name="Role")
RoleInSchemaModel = pydantic_model_creator(Role, name="RoleIn", exclude_readonly=True)
