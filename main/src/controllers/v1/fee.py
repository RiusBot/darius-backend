from aiohttp.web import json_response
from main.src.core import fee
from main.src.core.auth import authenticate


async def user_confirm_payment(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    uid = json_payload.get("uid")
    address = json_payload.get("address")
    txid = json_payload.get("txid")
    referal = json_payload.get("referal")
    plan = json_payload.get("plan")

    confirm_status, new_due_date = fee.corfirm_user_payment(uid, address, txid, referal, plan)

    return json_response(
        status=200,
        data={
            'status': True,
            'message': 'payment confirm' if confirm_status else 'payment not recieved',
            'new_due_date': new_due_date
        }
    )


async def get_user_due_date(request):

    json_payload = await request.json()
    if authenticate(json_payload) is False:
        response_data = {
            "message": "access token is not valid"
        }
        return json_response(data=response_data, status=401)

    uid = json_payload.get("uid")
    user_due_date = fee.get_user_due_date(uid)

    return json_response(
        status=200,
        data={
            'status': True,
            'message': 'The service is healthy based on liveness healthcheck',
            "due_date": user_due_date
        }
    )
