"""Хранилище комнат в памяти (для разработки)"""
import time
from utils.helpers import generate_unique_code


class MemoryStorage:
    def __init__(self):
        self.rooms = {}
    
    def create(self, room):
        """Создаёт комнату"""
        code = generate_unique_code(self.rooms.keys())
        room.code = code
        self.rooms[code] = room
        return room
    
    def get(self, code):
        """Получает комнату по коду"""
        return self.rooms.get(code.upper() if code else None)
    
    def delete(self, code):
        """Удаляет комнату"""
        if code in self.rooms:
            del self.rooms[code]
    
    def count(self):
        """Количество активных комнат"""
        return len(self.rooms)
    
    def cleanup(self, max_age_hours=2):
        """Удаляет старые комнаты"""
        now = time.time()
        expired = [
            code for code, room in self.rooms.items()
            if now - room.created_at > max_age_hours * 3600
        ]
        for code in expired:
            del self.rooms[code]
        return len(expired)