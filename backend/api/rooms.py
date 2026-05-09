"""API для работы с комнатами"""
import json
from ..storage.memory import MemoryStorage
from ..models.room import Room
from ..utils.loader import load_games

# Загружаем игры и создаём хранилище
games = load_games()
storage = MemoryStorage()


def handle_create(game_id='quiz'):
    """Создание комнаты"""
    if game_id not in games:
        return {'error': 'Игра не найдена'}, 400
    
    game = games[game_id]
    room = Room(code='', game_config=game)
    storage.create(room)
    
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


def handle_join(code, name):
    """Подключение к комнате"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    if room.state != 'lobby':
        return {'error': 'Игра уже началась'}, 400
    
    import random
    player_id = str(random.randint(10000, 99999))
    
    if not room.add_player(player_id, name):
        return {'error': 'Комната заполнена'}, 400
    
    print(f'👤 {name} → {code}')
    return {'player_id': player_id, 'name': name}, 200


def handle_start(code):
    """Запуск игры"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    if room.player_count() == 0:
        return {'error': 'Нужен хотя бы 1 игрок'}, 400
    
    room.start_game()
    print(f'🚀 Игра в {code} началась!')
    return {'ok': True, 'game_type': room.type}, 200


def handle_state(code):
    """Состояние комнаты"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    return room.to_dict(), 200


def handle_answer(code, player_id, answer):
    """Ответ игрока"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    result = room.submit_answer(player_id, answer)
    if 'error' in result:
        return result, 400
    
    return result, 200


def handle_next(code):
    """Следующий вопрос"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    room.next_question()
    return {'ok': True}, 200


def handle_reset(code):
    """Сброс комнаты"""
    room = storage.get(code)
    if not room:
        return {'error': 'Комната не найдена'}, 404
    
    # Сбрасываем состояние
    game = games.get(room.game_id)
    if game:
        room.state = 'lobby'
        room.current_question = -1
        room.answers = {}
        room.votes = {}
        room.scores = {pid: 0 for pid in room.players}
        room.question_start_time = 0
        room.round = 0
        room.current_player_index = 0
        room.show_task = False
        
        if room.type == 'quiz' and game.get('questions'):
            import random
            room.questions = random.sample(game['questions'], len(game['questions']))
    
    print(f'🔄 Комната {code} сброшена')
    return {'ok': True}, 200


def handle_games_list():
    """Список игр"""
    from ..utils.loader import get_games_list
    return get_games_list(games), 200