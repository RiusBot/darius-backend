from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Permission(BaseModel):

    role = fields.ForeignKeyField("darius.Role", related_name="permission_role")
    service = fields.CharField(50, null=False)

    class Meta:
        table = "permission"
        table_description = "Permission"
        ordering = ["role_id", "-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "id", "is_del"]

    def __str__(self):
        return f"Permission [{self.id}]"


PermissionSchemaModel = pydantic_model_creator(Permission, name="Permission")
PermissionInSchemaModel = pydantic_model_creator(Permission, name="PermissionIn", exclude_readonly=True)
