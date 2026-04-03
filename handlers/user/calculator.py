"""
Основной флоу калькулятора для ВК.
Хендлеры сообщений (текстовый ввод) и callback-событий (кнопки).
"""

import logging
from vkbottle.bot import Bot, Message, MessageEvent

from keyboards import (
    building_type_flat_kb, building_type_house_kb,
    contact_kb, object_type_kb, outdoor_kb_multi,
    rooms_kb, skip_extra_kb, wall_kb_multi, yes_no_kb,
    WALL_KEY_TO_LABEL, OUTDOOR_KEY_TO_LABEL,
)
from session import session
from states import CalcStates
from utils.validators import sanitize_text, validate_phone, validate_positive_integer, validate_positive_number

log = logging.getLogger(__name__)

EXTRA_INFO_TEXT = (
    "Дополнительные сведения мастеру\n\n"
    "Здесь вы можете описать свои пожелания, другие условия работы "
    "или любую информацию, которую не удалось указать в опросе.\n\n"
    "Данные не влияют на предварительный расчёт, но будут полезны мастеру.\n\n"
    "Для пропуска нажмите НЕТ"
)


# ── Хелперы ──────────────────────────────────────────────────

async def _send(bot: Bot, peer_id: int, text: str, keyboard: str = None) -> None:
    """Отправить новое сообщение и сохранить его cmid в сессии."""
    params = dict(peer_id=peer_id, message=text, random_id=0)
    if keyboard:
        params["keyboard"] = keyboard
    result = await bot.api.messages.send(**params)
    # result — conversation_message_id нового сообщения
    session.set_last_msg(peer_id, result)


async def _edit(bot: Bot, peer_id: int, text: str, keyboard: str = None) -> None:
    """Отредактировать последнее сообщение бота (чистый чат)."""
    cmid = session.get_last_msg(peer_id)
    if cmid:
        try:
            params = dict(peer_id=peer_id, conversation_message_id=cmid, message=text)
            if keyboard:
                params["keyboard"] = keyboard
            else:
                params["keyboard"] = ""   # убрать клавиатуру
            await bot.api.messages.edit(**params)
            return
        except Exception:
            pass
    # Fallback: отправить новое
    await _send(bot, peer_id, text, keyboard)


# ── Запуск ───────────────────────────────────────────────────

async def handle_calc_start(bot: Bot, event: MessageEvent) -> None:
    peer_id = event.peer_id
    session.clear(peer_id)
    await bot.state_dispenser.set(peer_id, CalcStates.enter_city)
    await _edit(bot, peer_id,
        "Из какого вы города?\nВведите название города",
    )


# ── Город ────────────────────────────────────────────────────

async def handle_enter_city(bot: Bot, message: Message) -> None:
    city = sanitize_text(message.text or "", max_length=100)
    if len(city) < 2:
        return
    session.update(message.peer_id, city=city)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_district)
    await _edit(bot, message.peer_id,
        "Какой район или ЖК?\nВведите район или название жилого комплекса",
    )


# ── Район/ЖК ─────────────────────────────────────────────────

async def handle_enter_district(bot: Bot, message: Message) -> None:
    district = sanitize_text(message.text or "", max_length=150)
    if len(district) < 2:
        return
    session.update(message.peer_id, district=district)
    await bot.state_dispenser.set(message.peer_id, CalcStates.choose_object_type)
    await _edit(bot, message.peer_id, "Выберите тип объекта:", object_type_kb)


# ── Тип объекта ──────────────────────────────────────────────

async def handle_obj_flat(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, object_type="квартира")
    await bot.state_dispenser.set(event.peer_id, CalcStates.choose_building_type)
    await _edit(bot, event.peer_id, "Тип жилья:", building_type_flat_kb)


async def handle_obj_house(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, object_type="дом")
    await bot.state_dispenser.set(event.peer_id, CalcStates.choose_building_type)
    await _edit(bot, event.peer_id, "Количество этажей:", building_type_house_kb)


# ── Тип жилья ─────────────────────────────────────────────────

_BUILDING_MAP = {
    "bt_new": "новостройка", "bt_old": "вторичка",
    "bt_1floor": "1 этаж", "bt_2floor": "2+ этажа",
}


async def handle_building_type(bot: Bot, event: MessageEvent, cmd: str) -> None:
    building = _BUILDING_MAP[cmd]
    session.update(event.peer_id, building_type=building)
    data = session.get(event.peer_id)
    if data.get("object_type") == "дом":
        await bot.state_dispenser.set(event.peer_id, CalcStates.ask_outdoor_work)
        await _edit(bot, event.peer_id,
            "Нужны ли дополнительные электромонтажные работы на участке?",
            yes_no_kb,
        )
    else:
        await bot.state_dispenser.set(event.peer_id, CalcStates.enter_area)
        await _edit(bot, event.peer_id, "Укажите площадь объекта (кв.м):\nНапример: 60")


# ── Работы на участке ─────────────────────────────────────────

async def handle_outdoor_yes(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, outdoor_selection=[])
    await bot.state_dispenser.set(event.peer_id, CalcStates.choose_outdoor_types)
    await _edit(bot, event.peer_id,
        "Выберите объекты на участке:\nМожно выбрать несколько, затем нажмите Далее",
        outdoor_kb_multi([]),
    )


async def handle_outdoor_no(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, outdoor_work="Нет")
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_area)
    await _edit(bot, event.peer_id, "Укажите площадь дома (кв.м):\nНапример: 120")


async def handle_outdoor_toggle(bot: Bot, event: MessageEvent, key: str) -> None:
    label = OUTDOOR_KEY_TO_LABEL.get(key, key)
    data = session.get(event.peer_id)
    selected = list(data.get("outdoor_selection", []))
    if label in selected:
        selected.remove(label)
    else:
        selected.append(label)
    session.update(event.peer_id, outdoor_selection=selected)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Выберите объекты на участке:\nМожно выбрать несколько, затем нажмите Далее",
        keyboard=outdoor_kb_multi(selected),
    )


async def handle_outdoor_done(bot: Bot, event: MessageEvent) -> None:
    data = session.get(event.peer_id)
    selected = data.get("outdoor_selection", [])
    if not selected:
        await event.show_snackbar("Выберите хотя бы один вариант")
        return
    session.update(event.peer_id, outdoor_work=", ".join(selected))
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_area)
    await _edit(bot, event.peer_id, "Укажите площадь дома (кв.м):\nНапример: 120")


# ── Площадь ──────────────────────────────────────────────────

async def handle_enter_area(bot: Bot, message: Message) -> None:
    value = validate_positive_number(message.text or "")
    if value is None or value < 5 or value > 2000:
        return
    session.update(message.peer_id, area=value)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_rooms)
    await _edit(bot, message.peer_id, "Сколько комнат?", rooms_kb)


# ── Комнаты ───────────────────────────────────────────────────

_ROOMS_MAP = {"rooms_studio": 0, "rooms_1": 1, "rooms_2": 2, "rooms_3": 3, "rooms_4plus": 4}


async def handle_rooms(bot: Bot, event: MessageEvent, cmd: str) -> None:
    session.update(event.peer_id, rooms=_ROOMS_MAP[cmd], wall_selection=[])
    await bot.state_dispenser.set(event.peer_id, CalcStates.choose_wall_material)
    await _edit(bot, event.peer_id,
        "Материал стен:\nМожно выбрать несколько, затем нажмите Далее",
        wall_kb_multi([]),
    )


# ── Материал стен ─────────────────────────────────────────────

async def handle_wall_toggle(bot: Bot, event: MessageEvent, key: str) -> None:
    label = WALL_KEY_TO_LABEL.get(key, key)
    data = session.get(event.peer_id)
    selected = list(data.get("wall_selection", []))
    if label in selected:
        selected.remove(label)
    else:
        selected.append(label)
    session.update(event.peer_id, wall_selection=selected)
    await bot.api.messages.edit(
        peer_id=event.peer_id,
        conversation_message_id=session.get_last_msg(event.peer_id),
        message="Материал стен:\nМожно выбрать несколько, затем нажмите Далее",
        keyboard=wall_kb_multi(selected),
    )


async def handle_wall_done(bot: Bot, event: MessageEvent) -> None:
    data = session.get(event.peer_id)
    selected = data.get("wall_selection", [])
    if not selected:
        await event.show_snackbar("Выберите хотя бы один вариант")
        return
    session.update(event.peer_id, wall_material=", ".join(selected))
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_sockets)
    await _edit(bot, event.peer_id,
        "Количество розеток (всего по объекту):\n"
        "Включая двойные — считайте каждое гнездо отдельно",
    )


# ── Числовые вопросы ──────────────────────────────────────────

async def _ask_int(bot: Bot, message: Message, key: str, next_state, next_text: str, kb: str = None) -> None:
    value = validate_positive_integer(message.text or "")
    if value is None:
        return
    session.update(message.peer_id, **{key: value})
    await bot.state_dispenser.set(message.peer_id, next_state)
    await _edit(bot, message.peer_id, next_text, kb)


async def handle_enter_sockets(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "sockets", CalcStates.enter_switches,
        "Количество выключателей (одноклавишные + двухклавишные):")


async def handle_enter_switches(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "switches", CalcStates.enter_spots,
        "Количество точечных светильников (споты):\nВстраиваемые в потолок")


async def handle_enter_spots(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "spots", CalcStates.enter_lamps_simple,
        "Количество люстр простых (до 3 рожков, стандартная высота потолков):")


async def handle_enter_lamps_simple(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "lamps_simple", CalcStates.enter_lamps_hard,
        "Количество люстр сложных (4+ рожков, высокие потолки, каскадные):")


async def handle_enter_lamps_hard(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "lamps_hard", CalcStates.enter_stove,
        "Варочная панель — сколько штук? (0 если нет)")


async def handle_enter_stove(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "stove", CalcStates.enter_oven,
        "Духовой шкаф — сколько штук? (0 если нет)")


async def handle_enter_oven(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "oven", CalcStates.enter_ac,
        "Кондиционеры — сколько штук? (0 если нет)")


async def handle_enter_ac(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "ac", CalcStates.enter_floor_heating,
        "Тёплые полы — укажите площадь в кв.м (0 если не нужно):\n"
        "Электрический тёплый пол под плитку или ламинат")


async def handle_enter_floor_heating(bot: Bot, message: Message) -> None:
    value = validate_positive_number(message.text or "")
    if value is None:
        return
    session.update(message.peer_id, floor_heating=value)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_washing_machine)
    await _edit(bot, message.peer_id, "Стиральная машина — сколько штук? (0 если нет)")


async def handle_enter_washing(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "washing_machine", CalcStates.enter_dishwasher,
        "Посудомоечная машина — сколько штук? (0 если нет)")


async def handle_enter_dishwasher(bot: Bot, message: Message) -> None:
    await _ask_int(bot, message, "dishwasher", CalcStates.enter_boiler,
        "Нужно ли подключить бойлер/водонагреватель?", yes_no_kb)


# ── Блок да/нет ──────────────────────────────────────────────

async def handle_boiler(bot: Bot, event: MessageEvent, answer: bool) -> None:
    session.update(event.peer_id, boiler=answer)
    await bot.state_dispenser.set(event.peer_id, CalcStates.ask_shield)
    await _edit(bot, event.peer_id,
        "Нужна ли сборка/монтаж электрощита?\n"
        "Установка или замена распределительного щитка с автоматами", yes_no_kb)


async def handle_shield(bot: Bot, event: MessageEvent, answer: bool) -> None:
    session.update(event.peer_id, shield_needed=answer)
    await bot.state_dispenser.set(event.peer_id, CalcStates.ask_low_voltage)
    await _edit(bot, event.peer_id,
        "Нужна ли слаботочка?\nИнтернет, ТВ, видеонаблюдение", yes_no_kb)


async def handle_low_voltage(bot: Bot, event: MessageEvent, answer: bool) -> None:
    session.update(event.peer_id, low_voltage=answer)
    await bot.state_dispenser.set(event.peer_id, CalcStates.ask_demolition)
    await _edit(bot, event.peer_id, "Есть ли старые линии для демонтажа?", yes_no_kb)


async def handle_demolition_yes(bot: Bot, event: MessageEvent) -> None:
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_demolition_count)
    await _edit(bot, event.peer_id,
        "Сколько точек нужно демонтировать?\n"
        "Примерное количество розеток, выключателей и светильников")


async def handle_demolition_no(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, demolition=0)
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_extra_info)
    await _edit(bot, event.peer_id, EXTRA_INFO_TEXT, skip_extra_kb)


async def handle_enter_demolition_count(bot: Bot, message: Message) -> None:
    value = validate_positive_integer(message.text or "")
    if value is None:
        return
    session.update(message.peer_id, demolition=value)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_extra_info)
    await _edit(bot, message.peer_id, EXTRA_INFO_TEXT, skip_extra_kb)


# ── Доп. сведения ─────────────────────────────────────────────

async def handle_extra_skip(bot: Bot, event: MessageEvent) -> None:
    session.update(event.peer_id, extra_info="")
    await bot.state_dispenser.set(event.peer_id, CalcStates.enter_name)
    await _edit(bot, event.peer_id, "Введите ваше имя:")


async def handle_enter_extra_info(bot: Bot, message: Message) -> None:
    text = sanitize_text(message.text or "", max_length=1000)
    if len(text) < 1:
        return
    session.update(message.peer_id, extra_info=text)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_name)
    await _edit(bot, message.peer_id, "Введите ваше имя:")


# ── Контакты ──────────────────────────────────────────────────

async def handle_enter_name(bot: Bot, message: Message) -> None:
    name = sanitize_text(message.text or "", max_length=100)
    if len(name) < 2:
        return
    session.update(message.peer_id, client_name=name)
    await bot.state_dispenser.set(message.peer_id, CalcStates.enter_phone)
    await _edit(bot, message.peer_id,
        "Ваш номер телефона:\nНапример: 89181234567 или +7 918 123-45-67")


async def handle_enter_phone(bot: Bot, message: Message) -> None:
    phone = validate_phone(message.text or "")
    if phone is None:
        return
    session.update(message.peer_id, client_phone=phone)
    await bot.state_dispenser.set(message.peer_id, CalcStates.choose_contact_method)
    await _edit(bot, message.peer_id, "Удобный способ связи:", contact_kb)


_CONTACT_MAP = {"contact_call": "Звонок", "contact_wa": "WhatsApp", "contact_tg": "Telegram"}


async def handle_contact_method(bot: Bot, event: MessageEvent, cmd: str) -> None:
    session.update(event.peer_id, contact_method=_CONTACT_MAP[cmd])
    from handlers.user.confirm import show_confirmation
    await show_confirmation(bot, event)
