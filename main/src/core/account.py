import logging
from tortoise.transactions import atomic
from main.src.models import User


logger = logging.getLogger(__name__)


@atomic()
async def _update_user_profile(user_id: int, user_name: str, email: str):
    user = await User.filter(id=user_id).first()
    user.user_name = user_name
    user.email = email
    await user.save()
