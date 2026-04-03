"""Форматирование сообщений для ВК (plain text, без HTML)."""

from database.models import Lead


def yn(value) -> str:
    return "Да" if value else "Нет"


def format_lead_message(lead: Lead) -> str:
    dt = lead.created_at
    date_str = dt.strftime("%d.%m.%Y %H:%M") if dt else "—"
    rooms_str = "Студия" if lead.rooms == 0 else str(lead.rooms)

    lines = [
        f"📋 Новая заявка #{lead.id}",
        "",
        f"📍 Город: {lead.city or '—'}",
        f"🗺 Район/ЖК: {lead.district or '—'}",
        "",
        f"Объект: {lead.object_type} ({lead.building_type})",
        f"Площадь: {lead.area} кв.м",
        f"Комнат: {rooms_str}",
        f"Стены: {lead.wall_material}",
    ]

    if lead.outdoor_work and lead.outdoor_work != "Нет":
        lines.append(f"🌿 Работы на участке: {lead.outdoor_work}")

    lines += [
        "",
        "⚡ Электрические точки:",
        f"  Розетки: {lead.sockets} шт",
        f"  Выключатели: {lead.switches} шт",
        f"  Споты: {lead.spots} шт",
        f"  Люстры простые: {lead.lamps_simple} шт",
        f"  Люстры сложные: {lead.lamps_hard} шт",
        "",
        "🔌 Мощные потребители:",
        f"  Варочная панель: {lead.stove} шт",
        f"  Духовой шкаф: {lead.oven} шт",
        f"  Кондиционеры: {lead.ac} шт",
        f"  Бойлер: {yn(lead.boiler)}",
        f"  Тёплые полы: {lead.floor_heating} кв.м",
        f"  Стиральная машина: {lead.washing_machine} шт",
        f"  Посудомоечная машина: {lead.dishwasher} шт",
        "",
        "🛠 Дополнительно:",
        f"  Сборка щита: {yn(lead.shield_needed)}",
        f"  Слаботочка: {yn(lead.low_voltage)}",
        f"  Демонтаж: {lead.demolition} точек",
    ]

    if lead.extra_info:
        lines += ["", f"💬 Доп. сведения мастеру: {lead.extra_info}"]

    lines += [
        "",
        "💰 Примерная стоимость работ:",
        f"от {lead.price_min:,} до {lead.price_max:,} руб. (без материалов)".replace(",", " "),
        "",
        "👤 Контакты:",
        f"  Имя: {lead.client_name}",
        f"  Телефон: {lead.client_phone}",
        f"  Связь: {lead.contact_method}",
        "",
        f"📅 Дата заявки: {date_str}",
    ]
    return "\n".join(lines)


def format_summary(data: dict, price_min: int, price_max: int) -> str:
    rooms_val = data.get("rooms", "—")
    rooms_str = "Студия" if rooms_val == 0 else str(rooms_val)
    outdoor = data.get("outdoor_work", "")

    lines = [
        "📊 Ваш расчёт готов!",
        "",
        f"📍 {data.get('city', '—')}, {data.get('district', '—')}",
        f"Объект: {data.get('object_type', '—')} ({data.get('building_type', '—')})",
        f"Площадь: {data.get('area', '—')} кв.м, комнат: {rooms_str}",
        f"Стены: {data.get('wall_material', '—')}",
    ]
    if outdoor and outdoor != "Нет":
        lines.append(f"🌿 Участок: {outdoor}")

    lines += [
        "",
        f"Розетки: {data.get('sockets', 0)}, "
        f"Выключатели: {data.get('switches', 0)}, "
        f"Споты: {data.get('spots', 0)}",
        "",
        "💰 Примерная стоимость работ:",
        f"от {price_min:,} до {price_max:,} руб. (без материалов)".replace(",", "\u00a0"),
    ]

    extra = data.get("extra_info", "")
    if extra:
        lines += ["", f"💬 Ваши пожелания: {extra}"]

    lines += [
        "",
        "Точная смета составляется после осмотра объекта или по вашему проекту.",
        "Осмотр бесплатный.",
    ]
    return "\n".join(lines)


def format_all_settings(settings: dict) -> str:
    from config import COEFF_LABELS, PRICE_LABELS
    lines = ["⚙️ Текущие настройки", "", "💰 Цены:"]
    for key, label in PRICE_LABELS.items():
        lines.append(f"  {label}: {settings.get(key, '—')} руб.")
    lines += ["", "📐 Коэффициенты:"]
    for key, label in COEFF_LABELS.items():
        lines.append(f"  {label}: {settings.get(key, '—')}")
    return "\n".join(lines)
