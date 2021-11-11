from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models.base import BaseModel


class User(BaseModel):

    username = fields.CharField(100, null=True)

    class Meta:
        table = "user"
        table_description = "User"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "modified_at", "id"]

    def __str__(self):
        return f"User [{self.id}]"


UserSchemaModel = pydantic_model_creator(User, name="User")
UserInSchemaModel = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
