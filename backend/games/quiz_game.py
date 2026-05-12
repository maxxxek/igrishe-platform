"""Квиз"""
from .base_game import BaseGame
import time
import random


class QuizGame(BaseGame):
    type = 'quiz'
    name = '🎯 Квиз-Шоу'
    
    def handle(self, room, action, path):
        player_id = action.get('player_id', '')
        
        if path == '/api/start':
            return self._start(room)
        elif path == '/api/answer':
            return self._answer(room, player_id, action.get('answer', 0))
        elif path == '/api/next':
            return self._next(room)
        elif path == '/api/game/reward':
            return self._reward(room, player_id)
        return None
    
    def _start(self, room):
        if room.questions:
            random.shuffle(room.questions)
        room.state = 'playing'
        room.current_question = 0
        room.question_start_time = time.time()
        return {'ok': True, 'game_type': self.type}
    
    def _answer(self, room, player_id, answer):
        if player_id in room.answers:
            return {'error': 'Уже ответил'}
        
        q_idx = room.current_question
        if 0 <= q_idx < len(room.questions):
            q = room.questions[q_idx]
            correct = answer == q.get('correct', -1)
            if correct:
                room.scores[player_id] = room.scores.get(player_id, 0) + (getattr(room, 'points', 100))
            room.answers[player_id] = answer
            return {
                'correct': correct,
                'score': room.scores[player_id],
                'all_answered': len(room.answers) >= len(room.players)
            }
        return {'error': 'Неверный вопрос'}
    
    def _next(self, room):
        room.current_question += 1
        room.answers = {}
        room.question_start_time = time.time()
        if room.current_question >= len(room.questions):
            room.state = 'finished'
        return {'ok': True}
    
    def _reward(self, room, player_id):
        scores = room.scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        position = next((i+1 for i, (pid, _) in enumerate(sorted_scores) if pid == player_id), len(sorted_scores))
        score = scores.get(player_id, 0)
        coins = 10 + min(score // 10, 40) + (50 if position == 1 else 30 if position == 2 else 15 if position == 3 else 0)
        return {'coins_earned': coins, 'position': position, 'score': score}