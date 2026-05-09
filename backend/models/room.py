"""Модель игровой комнаты"""
import random
import time
from ..config import MAX_PLAYERS
from ..utils.helpers import get_timestamp


class Room:
    def __init__(self, code, game_config):
        self.code = code
        self.game_id = game_config.get('id', 'quiz')
        self.game_name = game_config.get('name', 'Игра')
        self.game_color = game_config.get('color', '#7c3aed')
        self.game_icon = game_config.get('icon', '🎮')
        self.game_icon_image = game_config.get('icon_image', '')
        self.tier = game_config.get('tier', 'free')
        self.type = game_config.get('type', 'quiz')
        
        # Игроки
        self.players = {}
        self.scores = {}
        self.player_order = []
        self.current_player_index = 0
        
        # Состояние
        self.state = 'lobby'
        self.current_question = -1
        self.answers = {}
        self.votes = {}
        self.round = 0
        self.total_rounds = game_config.get('rounds', 5)
        self.points = game_config.get('points_per_question', 100)
        
        # Вопросы
        self.questions = []
        self.truth_pool = game_config.get('truth_pool', [])
        self.dare_pool = game_config.get('dare_pool', [])
        self.player_themes = {}
        
        # Время
        self.question_start_time = 0
        self.created_at = get_timestamp()
        
        # Задание
        self.show_task = False
        self.current_task = ''
        self.task_type = ''
        self.vote_result = ''
        
        # Загружаем вопросы для квиза
        if self.type == 'quiz' and game_config.get('questions'):
            self.questions = random.sample(
                game_config['questions'],
                len(game_config['questions'])
            )
    
    def add_player(self, player_id, name):
        """Добавляет игрока"""
        if len(self.players) >= MAX_PLAYERS:
            return False
        self.players[player_id] = {'name': name}
        self.scores[player_id] = 0
        return True
    
    def remove_player(self, player_id):
        """Удаляет игрока"""
        if player_id in self.players:
            del self.players[player_id]
            if player_id in self.scores:
                del self.scores[player_id]
    
    def player_count(self):
        return len(self.players)
    
    def start_game(self):
        """Запускает игру"""
        if self.type == 'quiz':
            self.state = 'playing'
            self.current_question = 0
            self.question_start_time = get_timestamp()
        elif self.type == 'truth_dare':
            self.player_order = list(self.players.keys())
            random.shuffle(self.player_order)
            self.current_player_index = 0
            self.round = 0
            self.state = 'voting'
            self.votes = {}
        return True
    
    def next_question(self):
        """Переходит к следующему вопросу"""
        self.current_question += 1
        self.answers = {}
        self.question_start_time = get_timestamp()
        if self.current_question >= len(self.questions):
            self.state = 'finished'
    
    def submit_answer(self, player_id, answer):
        """Отправка ответа"""
        if player_id in self.answers:
            return {'error': 'Уже ответил'}
        
        if self.type == 'quiz':
            q_idx = self.current_question
            if 0 <= q_idx < len(self.questions):
                is_correct = answer == self.questions[q_idx].get('correct', -1)
                if is_correct:
                    self.scores[player_id] += self.points
                self.answers[player_id] = answer
                return {
                    'correct': is_correct,
                    'score': self.scores[player_id],
                    'all_answered': len(self.answers) >= len(self.players)
                }
        
        return {'error': 'Неверный вопрос'}
    
    def get_question_time_left(self):
        """Оставшееся время вопроса"""
        if not self.question_start_time or self.current_question < 0:
            return 0
        if self.current_question >= len(self.questions):
            return 0
        elapsed = time.time() - self.question_start_time
        total = self.questions[self.current_question].get('time', 30)
        return max(0, int(total - elapsed))
    
    def to_dict(self):
        """Сериализация для API"""
        data = {
            'code': self.code,
            'game_id': self.game_id,
            'game_name': self.game_name,
            'game_color': self.game_color,
            'game_icon': self.game_icon,
            'game_icon_image': self.game_icon_image,
            'game_type': self.type,
            'tier': self.tier,
            'state': self.state,
            'players': self.players,
            'scores': self.scores,
            'round': self.round,
            'total_rounds': self.total_rounds,
            'answers_count': len(self.answers),
            'answered_players': list(self.answers.keys()),
            'votes': self.votes,
            'votes_count': len(self.votes),
            'total_voters': max(0, len(self.players) - 1),
        }
        
        # Текущий вопрос (для квиза)
        if self.type == 'quiz' and 0 <= self.current_question < len(self.questions):
            q = self.questions[self.current_question]
            data['current_question'] = {
                'text': q.get('text', ''),
                'answers': q.get('answers', []),
                'time': q.get('time', 30)
            }
            data['question_index'] = self.current_question
            data['total_questions'] = len(self.questions)
            data['question_time_left'] = self.get_question_time_left()
        
        # Правда/Действие
        if self.type == 'truth_dare':
            if self.player_order and self.current_player_index < len(self.player_order):
                cp_id = self.player_order[self.current_player_index]
                data['current_player_id'] = cp_id
                data['current_player_name'] = self.players.get(cp_id, {}).get('name', '')
            data['vote_result'] = self.vote_result
            data['current_task'] = self.current_task
            data['task_type'] = self.task_type
            data['show_task'] = self.show_task
        
        return data