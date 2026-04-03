"""Административная панель ВК-бота."""

import logging
from vkbottle.bot import Bot, Message, MessageEvent

from config import ADMIN_IDS
from database.crud import get_all_settings, get_stats
from keyboards import admin_menu_kb, back_kb
from session import session
from utils.formatters import format_all_settings

log = logging.getLogger(__name__)


def is_admin(peer_id: int) -> bool:
    return peer_id in ADMIN_IDS


async def handle_admin_command(bot: Bot, message: Message) -> None:
    if not is_admin(message.peer_id):
        await message.answer("Доступ запрещён.")
        return
    log.info("Admin %s opened admin panel", message.peer_id)
    result = await bot.api.messages.send(
        peer_id=message.peer_id,
        message="Панель администратора\nВыберите раздел:",
        keyboard=admin_menu_kb,
        random_id=0,
    )
    session.set_last_msg(message.peer_id, result)


async def handle_adm_back(bot: Bot, event: MessageEvent) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    from states import AdminStates
    await bot.state_dispenser.delete(event.peer_id)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Панель администратора\nВыберите раздел:",
        keyboard=admin_menu_kb,
    )


async def handle_adm_view(bot: Bot, event: MessageEvent) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    settings = await get_all_settings()
    text = format_all_settings(settings)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message=text,
        keyboard=back_kb,
    )


async def handle_adm_stats(bot: Bot, event: MessageEvent) -> None:
    if not is_admin(event.peer_id):
        await event.show_snackbar("Доступ запрещён")
        return
    stats = await get_stats()
    text = (
        "📊 Статистика заявок\n\n"
        f"Всего заявок: {stats['total']}\n"
        f"Сегодня: {stats['today']}\n"
        f"За неделю: {stats['week']}\n"
        f"За месяц: {stats['month']}\n\n"
        f"Средняя стоимость: {stats['avg_price']:,} руб.\n\n".replace(",", "\u00a0")
        + f"Квартиры: {stats['apt_count']}\n"
        f"Дома: {stats['house_count']}"
    )
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message=text,
        keyboard=back_kb,
    )
