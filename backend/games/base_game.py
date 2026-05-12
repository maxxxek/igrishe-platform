"""Базовый класс для всех игр"""

class BaseGame:
    type = 'base'
    name = 'Базовая игра'
    
    def handle(self, room, action, path):
        """Обрабатывает действие. Переопредели в дочернем классе."""
        return None
    
    def get_pages(self):
        """Возвращает страницы для игры"""
        return {'tv': f'tv_{self.type}.html', 'player': f'player_{self.type}.html'}
    
    def init_room(self, room):
        """Инициализация комнаты при создании"""
        pass
    
    def get_state(self, room):
        """Дополнительные поля для /api/state"""
        return {}
    
    def reset_room(self, room):
        """Сброс комнаты"""
        pass