"""
Хранилище пользовательских данных сессии.
Заменяет FSMContext.get_data() / update_data() из aiogram.
Ключ — peer_id пользователя ВКонтакте.
"""


class SessionStorage:
    def __init__(self) -> None:
        self._data: dict[int, dict] = {}

    def get(self, peer_id: int) -> dict:
        """Вернуть весь словарь данных пользователя."""
        return self._data.setdefault(peer_id, {})

    def update(self, peer_id: int, **kwargs) -> None:
        """Обновить/добавить поля в данные пользователя."""
        self._data.setdefault(peer_id, {}).update(kwargs)

    def clear(self, peer_id: int) -> None:
        """Очистить данные пользователя (при старте нового опроса)."""
        self._data.pop(peer_id, None)

    def set_last_msg(self, peer_id: int, cmid: int) -> None:
        """Сохранить conversation_message_id последнего сообщения бота."""
        self.update(peer_id, last_cmid=cmid)

    def get_last_msg(self, peer_id: int) -> int | None:
        """Вернуть conversation_message_id последнего сообщения бота."""
        return self.get(peer_id).get("last_cmid")


# Глобальный экземпляр — импортируется во всех хендлерах
session = SessionStorage()
