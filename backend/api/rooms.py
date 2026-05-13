"""API для работы с комнатами (облегчённый)"""
import json
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.memory import MemoryStorage
from models.room import Room
from utils.loader import load_games

games = load_games()
storage = MemoryStorage()


def handle_create(game_id='quiz'):
    if game_id not in games:
        return {'error': 'Игра не найдена'}, 400
    
    game = games[game_id]
    room = Room(code='', game_config=game)
    storage.create(room)
    
    # Для игр-плагинов — инициализация через GAMES
    from games import GAMES
    game_plugin = GAMES.get(game.get('type'))
    if game_plugin and hasattr(game_plugin, 'init_room'):
        game_plugin.init_room(room)
    
    print(f'✅ Комната {room.code} — {game["name"]}')
    
    return {
        'code': room.code,
        'game': {
            'name': game['name'],
            'color': game['color'],
            'icon': game.get('icon', '🎮'),
            'icon_image': game.get('icon_image', ''),
            'type': game.get('type', 'quiz')
        }
    }, 200


def handle_join(code, name, avatar_url=''):
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    if room.state != 'lobby':
        return {'error': 'Игра уже началась'}, 400
    
    player_id = str(random.randint(10000, 99999))
    
    if not room.add_player(player_id, name):
        return {'error': 'Комната заполнена'}, 400
    
    if avatar_url:
        room.players[player_id]['avatar_url'] = avatar_url
    
    room.players[player_id]['ready'] = False
    
    print(f'👤 {name} → {code}')
    return {
        'player_id': player_id,
        'name': name,
        'game_type': room.type
    }, 200


def handle_state(code):
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    data = room.to_dict()
    
    # 🔥 Добавляем баланс игроков из БД
    from storage.database import get_user_by_id
    for pid in data.get('players', {}):
        try:
            user = get_user_by_id(int(pid))
            if user:
                data['players'][pid]['coins'] = user.get('coins', 0)
            else:
                data['players'][pid]['coins'] = 0
        except:
            data['players'][pid]['coins'] = 0
    
    from games import GAMES
    game = GAMES.get(room.type)
    if game and hasattr(game, 'get_state'):
        extra = game.get_state(room)
        if extra:
            data.update(extra)
    
    return data, 200


def handle_reset(code):
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    room.state = 'lobby'
    room.current_question = -1
    room.answers = {}
    room.votes = {}
    room.scores = {pid: 0 for pid in room.players}
    room.question_start_time = 0
    room.round = 0
    room.current_player_index = 0
    room.show_task = False
    
    # Сброс через игру-плагин
    from games import GAMES
    game = GAMES.get(room.type)
    if game and hasattr(game, 'reset_room'):
        game.reset_room(room)
    
    print(f'🔄 Комната {code} сброшена')
    return {'ok': True}, 200


def handle_games_list():
    from utils.loader import load_games, get_games_list
    all_games = load_games()
    return get_games_list(all_games), 200