"""
Точка входа ВК-бота.
Здесь регистрируются все хендлеры сообщений и callback-событий.
"""

import asyncio
import logging

from vkbottle import GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from config import ADMIN_IDS, VK_TOKEN
from database.crud import init_db
from keyboards import start_kb
from session import session
from states import AdminStates, CalcStates

# ── Импорт хендлеров ─────────────────────────────────────────
from handlers.user.calculator import (
    handle_calc_start,
    handle_obj_flat, handle_obj_house,
    handle_building_type,
    handle_outdoor_yes, handle_outdoor_no,
    handle_outdoor_toggle, handle_outdoor_done,
    handle_enter_area, handle_rooms,
    handle_wall_toggle, handle_wall_done,
    handle_enter_city, handle_enter_district,
    handle_enter_sockets, handle_enter_switches,
    handle_enter_spots, handle_enter_lamps_simple, handle_enter_lamps_hard,
    handle_enter_stove, handle_enter_oven, handle_enter_ac,
    handle_enter_floor_heating, handle_enter_washing, handle_enter_dishwasher,
    handle_boiler, handle_shield, handle_low_voltage,
    handle_demolition_yes, handle_demolition_no, handle_enter_demolition_count,
    handle_extra_skip, handle_enter_extra_info,
    handle_enter_name, handle_enter_phone, handle_contact_method,
    _BUILDING_MAP, _ROOMS_MAP, _CONTACT_MAP,
)
from handlers.user.confirm import (
    handle_submit_lead, handle_edit_data, handle_cancel_lead,
)
from handlers.admin.admin_menu import (
    handle_admin_command, handle_adm_back, handle_adm_view, handle_adm_stats,
)
from handlers.admin.prices import (
    handle_adm_prices, handle_edit_price, handle_new_price_input,
    handle_adm_coeffs, handle_edit_coeff, handle_new_coeff_input,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

bot = Bot(token=VK_TOKEN)

WELCOME_TEXT = (
    "Добро пожаловать!\n\n"
    "Я помогу рассчитать примерную стоимость электромонтажных работ "
    "в вашей квартире или доме в Ростове-на-Дону и Батайске.\n\n"
    "Расчёт является предварительным. "
    "Точная смета составляется после выезда специалиста или по вашему проекту. "
    "Осмотр объекта — бесплатно.\n\n"
    "Нажмите кнопку ниже, чтобы начать:"
)


# ════════════════════════════════════════════════════════════
# ХЕНДЛЕРЫ ТЕКСТОВЫХ СООБЩЕНИЙ (по состоянию FSM)
# ════════════════════════════════════════════════════════════

@bot.on.message(text=["/start", "Начать", "начать", "старт", "Старт"])
async def cmd_start(message: Message) -> None:
    log.info("User %s started bot", message.peer_id)
    session.clear(message.peer_id)
    await bot.state_dispenser.delete(message.peer_id)
    result = await message.answer(WELCOME_TEXT, keyboard=start_kb)
    session.set_last_msg(message.peer_id, result)


@bot.on.message(text=["/admin", "admin"])
async def cmd_admin(message: Message) -> None:
    await handle_admin_command(bot, message)


@bot.on.message(text=["/cancel", "отмена", "Отмена"])
async def cmd_cancel(message: Message) -> None:
    session.clear(message.peer_id)
    await bot.state_dispenser.delete(message.peer_id)
    result = await message.answer("Опрос отменён. Главное меню:", keyboard=start_kb)
    session.set_last_msg(message.peer_id, result)


# ── Состояния калькулятора (текстовый ввод) ──────────────────

@bot.on.message(state=CalcStates.enter_city)
async def on_enter_city(message: Message) -> None:
    await handle_enter_city(bot, message)


@bot.on.message(state=CalcStates.enter_district)
async def on_enter_district(message: Message) -> None:
    await handle_enter_district(bot, message)


@bot.on.message(state=CalcStates.enter_area)
async def on_enter_area(message: Message) -> None:
    await handle_enter_area(bot, message)


@bot.on.message(state=CalcStates.enter_sockets)
async def on_enter_sockets(message: Message) -> None:
    await handle_enter_sockets(bot, message)


@bot.on.message(state=CalcStates.enter_switches)
async def on_enter_switches(message: Message) -> None:
    await handle_enter_switches(bot, message)


@bot.on.message(state=CalcStates.enter_spots)
async def on_enter_spots(message: Message) -> None:
    await handle_enter_spots(bot, message)


@bot.on.message(state=CalcStates.enter_lamps_simple)
async def on_enter_lamps_simple(message: Message) -> None:
    await handle_enter_lamps_simple(bot, message)


@bot.on.message(state=CalcStates.enter_lamps_hard)
async def on_enter_lamps_hard(message: Message) -> None:
    await handle_enter_lamps_hard(bot, message)


@bot.on.message(state=CalcStates.enter_stove)
async def on_enter_stove(message: Message) -> None:
    await handle_enter_stove(bot, message)


@bot.on.message(state=CalcStates.enter_oven)
async def on_enter_oven(message: Message) -> None:
    await handle_enter_oven(bot, message)


@bot.on.message(state=CalcStates.enter_ac)
async def on_enter_ac(message: Message) -> None:
    await handle_enter_ac(bot, message)


@bot.on.message(state=CalcStates.enter_floor_heating)
async def on_enter_floor_heating(message: Message) -> None:
    await handle_enter_floor_heating(bot, message)


@bot.on.message(state=CalcStates.enter_washing_machine)
async def on_enter_washing(message: Message) -> None:
    await handle_enter_washing(bot, message)


@bot.on.message(state=CalcStates.enter_dishwasher)
async def on_enter_dishwasher(message: Message) -> None:
    await handle_enter_dishwasher(bot, message)


@bot.on.message(state=CalcStates.enter_demolition_count)
async def on_enter_demolition_count(message: Message) -> None:
    await handle_enter_demolition_count(bot, message)


@bot.on.message(state=CalcStates.enter_extra_info)
async def on_enter_extra_info(message: Message) -> None:
    await handle_enter_extra_info(bot, message)


@bot.on.message(state=CalcStates.enter_name)
async def on_enter_name(message: Message) -> None:
    await handle_enter_name(bot, message)


@bot.on.message(state=CalcStates.enter_phone)
async def on_enter_phone(message: Message) -> None:
    await handle_enter_phone(bot, message)


# ── Состояния админки (текстовый ввод) ───────────────────────

@bot.on.message(state=AdminStates.enter_new_price)
async def on_new_price(message: Message) -> None:
    await handle_new_price_input(bot, message)


@bot.on.message(state=AdminStates.enter_new_coeff)
async def on_new_coeff(message: Message) -> None:
    await handle_new_coeff_input(bot, message)


# ════════════════════════════════════════════════════════════
# ЦЕНТРАЛЬНЫЙ РОУТЕР CALLBACK-СОБЫТИЙ (кнопки)
# ════════════════════════════════════════════════════════════

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def on_callback(event: MessageEvent) -> None:
    """Единый обработчик всех нажатий на кнопки."""
    cmd = event.payload.get("cmd", "")
    peer_id = event.peer_id

    # ── Запуск калькулятора ──────────────────────────────────
    if cmd == "calc_start":
        await handle_calc_start(bot, event)

    # ── Тип объекта ─────────────────────────────────────────
    elif cmd == "obj_flat":
        await handle_obj_flat(bot, event)
    elif cmd == "obj_house":
        await handle_obj_house(bot, event)

    # ── Тип жилья / этажность ───────────────────────────────
    elif cmd in _BUILDING_MAP:
        await handle_building_type(bot, event, cmd)

    # ── Работы на участке ────────────────────────────────────
    elif cmd == "yn_yes":
        state = await bot.state_dispenser.get(peer_id)
        state_name = state.state if state else None
        from states import CalcStates, AdminStates
        if state_name == CalcStates.ask_outdoor_work:
            await handle_outdoor_yes(bot, event)
        elif state_name == CalcStates.enter_boiler:
            await handle_boiler(bot, event, True)
        elif state_name == CalcStates.ask_shield:
            await handle_shield(bot, event, True)
        elif state_name == CalcStates.ask_low_voltage:
            await handle_low_voltage(bot, event, True)
        elif state_name == CalcStates.ask_demolition:
            await handle_demolition_yes(bot, event)

    elif cmd == "yn_no":
        state = await bot.state_dispenser.get(peer_id)
        state_name = state.state if state else None
        from states import CalcStates
        if state_name == CalcStates.ask_outdoor_work:
            await handle_outdoor_no(bot, event)
        elif state_name == CalcStates.enter_boiler:
            await handle_boiler(bot, event, False)
        elif state_name == CalcStates.ask_shield:
            await handle_shield(bot, event, False)
        elif state_name == CalcStates.ask_low_voltage:
            await handle_low_voltage(bot, event, False)
        elif state_name == CalcStates.ask_demolition:
            await handle_demolition_no(bot, event)

    elif cmd.startswith("outdoor_toggle_"):
        key = cmd.replace("outdoor_toggle_", "")
        await handle_outdoor_toggle(bot, event, key)
    elif cmd == "outdoor_done":
        await handle_outdoor_done(bot, event)

    # ── Комнаты ─────────────────────────────────────────────
    elif cmd in _ROOMS_MAP:
        await handle_rooms(bot, event, cmd)

    # ── Материал стен ────────────────────────────────────────
    elif cmd.startswith("wall_toggle_"):
        key = cmd.replace("wall_toggle_", "")
        await handle_wall_toggle(bot, event, key)
    elif cmd == "wall_done":
        await handle_wall_done(bot, event)

    # ── Доп. сведения ────────────────────────────────────────
    elif cmd == "extra_skip":
        await handle_extra_skip(bot, event)

    # ── Способ связи ─────────────────────────────────────────
    elif cmd in _CONTACT_MAP:
        await handle_contact_method(bot, event, cmd)

    # ── Подтверждение заявки ─────────────────────────────────
    elif cmd == "submit_lead":
        await handle_submit_lead(bot, event)
    elif cmd == "edit_data":
        await handle_edit_data(bot, event)
    elif cmd == "cancel_lead":
        await handle_cancel_lead(bot, event)

    # ── Админ-панель ─────────────────────────────────────────
    elif cmd == "adm_back":
        await handle_adm_back(bot, event)
    elif cmd == "adm_view":
        await handle_adm_view(bot, event)
    elif cmd == "adm_stats":
        await handle_adm_stats(bot, event)
    elif cmd == "adm_prices":
        await handle_adm_prices(bot, event)
    elif cmd == "adm_coeffs":
        await handle_adm_coeffs(bot, event)
    elif cmd.startswith("edit_price_"):
        key = cmd.replace("edit_price_", "")
        await handle_edit_price(bot, event, key)
    elif cmd.startswith("edit_coeff_"):
        key = cmd.replace("edit_coeff_", "")
        await handle_edit_coeff(bot, event, key)


# ════════════════════════════════════════════════════════════
# ЗАПУСК
# ════════════════════════════════════════════════════════════

async def main() -> None:
    if not VK_TOKEN:
        raise ValueError("API_TOKEN не задан в переменных окружения")
    await init_db()
    log.info("Database initialized")
    log.info("VK bot started")
    await bot.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
