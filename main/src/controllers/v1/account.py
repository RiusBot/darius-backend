import logging
from main.src.models.user import User
from aiohttp.web import json_response

logger = logging.getLogger(__name__)

async def update_user_profile(request):
    json_payload = await request.json()
    try:
        logger.info("Update user profile %s", json_payload)
        user_id = json_payload["user_id"]
        user_name = json_payload["user_name"]
        email = json_payload["email"]
        user = await User.filter(id=user_id).first()
        user.user_name = user_name
        user.email = email
        await user.save()

        return json_response(status=200)
    except Exception as ex:
        logger.exception("Unexpected error when updating user profile, due to: %s", ex)
        return json_response(
            status=500,
            data={
                'code': 500,
                'message': str(ex)
            }
        )
