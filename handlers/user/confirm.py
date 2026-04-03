"""Подтверждение расчёта и отправка заявки."""

import logging
from datetime import datetime

from vkbottle.bot import Bot, MessageEvent

from config import SPAM_INTERVAL
from database.crud import create_lead, get_last_lead_time
from keyboards import confirm_kb, start_kb
from services.lead_sender import send_lead_to_chat
from services.pricing import calculate_price
from session import session
from utils.formatters import format_summary

log = logging.getLogger(__name__)


async def show_confirmation(bot: Bot, event: MessageEvent) -> None:
    """Рассчитать стоимость и показать итоговую сводку."""
    peer_id = event.peer_id
    data = session.get(peer_id)
    price_min, price_max = await calculate_price(data)
    session.update(peer_id, price_min=price_min, price_max=price_max)

    from states import CalcStates
    await bot.state_dispenser.set(peer_id, CalcStates.confirm)

    text = format_summary(data, price_min, price_max)
    cmid = session.get_last_msg(peer_id)
    if cmid:
        try:
            await bot.api.messages.edit(
                peer_id=peer_id,
                conversation_message_id=cmid,
                message=text,
                keyboard=confirm_kb,
            )
            return
        except Exception:
            pass
    result = await bot.api.messages.send(
        peer_id=peer_id, message=text, keyboard=confirm_kb, random_id=0
    )
    session.set_last_msg(peer_id, result)


async def handle_submit_lead(bot: Bot, event: MessageEvent) -> None:
    """Антиспам + сохранение + отправка заявки."""
    peer_id = event.peer_id

    last_time = await get_last_lead_time(peer_id)
    if last_time:
        elapsed = (datetime.utcnow() - last_time).total_seconds()
        if elapsed < SPAM_INTERVAL:
            wait = int(SPAM_INTERVAL - elapsed)
            await event.show_snackbar(f"Следующую заявку можно отправить через {wait} сек.")
            return

    data = session.get(peer_id)
    lead_data = {
        "user_id": peer_id,
        "username": None,
        "city": data.get("city"),
        "district": data.get("district"),
        "object_type": data.get("object_type"),
        "building_type": data.get("building_type"),
        "outdoor_work": data.get("outdoor_work", "Нет"),
        "area": data.get("area"),
        "rooms": data.get("rooms"),
        "wall_material": data.get("wall_material"),
        "sockets": data.get("sockets", 0),
        "switches": data.get("switches", 0),
        "spots": data.get("spots", 0),
        "lamps_simple": data.get("lamps_simple", 0),
        "lamps_hard": data.get("lamps_hard", 0),
        "stove": data.get("stove", 0),
        "oven": data.get("oven", 0),
        "ac": data.get("ac", 0),
        "boiler": data.get("boiler", False),
        "floor_heating": data.get("floor_heating", 0.0),
        "washing_machine": data.get("washing_machine", 0),
        "dishwasher": data.get("dishwasher", 0),
        "shield_needed": data.get("shield_needed", False),
        "low_voltage": data.get("low_voltage", False),
        "demolition": data.get("demolition", 0),
        "extra_info": data.get("extra_info", ""),
        "price_min": data.get("price_min"),
        "price_max": data.get("price_max"),
        "client_name": data.get("client_name"),
        "client_phone": data.get("client_phone"),
        "contact_method": data.get("contact_method"),
    }

    lead = await create_lead(lead_data)
    log.info("New lead #%s from peer %s", lead.id, peer_id)
    await send_lead_to_chat(bot, lead)

    session.clear(peer_id)
    await bot.state_dispenser.delete(peer_id)

    cmid = session.get_last_msg(peer_id)
    thanks = "✅ Спасибо! Ваша заявка отправлена.\nМастер свяжется с вами в ближайшее время."
    if cmid:
        try:
            await bot.api.messages.edit(
                peer_id=peer_id,
                conversation_message_id=cmid,
                message=thanks,
                keyboard="",
            )
        except Exception:
            await bot.api.messages.send(peer_id=peer_id, message=thanks, random_id=0)
    else:
        await bot.api.messages.send(peer_id=peer_id, message=thanks, random_id=0)

    await bot.api.messages.send(
        peer_id=peer_id,
        message="Главное меню:",
        keyboard=start_kb,
        random_id=0,
    )


async def handle_edit_data(bot: Bot, event: MessageEvent) -> None:
    from states import CalcStates
    from keyboards import object_type_kb
    session.clear(event.peer_id)
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_city)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Из какого вы города?\nВведите название города",
        keyboard="",
    )


async def handle_cancel_lead(bot: Bot, event: MessageEvent) -> None:
    session.clear(event.peer_id)
    await bot.state_dispenser.delete(event.peer_id)
    try:
        await bot.api.messages.edit(
            peer_id=event.peer_id,
            conversation_message_id=session.get_last_msg(event.peer_id),
            message="Заявка отменена.",
            keyboard="",
        )
    except Exception:
        pass
    await bot.api.messages.send(
        peer_id=event.peer_id, message="Главное меню:", keyboard=start_kb, random_id=0
    )
