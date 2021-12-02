from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Role(BaseModel):

    permission = fields.ForeignKeyField("darius.Permission", related_name="role_permission", through="role_permission")
    name = fields.CharField(50, null=False)

    class Meta:
        table = "role"
        table_description = "Role"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "is_del"]

    def __str__(self):
        return f"Role [{self.id}]"


RoleSchemaModel = pydantic_model_creator(Role, name="Role")
RoleInSchemaModel = pydantic_model_creator(Role, name="RoleIn", exclude_readonly=True)
