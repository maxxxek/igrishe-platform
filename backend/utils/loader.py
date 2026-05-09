"""Загрузчик игр и вопросов"""
import json
import os
import glob
from ..config import GAMES_DIR, QUESTIONS_DIR


def load_games():
    """Загружает все игры из data/games/"""
    games = {}
    
    for tier in ['free', 'premium']:
        tier_path = os.path.join(GAMES_DIR, tier)
        if os.path.exists(tier_path):
            for filename in os.listdir(tier_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(tier_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            game = json.load(f)
                            game['tier'] = tier
                            game_id = game.get('id')
                            if game_id:
                                games[game_id] = game
                                print(f'   🎮 [{tier}] {game.get("name", filename)}')
                    except Exception as e:
                        print(f'   ❌ Ошибка в {filename}: {e}')
    
    return games


def load_question_bank():
    """Загружает банк вопросов"""
    bank = {'text': {}, 'video': [], 'audio': []}
    
    # Текстовые вопросы
    text_dir = os.path.join(QUESTIONS_DIR, 'text')
    if os.path.exists(text_dir):
        for filename in os.listdir(text_dir):
            if filename.endswith('.txt'):
                category = filename.replace('.txt', '')
                questions = []
                filepath = os.path.join(text_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('#') or not line:
                                continue
                            parts = [p.strip() for p in line.split('|')]
                            if len(parts) >= 6:
                                questions.append({
                                    'type': 'text',
                                    'text': parts[0],
                                    'answers': parts[1:5],
                                    'correct': int(parts[5]),
                                    'time': int(parts[6]) if len(parts) > 6 else 15,
                                    'category': category
                                })
                    bank['text'][category] = questions
                    print(f'   📝 {category}: {len(questions)} вопросов')
                except Exception as e:
                    print(f'   ❌ {filename}: {e}')
    
    return bank


def get_games_list(games):
    """Форматирует список игр для API"""
    return {
        gid: {
            'id': g['id'],
            'name': g['name'],
            'description': g['description'],
            'color': g['color'],
            'icon': g.get('icon', '🎮'),
            'icon_image': g.get('icon_image', ''),
            'tier': g.get('tier', 'free'),
            'category': g.get('category', 'general'),
            'questions_count': len(g.get('questions', []))
        }
        for gid, g in games.items()
    }