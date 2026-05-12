"""Правда или Действие"""
from .base_game import BaseGame
import random


class TruthDareGame(BaseGame):
    type = 'truth_dare'
    name = '🔥 Правда или Действие'
    
    def handle(self, room, action, path):
        player_id = action.get('player_id', '')
        if path == '/api/start':
            return self._start(room)
        elif path == '/api/vote':
            return self._vote(room, player_id, action.get('vote', ''))
        elif path == '/api/task_done':
            return self._task_done(room, player_id)
        elif path == '/api/game/reward':
            return self._reward(room, player_id)

    
    def _start(self, room):
        player_ids = list(room.players.keys())
        random.shuffle(player_ids)
        room.player_order = player_ids
        room.current_player_index = 0
        room.round = 0
        room.state = 'voting'
        room.votes = {}
        room.show_task = False
        return {'ok': True, 'game_type': self.type}
    
    def _vote(self, room, player_id, vote):
        cp_id = room.player_order[room.current_player_index]
        if player_id == cp_id:
            return {'error': 'Ты выбранный игрок'}
        
        room.votes[player_id] = vote
        total_voters = len(room.players) - 1
        
        if len(room.votes) >= total_voters:
            truth_count = sum(1 for v in room.votes.values() if v == 'truth')
            dare_count = sum(1 for v in room.votes.values() if v == 'dare')
            
            truth_pool = room.truth_pool if hasattr(room, 'truth_pool') else ['Расскажи секрет!', 'Твой главный страх?']
            dare_pool = room.dare_pool if hasattr(room, 'dare_pool') else ['Изобрази робота!', 'Станцуй ламбаду!']
            
            if truth_count >= dare_count:
                room.vote_result = 'truth'
                room.current_task = random.choice(truth_pool)
                room.task_type = 'truth'
            else:
                room.vote_result = 'dare'
                room.current_task = random.choice(dare_pool)
                room.task_type = 'dare'
            
            room.show_task = True
            room.state = 'task'
        
        return {'ok': True}
    
    def _task_done(self, room, player_id):
        cp_id = room.player_order[room.current_player_index]
        if player_id != cp_id:
            return {'error': 'Не твой ход'}
        
        room.scores[player_id] = room.scores.get(player_id, 0) + 50
        room.current_player_index += 1
        room.round += 1
        
        total = getattr(room, 'total_rounds', 5)
        if room.round >= total:
            room.state = 'finished'
        else:
            room.state = 'voting'
            room.votes = {}
            room.show_task = False
        
        return {'ok': True}
    
    def _reward(self, room, player_id):
        scores = room.scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        position = next((i+1 for i, (pid, _) in enumerate(sorted_scores) if pid == player_id), len(sorted_scores))
        coins = 10 + (50 if position == 1 else 30 if position == 2 else 15 if position == 3 else 0)
        return {'coins_earned': coins, 'position': position, 'score': scores.get(player_id, 0)}