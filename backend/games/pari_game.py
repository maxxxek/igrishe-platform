"""Кто ближе?"""
from .base_game import BaseGame
from utils.loader import load_pari_questions
import random


class PariGame(BaseGame):
    type = 'kto_blizhe'
    name = '🎯 Кто ближе?'
    
    def init_room(self, room):
        """Инициализация комнаты при создании"""
        all_questions = load_pari_questions()
        count = min(3, len(all_questions))
        room.pari_questions = random.sample(all_questions, count) if all_questions else []
        room.pari_question_index = 0
        room.pari_phase = 'intro'
        room.pari_answers = {}  # Ответы игроков (их версии числа)
        room.pari_bets = {}     # Ставки игроков {player_id: amount}
        room.pari_bet_targets = {}  # На какой ответ поставил {player_id: target_player_id}
        room.pari_ready = set()  # Игроки, которые прочитали правила
        for p in room.players.values():
            p['ready'] = False
    
    def _go_to_answer(self, room):
        """ТВ нажал «К ответам» - игроки пишут свои варианты"""
        room.pari_phase = 'answer'
        room.pari_answers = {}
        return {'ok': True}

    def _go_to_show_answers(self, room):
        """ТВ нажал показать ответы - показываем шкалу с вариантами игроков"""
        room.pari_phase = 'show_answers'
        return {'ok': True}

    def _go_to_bet(self, room):
        """ТВ нажал «К ставкам» - игроки выбирают на что ставить"""
        room.pari_phase = 'bet'
        room.pari_bets = {}
        room.pari_bet_targets = {}
        return {'ok': True}

    def _go_to_result(self, room):
        """ТВ вскрывает правильный ответ"""
        room.pari_phase = 'result'
        return {'ok': True}

    def _check_all_answers(self, room):
        """Проверяет, все ли игроки дали ответы"""
        answers = getattr(room, 'pari_answers', {})
        return len(answers) == len(room.players) and len(room.players) > 0

    def _check_all_bets(self, room):
        """Проверяет, все ли игроки сделали ставки"""
        bets = getattr(room, 'pari_bets', {})
        return len(bets) == len(room.players) and len(room.players) > 0

    def get_state(self, room):
        """Дополнительные поля для /api/state"""
        data = {
            'pari_phase': getattr(room, 'pari_phase', 'intro'),
            'pari_answers': getattr(room, 'pari_answers', {}),
            'pari_bets': getattr(room, 'pari_bets', {}),
            'pari_bet_targets': getattr(room, 'pari_bet_targets', {}),
            'pari_ready': list(getattr(room, 'pari_ready', set())),
            'all_answers_done': self._check_all_answers(room),
            'all_bets_done': self._check_all_bets(room),
        }
        qs = getattr(room, 'pari_questions', [])
        idx = getattr(room, 'pari_question_index', 0)
        if qs and idx < len(qs):
            q = qs[idx]
            data['pari_question'] = {
                'question': q['question'],
                'answer': q['answer'],  # Правильный ответ (секретный пока)
                'unit': q.get('unit', ''),
                'round': idx + 1,
                'total': len(qs)
            }
        return data
    
    def reset_room(self, room):
        """Сброс комнаты"""
        all_questions = load_pari_questions()
        count = min(7, len(all_questions))
        room.pari_questions = random.sample(all_questions, count) if all_questions else []
        room.pari_phase = 'intro'
        room.pari_answers = {}
        room.pari_bets = {}
        room.pari_bet_targets = {}
        room.pari_ready = set()
        room.pari_question_index = 0
        for p in room.players.values():
            p['ready'] = False
    
    def handle(self, room, action, path):
        """Обрабатывает ВСЕ запросы к игре"""
        player_id = action.get('player_id', '')
        
        # POST запросы
        if path == '/api/start':
            return self._start(room)
        elif path == '/api/pari/ready':
            return self._ready(room, player_id)
        elif path == '/api/pari/answer':
            return self._answer(room, player_id, action.get('answer', 0))
        elif path == '/api/pari/bet':
            return self._bet(room, player_id, action.get('bet', 100), action.get('target', ''))
        elif path == '/api/pari/next':
            return self._next(room)
        elif path == '/api/game/reward':
            return self._reward(room, player_id)
        elif path == '/api/pari/go-answer':
            return self._go_to_answer(room)
        elif path == '/api/pari/go-show-answers':
            return self._go_to_show_answers(room)
        elif path == '/api/pari/go-bet':
            return self._go_to_bet(room)
        elif path == '/api/pari/go-result':
            return self._go_to_result(room)
        
        return None
    
    def _start(self, room):
            """Начинает игру - показывает правила"""
            room.pari_phase = 'intro'  # 🔥 Было 'question', теперь 'intro'
            room.state = 'playing'     # 🔥 Меняем на playing
            room.pari_answers = {}
            room.pari_bets = {}
            room.pari_bet_targets = {}
            room.pari_ready = set()
            for p in room.players.values():
                p['ready'] = False
            return {'ok': True, 'game_type': self.type}
    
    def _ready(self, room, player_id):
        """Игрок прочитал правила"""
        if player_id in room.players:
            if not hasattr(room, 'pari_ready'):
                room.pari_ready = set()
            room.pari_ready.add(player_id)
            room.players[player_id]['ready'] = True

            all_ready = len(room.pari_ready) == len(room.players)
            return {'ok': True, 'all_ready': all_ready}
        return {'ok': False, 'error': 'Игрок не найден'}
    
    def _answer(self, room, player_id, answer):
        """Игрок даёт свой вариант числа"""
        if not hasattr(room, 'pari_answers'):
            room.pari_answers = {}
        room.pari_answers[player_id] = answer
        
        all_done = self._check_all_answers(room)
        return {'ok': True, 'all_answers_done': all_done}
    
    def _bet(self, room, player_id, bet, target):
        """Игрок делает ставку на чей-то ответ"""
        if not hasattr(room, 'pari_bets'):
            room.pari_bets = {}
        if not hasattr(room, 'pari_bet_targets'):
            room.pari_bet_targets = {}
        
        room.pari_bets[player_id] = bet
        room.pari_bet_targets[player_id] = target  # На какой ответ поставил
        
        all_done = self._check_all_bets(room)
        return {'ok': True, 'all_bets_done': all_done}
    
    def _next(self, room):
        """Следующий раунд"""
        room.pari_question_index = getattr(room, 'pari_question_index', 0) + 1
        room.pari_answers = {}
        room.pari_bets = {}
        room.pari_bet_targets = {}
        room.pari_ready = set()
        room.pari_phase = 'question'
        for p in room.players.values():
            p['ready'] = False
        
        qs = getattr(room, 'pari_questions', [])
        idx = room.pari_question_index
        if idx >= len(qs):
            room.state = 'finished'
            return {'ok': True, 'finished': True}
        
        return {'ok': True, 'finished': False}
    
    def _reward(self, room, player_id):
        """Начисление монет после игры"""
        scores = getattr(room, 'scores', {})
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            position = next((i+1 for i, (pid, _) in enumerate(sorted_scores) if pid == player_id), 1)
        else:
            position = 1
        coins = 10 + (50 if position == 1 else 30 if position == 2 else 15 if position == 3 else 0)
        return {'coins_earned': coins, 'position': position}
    
    def get_question(self, room):
        """Возвращает текущий вопрос"""
        qs = getattr(room, 'pari_questions', [])
        idx = getattr(room, 'pari_question_index', 0)
        if idx < len(qs):
            q = qs[idx]
            return {
                'question': q['question'],
                'unit': q.get('unit', ''),
                'round': idx + 1,
                'total': len(qs)
            }
        return {'error': 'Вопросы кончились'}
    
    def get_results(self, room):
        """Возвращает результаты раунда"""
        qs = getattr(room, 'pari_questions', [])
        idx = getattr(room, 'pari_question_index', 0)
        correct = qs[idx]['answer'] if idx < len(qs) else 0
        
        # Собираем ответы игроков
        answers_list = []
        for pid, ans in getattr(room, 'pari_answers', {}).items():
            if pid in room.players:
                answers_list.append({
                    'player_id': pid,
                    'name': room.players[pid].get('name', '?'),
                    'answer': ans,
                    'diff': abs(ans - correct)
                })
        
        # Сортируем по близости к правильному ответу
        answers_list.sort(key=lambda x: x['diff'])
        
        # Определяем победителя - тот, кто поставил на самый близкий ответ
        bet_targets = getattr(room, 'pari_bet_targets', {})
        bets = getattr(room, 'pari_bets', {})
        
        winners = []
        if answers_list and bet_targets:
            # Находим самый близкий ответ
            closest_player_id = answers_list[0]['player_id']
            
            # Кто поставил на этот ответ - те выиграли
            for pid, target in bet_targets.items():
                if target == closest_player_id:
                    winners.append({
                        'player_id': pid,
                        'name': room.players.get(pid, {}).get('name', '?'),
                        'bet': bets.get(pid, 0)
                    })
        
        pot = sum(bets.values())
        win_amount = pot // len(winners) if winners else 0
        
        return {
            'correct_answer': correct,
            'unit': qs[idx].get('unit', '') if idx < len(qs) else '',
            'answers': answers_list,
            'winners': winners,
            'closest_player': answers_list[0] if answers_list else None,
            'pot': pot,
            'win_amount': win_amount
        }