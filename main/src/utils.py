import os
import json
import random
import string
import logging

from main.src.core.cipher import decrypt
from main.src.exception import BackendException
from main.src.core.auth import fetch_secret_token_firestore


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


def generate_random_string(k: int):
    return ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits,
        k=k,
    ))


def pagination(page: int, pagesize: int, totalpage: int):
    if totalpage > 0 and page >= totalpage:
        raise BackendException("Invalid page")
    offset = page * pagesize
    limit = pagesize
    logger.info(f"pagination {page}/{totalpage} size {pagesize}")
    return offset, limit


def data_decrypt(data: dict):
    try:
        if 'api_key' in data:
            if "api_secret" in data:
                data["api_secret"] = decrypt(data["api_key"], data["api_secret"])
            if "password" in data:
                data["password"] = decrypt(data["api_key"], data["password"]) if data["password"] else ""
    except Exception:
        logger.error('Decrypt Error')
        logger.exception("")
    return data


async def fetch(session, sem, url: str, request_data: dict, max_retry: int = 3, error: str = "ERROR"):
    if request_data.get("test"):
        return "Test only"
    try:
        async with sem:
            request_data["token"] = fetch_secret_token_firestore() if usingProjectId != "local" else ""
            request_data = data_decrypt(request_data)

            for i in range(max_retry):
                async with session.post(url, json=request_data, timeout=15) as response:
                    response = await response.text()

                    if (isinstance(response, str) and ("Rate exceeded" in response or "DDoSProtection" in response or "Too many requests" in response)):
                        continue

                    try:
                        response = json.loads(response)
                        if "error_message" in response:
                            response = str(response["error_message"])
                        elif "error_messages" in response:
                            response = str(response["error_messages"])
                    except Exception:
                        # return text if json parse failed
                        pass

                    return response

            return error

    except Exception as e:
        logger.exception("")
        # return str(e)
        # logger.error(str(e))
        return error
