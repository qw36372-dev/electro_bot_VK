"""FSM-состояния для ВК-бота (vkbottle BaseStateGroup)."""

from enum import auto
from vkbottle import BaseStateGroup


class CalcStates(BaseStateGroup):
    # Геолокация
    enter_city = auto()
    enter_district = auto()

    # Тип объекта
    choose_object_type = auto()
    choose_building_type = auto()

    # Доп. работы на участке
    ask_outdoor_work = auto()
    choose_outdoor_types = auto()

    # Общие параметры
    enter_area = auto()
    enter_rooms = auto()
    choose_wall_material = auto()

    # Электрические точки
    enter_sockets = auto()
    enter_switches = auto()
    enter_spots = auto()
    enter_lamps_simple = auto()
    enter_lamps_hard = auto()

    # Дополнительные потребители
    enter_stove = auto()
    enter_oven = auto()
    enter_ac = auto()
    enter_floor_heating = auto()
    enter_washing_machine = auto()
    enter_dishwasher = auto()

    # Блок да/нет
    enter_boiler = auto()
    ask_shield = auto()
    ask_low_voltage = auto()
    ask_demolition = auto()
    enter_demolition_count = auto()

    # Доп. сведения
    enter_extra_info = auto()

    # Контакты
    enter_name = auto()
    enter_phone = auto()
    choose_contact_method = auto()

    # Подтверждение
    confirm = auto()


class AdminStates(BaseStateGroup):
    choose_price_item = auto()
    enter_new_price = auto()
    choose_coeff_item = auto()
    enter_new_coeff = auto()
