from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from main.src.models import BaseModel


class Referral(BaseModel):

    user = fields.OneToOneField("darius.User", related_name="referral_user", on_delete=fields.CASCADE, null=True)
    referrer = fields.ForeignKeyField("darius.Referral", related_name="referral_referrer", null=True)
    referral_code = fields.CharField(8, null=False, unqiue=True)
    register_count = fields.IntField(null=False, default=0)
    bot_count = fields.IntField(null=False, default=0)
    subscribe_count = fields.IntField(null=False, default=0)
    total_rebate = fields.FloatField(null=False, default=0)
    rebate_rate = fields.FloatField(null=False, default=0.1)
    referrer_rebate_rate = fields.FloatField(null=False, default=0.1)
    referral_rebate_rate = fields.FloatField(null=False, default=0)

    class Meta:
        table = "referral"
        table_description = "Referral"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "id", "is_del"]

    def __str__(self):
        return f"Referral [{self.id}]"


ReferralSchemaModel = pydantic_model_creator(Referral, name="Referral")
ReferralInSchemaModel = pydantic_model_creator(Referral, name="ReferralIn", exclude_readonly=True)


class ReferralHistory(BaseModel):

    referrer = fields.ForeignKeyField("darius.Referral", related_name="referral_history_referrer", on_delete=fields.CASCADE, null=False)
    referral = fields.ForeignKeyField("darius.Referral", related_name="referral_history_referral", on_delete=fields.CASCADE, null=False)
    bot = fields.ForeignKeyField("darius.BotOrder", related_name="referral_history_bot", on_delete=fields.CASCADE, null=True, unqiue=True)
    subscription = fields.ForeignKeyField("darius.Subscription", related_name="referral_history_subscription", on_delete=fields.CASCADE, null=True, unqiue=True)
    rebate = fields.FloatField(null=False, default=0)
    referrer_rebate_rate = fields.FloatField(null=False, default=0.1)
    referral_rebate_rate = fields.FloatField(null=False, default=0)

    class Meta:
        table = "referral_history"
        table_description = "ReferralHistory"
        ordering = ["-created_at", "id"]

    class PydanticMeta:
        exclude = ["created_at", "updated_at", "id", "is_del", "referrer_rebate_rate", "referral_rebate_rate"]

    def __str__(self):
        return f"ReferralHistory [{self.id}]"


ReferralHistorySchemaModel = pydantic_model_creator(ReferralHistory, name="ReferralHistory")
ReferralHistoryInSchemaModel = pydantic_model_creator(ReferralHistory, name="ReferralHistoryIn", exclude_readonly=True)
