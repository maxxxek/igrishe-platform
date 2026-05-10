"""Загрузчик квизов и игр"""
import json
import os
import random
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
QUIZZES_DIR = os.path.join(BASE_DIR, 'data', 'questions')
GAMES_DIR = os.path.join(BASE_DIR, 'data', 'games')


def load_all_quizzes():
    """Загружает ВСЕ квизы из data/questions/ (рекурсивно)"""
    quizzes = {}
    
    if not os.path.exists(QUIZZES_DIR):
        os.makedirs(QUIZZES_DIR)
        return quizzes
    
    # Рекурсивно ищем JSON-файлы
    for root, dirs, files in os.walk(QUIZZES_DIR):
        for filename in files:
            if filename.endswith('.json') and filename != 'categories.json':
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        quiz = json.load(f)
                        quiz_id = quiz.get('id')
                        if quiz_id and 'questions' in quiz:
                            quizzes[quiz_id] = quiz
                            q_count = len(quiz.get('questions', []))
                            print(f'   ✅ {quiz.get("name", filename)} ({q_count} вопросов)')
                except Exception as e:
                    print(f'   ❌ {filename}: {e}')
    
    return quizzes


def load_games():
    """Загружает ВСЕ игры: механики + квизы"""
    games = {}
    
    # 1. Загружаем механики из data/games/
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
                        print(f'   ❌ {filename}: {e}')
    
    # 2. Загружаем квизы из data/questions/ (рекурсивно)
    quizzes = load_all_quizzes()
    for qid, quiz in quizzes.items():
        games[qid] = {
            'id': qid,
            'name': quiz.get('name', qid),
            'description': quiz.get('description', ''),
            'color': quiz.get('color', '#7c3aed'),
            'icon': quiz.get('icon', '🎮'),
            'icon_image': quiz.get('icon_image', ''),
            'type': 'quiz',
            'tier': quiz.get('tier', 'free'),
            'category': quiz.get('category', 'quiz'),
            'subcategory': quiz.get('subcategory', 'random'),
            'questions_count': len(quiz.get('questions', [])),
            'questions': quiz.get('questions', [])
        }
    
    print(f'📦 Всего загружено игр: {len(games)}')
    return games


def load_pari_questions():
    """Загружает все вопросы для «Кто ближе?»"""
    questions = []
    pari_dir = os.path.join(QUIZZES_DIR, 'table', 'pari')
    
    if os.path.exists(pari_dir):
        for filename in os.listdir(pari_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(pari_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for q in data.get('questions', []):
                            q['source'] = filename.replace('.json', '')
                            questions.append(q)
                except:
                    pass
    
    random.shuffle(questions)
    return questions


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
            'category': g.get('category', 'quiz'),
            'subcategory': g.get('subcategory', 'random'),
            'questions_count': len(g.get('questions', [])) if g.get('type') == 'quiz' else g.get('rounds', 5)
        }
        for gid, g in games.items()
    }