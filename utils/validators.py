"""Валидация пользовательского ввода."""

import re


def validate_positive_number(text: str) -> float | None:
    text = text.strip().replace(",", ".")
    try:
        value = float(text)
        return value if value >= 0 else None
    except ValueError:
        return None


def validate_positive_integer(text: str) -> int | None:
    value = validate_positive_number(text)
    return int(value) if value is not None else None


def validate_phone(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    else:
        return None
    if not digits.startswith("7"):
        return None
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def sanitize_text(text: str, max_length: int = 200) -> str:
    text = text.strip()
    text = re.sub(r"[<>\"']", "", text)
    return text[:max_length]
