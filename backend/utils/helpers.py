"""Вспомогательные функции"""
import random
import string
import time


def generate_room_code(length=4):
    """Генерирует код комнаты"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def generate_unique_code(existing_codes, length=4):
    """Генерирует уникальный код"""
    code = generate_room_code(length)
    while code in existing_codes:
        code = generate_room_code(length)
    return code


def get_timestamp():
    """Возвращает текущий timestamp"""
    return time.time()


def safe_int(value, default=0):
    """Безопасное преобразование в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default