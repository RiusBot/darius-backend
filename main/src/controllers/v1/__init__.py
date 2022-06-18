import ccxt
import logging
from functools import wraps
from aiohttp.web import json_response
from main.src.exception import BackendException
from main.src.core.validator import filter_illegal_char


logger = logging.getLogger(__name__)


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


def input_filter(f):
    @wraps(f)
    async def wrapper(request, *args, **kwargs):

        if request.method == "GET":
            json_payload = dict(request.rel_url.query)
            json_payload = filter_illegal_char(json_payload)
        else:
            json_payload = await request.json()
            json_payload = filter_illegal_char(json_payload)

        args = filter_illegal_char({e: i for e, i in enumerate(args)})
        args = [args[key] for key in sorted(args.keys())]
        kwargs = filter_illegal_char(kwargs)
        return await f(json_payload, *args, **kwargs)

    return wrapper
