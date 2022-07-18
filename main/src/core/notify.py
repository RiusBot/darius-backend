import logging
import asyncio
from typing import List
from tortoise.transactions import atomic

from main.src.models import Notify, User
from main.src.models.notify import MessageTemplate, ConfigTemplate
from main.src.core.telegram import _user_telegram_send_message
from main.src.core.permission import permission_validator


logger = logging.getLogger(__name__)


async def notify(user: User, service: str, info: dict):
    try:
        notify_list = await Notify.filter(user=user, service=service, is_del=False)
        msg = MessageTemplate(service, info)
        for notify in notify_list:
            if notify.notify == "TELEGRAM":
                await _user_telegram_send_message(user.uid, msg)
            elif notify.notify == "SMS":
                pass
            elif notify.notify == "EMAIL":
                pass
    except Exception:
        logger.error("notify error")
        logger.exception("")


async def entries_to_dict(entries: List[Notify]):
    notify_config = ConfigTemplate()
    for entry in entries:
        notify_config[entry.notify][entry.service] = True
    return notify_config


async def dict_to_entries(user: User, notify_config: dict):
    inst_query = []
    input_list = []
    for notify in notify_config:
        for service in notify_config[notify]:
            query = Notify.filter(is_del=False, service=service, notify=notify).first()
            inst_query.append(query)
            input_list.append((notify, service))

    inst_list = await asyncio.gather(*inst_query)
    query = []

    for (notify, service), inst in zip(input_list, inst_list):
        if notify_config[notify][service] and inst is None:
            # create
            query.append(Notify.create(user=user, service=service, notify=notify))
            logger.debug(f"create {notify} {service}")
        elif not notify_config[notify][service] and inst:
            # drop
            query.append(inst.delete())
            logger.debug(f"delete {notify} {service}")

    await asyncio.gather(*query)


@atomic()
@permission_validator("get_user_notify")
async def _get_user_notify(user: User) -> dict:
    uid = user.uid
    logger.info(f"Get notify for user {uid}")
    notify_entries = await Notify.filter(user=user, is_del=False)
    notify_config = await entries_to_dict(notify_entries)
    return notify_config


@atomic()
@permission_validator("create_user_notify")
async def _create_user_notify(user: User, notify_config: dict):
    return


@atomic()
@permission_validator("update_user_notify")
async def _update_user_notify(user: User, notify_config: dict):
    uid = user.uid
    logger.info(f"Update notify for user [{uid}]")
    await dict_to_entries(user, notify_config)


@atomic()
@permission_validator("delete_user_notify")
async def _delete_user_notify(user: User) -> int:
    return
