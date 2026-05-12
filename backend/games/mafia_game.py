"""Мафия"""
from .base_game import BaseGame
import random


class MafiaGame(BaseGame):
    type = 'mafia'
    name = '🕵️ Мафия'
    
    # Конфигурация ролей по количеству игроков
    ROLE_CONFIG = {
        5:  {'mafia': 1, 'sheriff': 1, 'doctor': 0, 'civilian': 3},
        6:  {'mafia': 1, 'sheriff': 1, 'doctor': 1, 'civilian': 3},
        7:  {'mafia': 2, 'sheriff': 1, 'doctor': 1, 'civilian': 3},
        8:  {'mafia': 2, 'sheriff': 1, 'doctor': 1, 'civilian': 4},
        9:  {'mafia': 2, 'sheriff': 1, 'doctor': 1, 'civilian': 5},
        10: {'mafia': 3, 'sheriff': 1, 'doctor': 1, 'civilian': 5},
        11: {'mafia': 3, 'sheriff': 1, 'doctor': 1, 'civilian': 6},
        12: {'mafia': 3, 'sheriff': 1, 'doctor': 1, 'civilian': 7},
    }
    
    ROLE_INFO = {
        'mafia':    {'icon': '🔫', 'name': 'Мафия', 'desc': 'Просыпается ночью и выбирает жертву'},
        'sheriff':  {'icon': '⭐', 'name': 'Шериф', 'desc': 'Проверяет одного игрока каждую ночь'},
        'doctor':   {'icon': '💊', 'name': 'Доктор', 'desc': 'Лечит одного игрока каждую ночь'},
        'civilian': {'icon': '👤', 'name': 'Мирный', 'desc': 'Голосует днём против мафии'},
    }
    
    def handle(self, room, action, path):
        player_id = action.get('player_id', '')
        
        if path == '/api/start':
            return self._start(room)
        elif path == '/api/mafia/role':
            return self._get_role(room, player_id)
        elif path == '/api/mafia/host/action':
            return self._host_action(room, action)
        elif path == '/api/mafia/host/execute':
            return self._execute(room, action.get('target', ''))
        elif path == '/api/mafia/host/end':
            return self._end_game(room, action.get('winner', ''))
        
        return None
    
    def _start(self, room):
        """Распределяет роли"""
        player_count = len(room.players)
        closest = min(self.ROLE_CONFIG.keys(), key=lambda k: abs(k - player_count))
        config = self.ROLE_CONFIG[closest]
        
        # Создаём список ролей
        roles = []
        for role, count in config.items():
            for _ in range(count):
                roles.append(role)
        random.shuffle(roles)
        
        # Назначаем роли игрокам
        room.mafia_roles = {}
        player_ids = list(room.players.keys())
        random.shuffle(player_ids)
        
        for i, pid in enumerate(player_ids):
            if i < len(roles):
                room.mafia_roles[pid] = roles[i]
                room.players[pid]['alive'] = True
        
        room.mafia_phase = 'night'
        room.mafia_kill_target = None
        room.mafia_check_target = None
        room.mafia_heal_target = None
        room.mafia_killed_tonight = None
        room.mafia_votes = {}
        room.state = 'playing'
        
        return {'ok': True, 'game_type': self.type}
    
    def _get_role(self, room, player_id):
        """Возвращает роль игрока"""
        role = room.mafia_roles.get(player_id, 'civilian')
        info = self.ROLE_INFO.get(role, self.ROLE_INFO['civilian'])
        return {
            'role': role,
            'icon': info['icon'],
            'name': info['name'],
            'description': info['desc']
        }
    
    def _host_action(self, room, action):
        """Ведущий выполняет действие"""
        action_type = action.get('action', '')
        target = action.get('target', '')
        
        if action_type == 'kill':
            room.mafia_kill_target = target
        elif action_type == 'check':
            room.mafia_check_target = target
            role = room.mafia_roles.get(target, 'civilian')
            return {'ok': True, 'role': role, 'is_mafia': role == 'mafia'}
        elif action_type == 'heal':
            room.mafia_heal_target = target
        elif action_type == 'next_phase':
            return self._next_phase(room)
        
        return {'ok': True}
    
    def _next_phase(self, room):
        """Переход между фазами"""
        if room.mafia_phase == 'night':
            # Обработка ночи
            killed = room.mafia_kill_target
            healed = room.mafia_heal_target
            
            if killed and killed != healed:
                room.players[killed]['alive'] = False
                room.mafia_killed_tonight = killed
            else:
                room.mafia_killed_tonight = None
            
            room.mafia_phase = 'day'
            room.mafia_kill_target = None
            room.mafia_check_target = None
            room.mafia_heal_target = None
            room.mafia_votes = {}
            
        elif room.mafia_phase == 'day':
            room.mafia_phase = 'voting'
            
        elif room.mafia_phase == 'voting':
            room.mafia_phase = 'night'
            room.mafia_killed_tonight = None
        
        return {
            'ok': True,
            'phase': room.mafia_phase,
            'killed': room.mafia_killed_tonight
        }
    
    def _execute(self, room, target):
        """Казнь игрока"""
        if target and target in room.players:
            room.players[target]['alive'] = False
            room.mafia_killed_tonight = target
        return {'ok': True, 'executed': target}
    
    def _end_game(self, room, winner):
        """Завершение игры"""
        room.state = 'finished'
        room.mafia_winner = winner
        
        # Начисляем очки
        for pid, role in room.mafia_roles.items():
            if (winner == 'mafia' and role == 'mafia') or (winner == 'citizens' and role != 'mafia'):
                room.scores[pid] = room.scores.get(pid, 0) + 100
            else:
                room.scores[pid] = room.scores.get(pid, 0) + 20
        
        return {
            'ok': True,
            'winner': winner,
            'roles': {pid: room.mafia_roles.get(pid, '') for pid in room.players},
            'scores': room.scores
        }
    def init_room(self, room):
        room.mafia_roles = {}
        room.mafia_phase = 'night'
        room.mafia_killed_tonight = None
    
    def get_state(self, room):
        return {
            'mafia_phase': getattr(room, 'mafia_phase', 'night'),
            'mafia_killed_tonight': getattr(room, 'mafia_killed_tonight', None),
            'mafia_winner': getattr(room, 'mafia_winner', None),
        }
    
    def reset_room(self, room):
        room.mafia_roles = {}
        room.mafia_phase = 'night'
        room.mafia_killed_tonight = None
        room.mafia_winner = None