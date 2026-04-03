"""Управление ценами и коэффициентами через админ-панель ВК."""

import logging
from vkbottle.bot import Bot, Message, MessageEvent

from config import ADMIN_IDS, COEFF_LABELS, PRICE_LABELS
from database.crud import get_all_settings, set_setting
from keyboards import coeffs_kb, prices_kb
from session import session
from states import AdminStates
from utils.validators import validate_positive_number

log = logging.getLogger(__name__)


def is_admin(peer_id: int) -> bool:
    return peer_id in ADMIN_IDS


# ── Цены ─────────────────────────────────────────────────────

async def handle_adm_prices(bot: Bot, event: MessageEvent) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    await bot.state_dispenser.set(event.peer_id, AdminStates.choose_price_item)
    settings = await get_all_settings()
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Управление ценами\nВыберите позицию для редактирования:",
        keyboard=prices_kb(settings),
    )


async def handle_edit_price(bot: Bot, event: MessageEvent, key: str) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    label = PRICE_LABELS.get(key, key)
    settings = await get_all_settings()
    current = int(settings.get(key, 0))
    session.update(event.peer_id, editing_key=key)
    await bot.state_dispenser.set(event.peer_id, AdminStates.enter_new_price)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message=f"{label}\nТекущая цена: {current} руб.\n\nВведите новую цену (руб.):",
        keyboard="",
    )


async def handle_new_price_input(bot: Bot, message: Message) -> None:
    if not is_admin(message.peer_id):
        return
    value = validate_positive_number(message.text or "")
    if value is None or value <= 0:
        await message.answer("Введите корректную цену > 0:")
        return
    data = session.get(message.peer_id)
    key = data.get("editing_key")
    label = PRICE_LABELS.get(key, key)
    await set_setting(key, value)
    log.info("Admin %s set %s = %s", message.peer_id, key, value)
    await bot.state_dispenser.set(message.peer_id, AdminStates.choose_price_item)
    settings = await get_all_settings()
    await message.answer(f"Цена «{label}» обновлена: {int(value)} руб.")
    result = await bot.api.messages.send(
        peer_id=message.peer_id,
        message="Управление ценами\nВыберите позицию:",
        keyboard=prices_kb(settings),
        random_id=0,
    )
    session.set_last_msg(message.peer_id, result)


# ── Коэффициенты ─────────────────────────────────────────────

async def handle_adm_coeffs(bot: Bot, event: MessageEvent) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    await bot.state_dispenser.set(event.peer_id, AdminStates.choose_coeff_item)
    settings = await get_all_settings()
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Управление коэффициентами\nВыберите параметр:",
        keyboard=coeffs_kb(settings),
    )


async def handle_edit_coeff(bot: Bot, event: MessageEvent, key: str) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    label = COEFF_LABELS.get(key, key)
    settings = await get_all_settings()
    current = settings.get(key, 0)
    session.update(event.peer_id, editing_key=key)
    await bot.state_dispenser.set(event.peer_id, AdminStates.enter_new_coeff)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message=f"{label}\nТекущее значение: {current}\n\nВведите новое значение:\n"
                "(напр. 1.15 = +15%, для разброса 0.10 = ±10%)",
        keyboard="",
    )


async def handle_new_coeff_input(bot: Bot, message: Message) -> None:
    if not is_admin(message.peer_id):
        return
    value = validate_positive_number(message.text or "")
    if value is None or value <= 0:
        await message.answer("Введите корректное положительное число (например 1.15 или 0.10):")
        return
    data = session.get(message.peer_id)
    key = data.get("editing_key")
    label = COEFF_LABELS.get(key, key)
    await set_setting(key, value)
    log.info("Admin %s set %s = %s", message.peer_id, key, value)
    await bot.state_dispenser.set(message.peer_id, AdminStates.choose_coeff_item)
    settings = await get_all_settings()
    await message.answer(f"«{label}» обновлён: {value}")
    result = await bot.api.messages.send(
        peer_id=message.peer_id,
        message="Управление коэффициентами\nВыберите параметр:",
        keyboard=coeffs_kb(settings),
        random_id=0,
    )
    session.set_last_msg(message.peer_id, result)
