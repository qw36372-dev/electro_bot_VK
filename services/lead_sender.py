"""Отправка заявки в беседу/диалог ВКонтакте."""

import logging
from vkbottle.bot import Bot

from config import LEADS_CHAT_ID
from database.models import Lead
from utils.formatters import format_lead_message

log = logging.getLogger(__name__)


async def send_lead_to_chat(bot: Bot, lead: Lead) -> bool:
    if not LEADS_CHAT_ID:
        log.warning("LEADS_CHAT_ID не задан — заявка не отправлена в беседу")
        return False
    text = format_lead_message(lead)
    try:
        await bot.api.messages.send(
            peer_id=LEADS_CHAT_ID,
            message=text,
            random_id=0,
        )
        return True
    except Exception as exc:
        log.error("Ошибка отправки заявки в беседу: %s", exc)
        return False
