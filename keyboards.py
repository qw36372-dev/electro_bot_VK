"""
Клавиатуры для ВК-бота (vkbottle).
Используются Callback-кнопки (inline) — аналог Telegram inline keyboard.
"""

import json
from vkbottle import Keyboard, KeyboardButtonColor, Callback, Text


def _kb(buttons: list[list[tuple[str, dict]]], inline: bool = True) -> str:
    """
    Вспомогательная функция.
    buttons — список строк, каждая строка — список (label, payload).
    Возвращает JSON-строку клавиатуры.
    """
    kb = Keyboard(inline=inline)
    for i, row in enumerate(buttons):
        for label, payload in row:
            kb.add(Callback(label, payload))
        if i < len(buttons) - 1:
            kb.row()
    return kb.get_json()


# ── Главное меню ─────────────────────────────────────────────
start_kb = _kb([[("🔧 Рассчитать стоимость работ", {"cmd": "calc_start"})]])

# ── Тип объекта ──────────────────────────────────────────────
object_type_kb = _kb([[
    ("🏢 Квартира", {"cmd": "obj_flat"}),
    ("🏠 Частный дом", {"cmd": "obj_house"}),
]])

# ── Тип жилья ────────────────────────────────────────────────
building_type_flat_kb = _kb([[
    ("🆕 Новостройка", {"cmd": "bt_new"}),
    ("🏚 Вторичка", {"cmd": "bt_old"}),
]])

building_type_house_kb = _kb([[
    ("1️⃣ 1 этаж", {"cmd": "bt_1floor"}),
    ("2️⃣ 2+ этажа", {"cmd": "bt_2floor"}),
]])

# ── Количество комнат ─────────────────────────────────────────
rooms_kb = _kb([
    [("Студия", {"cmd": "rooms_studio"}), ("1", {"cmd": "rooms_1"}), ("2", {"cmd": "rooms_2"})],
    [("3", {"cmd": "rooms_3"}), ("4+", {"cmd": "rooms_4plus"})],
])

# ── Да / Нет ─────────────────────────────────────────────────
yes_no_kb = _kb([[
    ("✅ Да", {"cmd": "yn_yes"}),
    ("❌ Нет", {"cmd": "yn_no"}),
]])

# ── Способ связи ─────────────────────────────────────────────
contact_kb = _kb([[
    ("📞 Звонок", {"cmd": "contact_call"}),
    ("💬 WhatsApp", {"cmd": "contact_wa"}),
    ("✈️ Telegram", {"cmd": "contact_tg"}),
]])

# ── Пропуск доп. сведений ─────────────────────────────────────
skip_extra_kb = _kb([[("❌ Нет", {"cmd": "extra_skip"})]])

# ── Подтверждение заявки ─────────────────────────────────────
confirm_kb = _kb([
    [("📨 Отправить заявку мастеру", {"cmd": "submit_lead"})],
    [("✏️ Изменить данные", {"cmd": "edit_data"}), ("❌ Отменить", {"cmd": "cancel_lead"})],
])

# ── Материал стен (множественный выбор) ──────────────────────
WALL_OPTIONS = [
    ("wall_concrete", "🧱 Бетон"),
    ("wall_brick",    "🏗 Кирпич"),
    ("wall_gas",      "🪨 Газоблок/пеноблок"),
    ("wall_wood",     "🪵 Дерево"),
    ("wall_other",    "❓ Другое"),
]

WALL_KEY_TO_LABEL = {k: v.split(" ", 1)[1] for k, v in WALL_OPTIONS}


def wall_kb_multi(selected: list) -> str:
    rows = []
    for key, label in WALL_OPTIONS:
        clean = label.split(" ", 1)[1]
        prefix = "✅ " if clean in selected else ""
        rows.append([(f"{prefix}{label}", {"cmd": f"wall_toggle_{key}"})])
    rows.append([("➡️ Далее", {"cmd": "wall_done"})])
    return _kb(rows)


# ── Работы на участке (множественный выбор) ──────────────────
OUTDOOR_OPTIONS = [
    ("outdoor_garage",    "🚗 Гараж"),
    ("outdoor_outbuilds", "🏚 Хозпостройки"),
    ("outdoor_landscape", "🌳 Ландшафтные работы"),
]

OUTDOOR_KEY_TO_LABEL = {k: v.split(" ", 1)[1] for k, v in OUTDOOR_OPTIONS}


def outdoor_kb_multi(selected: list) -> str:
    rows = []
    for key, label in OUTDOOR_OPTIONS:
        clean = label.split(" ", 1)[1]
        prefix = "✅ " if clean in selected else ""
        rows.append([(f"{prefix}{label}", {"cmd": f"outdoor_toggle_{key}"})])
    rows.append([("➡️ Далее", {"cmd": "outdoor_done"})])
    return _kb(rows)


# ── Административная панель ───────────────────────────────────
admin_menu_kb = _kb([
    [("💰 Управление ценами", {"cmd": "adm_prices"})],
    [("📐 Коэффициенты", {"cmd": "adm_coeffs"})],
    [("👁 Просмотр настроек", {"cmd": "adm_view"})],
    [("📊 Статистика заявок", {"cmd": "adm_stats"})],
])

back_kb = _kb([[("⬅️ Назад", {"cmd": "adm_back"})]])


def prices_kb(settings: dict) -> str:
    from config import PRICE_LABELS
    rows = []
    for key, label in PRICE_LABELS.items():
        val = int(settings.get(key, 0))
        rows.append([(f"{label} ({val} руб.)", {"cmd": f"edit_price_{key}"})])
    rows.append([("⬅️ Назад", {"cmd": "adm_back"})])
    return _kb(rows)


def coeffs_kb(settings: dict) -> str:
    from config import COEFF_LABELS
    rows = []
    for key, label in COEFF_LABELS.items():
        val = settings.get(key, 0)
        rows.append([(f"{label} ({val})", {"cmd": f"edit_coeff_{key}"})])
    rows.append([("⬅️ Назад", {"cmd": "adm_back"})])
    return _kb(rows)
