import os
import json
import ccxt
import random
import string
import logging
from typing import Tuple
from functools import wraps
from aiohttp.web import json_response
from tortoise.queryset import QuerySet

from main.src.core.cipher import decrypt
from main.src.exception import BackendException
from main.src.core.auth import fetch_secret_token_firestore
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)
usingProjectId = os.getenv('project_id', 'local')


def generate_random_string(k: int):
    return ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits,
        k=k,
    ))


async def pagination(query, page: int, pagesize: int) -> Tuple[QuerySet, int, int]:
    total_count = await query.limit(1000).count()
    totalpage = (total_count // pagesize) + (total_count % pagesize != 0)
    if totalpage > 0 and page >= totalpage:
        raise BackendException("Invalid page")
    offset = page * pagesize
    limit = pagesize
    logger.info(f"pagination {page}/{totalpage} size {pagesize}")
    return query.offset(offset).limit(limit), total_count, totalpage


def data_decrypt(data: dict):
    try:
        if 'api_key' in data:
            if "api_secret" in data:
                data["api_secret"] = decrypt(data["api_key"], data["api_secret"])
            if "password" in data:
                data["password"] = decrypt(data["api_key"], data["password"]) if data["password"] else ""

            if data["api_key"] == "9a53750a-5af4-4636-906c-c3e558801694":
                data["headers"] = {'x-simulated-trading': '1'}
            else:
                data["headers"] = {}
    except Exception:
        logger.error('Decrypt Error')
        logger.exception("")
    return data


async def fetch(session, sem, url: str, request_data: dict, max_retry: int = 3, error: str = "ERROR", timeout: int = 60):
    if request_data.get("test"):
        return "Test only"
    try:
        async with sem:
            request_data["token"] = fetch_secret_token_firestore()
            request_data = data_decrypt(request_data)

            for i in range(max_retry):
                async with session.post(url, json=request_data, timeout=timeout) as response:
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

    except Exception:
        logger.exception("")
        return error


def error_handler():
    def _error_handler(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):

            try:
                data = await f(*args, **kwargs)
                return json_response(
                    status=200,
                    data={} if data is None else data
                )
            except BackendException as e:
                logger.error(f"{e}")
                return json_response(
                    status=400,
                    data={
                        'code': 400,
                        'message': str(e)
                    }
                )
            except ccxt.BaseError as e:
                logger.error(f"{e}")
                return json_response(
                    status=400,
                    data={
                        'code': 400,
                        'message': repr(e)
                    }
                )
            except Exception:
                logger.exception("")
                return json_response(
                    status=500,
                    data={
                        'code': 500,
                        'message': "Unexpected Error"
                    }
                )

        return wrapper
    return _error_handler


def input_filter(filtered=True):
    def _input_filter(f):
        @wraps(f)
        async def wrapper(request, *args, **kwargs):

            if request.method == "GET":
                json_payload = dict(request.rel_url.query)
                if filtered:
                    json_payload = filter_illegal_char(json_payload)
            else:
                try:
                    json_payload = await request.json()
                    if filtered:
                        json_payload = filter_illegal_char(json_payload)
                except json.decoder.JSONDecodeError:
                    json_payload = {}

            args = filter_illegal_char({e: i for e, i in enumerate(args)})
            args = [args[key] for key in sorted(args.keys())]
            kwargs = filter_illegal_char(kwargs)
            return await f(json_payload, *args, **kwargs)

        return wrapper
    return _input_filter
