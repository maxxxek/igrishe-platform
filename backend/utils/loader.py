"""Загрузчик квизов и игр"""
import json
import os
import random
import glob

QUIZZES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'questions')
GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'games')

def load_pari_questions():
    """Загружает все вопросы для «Кто ближе?»"""
    questions = []
    pari_dir = os.path.join(QUESTIONS_DIR, 'table', 'pari')
    
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
    
    # Перемешиваем
    random.shuffle(questions)
    return questions

def load_all_quizzes():
    """Загружает ВСЕ квизы из папки data/questions/"""
    quizzes = {}
    
    if not os.path.exists(QUIZZES_DIR):
        os.makedirs(QUIZZES_DIR)
        print(f'📁 Создана папка: {QUIZZES_DIR}')
        return quizzes
    
    # Загружаем JSON-квизы
    for filepath in glob.glob(os.path.join(QUIZZES_DIR, '*.json')):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                quiz = json.load(f)
                quiz_id = quiz.get('id')
                if quiz_id:
                    quizzes[quiz_id] = quiz
                    q_count = len(quiz.get('questions', []))
                    print(f'   ✅ {quiz.get("name", os.path.basename(filepath))} ({q_count} вопросов)')
        except Exception as e:
            print(f'   ❌ Ошибка в {os.path.basename(filepath)}: {e}')
    
    # Загружаем TXT-квизы
    for filepath in glob.glob(os.path.join(QUIZZES_DIR, '*.txt')):
        try:
            quiz = _parse_txt_quiz(filepath)
            if quiz:
                quizzes[quiz['id']] = quiz
                print(f'   ✅ {quiz.get("name")} ({len(quiz.get("questions", []))} вопросов)')
        except Exception as e:
            print(f'   ❌ Ошибка в {os.path.basename(filepath)}: {e}')
    
    return quizzes


def _parse_txt_quiz(filepath):
    """Парсит TXT-файл в структуру квиза"""
    category = os.path.basename(filepath).replace('.txt', '')
    
    questions = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    name = category.replace('_', ' ').title()
    description = ''
    
    for line in lines:
        line = line.strip()
        
        # Заголовок
        if line.startswith('# NAME:'):
            name = line.replace('# NAME:', '').strip()
            continue
        if line.startswith('# DESC:'):
            description = line.replace('# DESC:', '').strip()
            continue
        
        # Пропускаем комментарии и пустые строки
        if line.startswith('#') or not line:
            continue
        
        # Парсим вопрос
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 6:
            q = {
                'type': 'text',
                'question': parts[0],
                'answers': [p.strip() for p in parts[1:5]],
                'correct': int(parts[5]),
                'time': int(parts[6]) if len(parts) > 6 else 15
            }
            # Если есть картинка
            if len(parts) > 7 and parts[7]:
                q['type'] = 'image'
                q['image'] = parts[7]
            questions.append(q)
    
    return {
        'id': category,
        'name': f'📝 {name}',
        'description': description or f'Текстовый квиз: {name}',
        'category': 'quiz',
        'subcategory': 'themed',
        'tier': 'free',
        'color': '#7c3aed',
        'icon': '📝',
        'questions': questions
    }


def load_games():
    """Загружает игры-механики из data/games/"""
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
                    except Exception as e:
                        print(f'   ❌ {filename}: {e}')
    
    # Добавляем все квизы как игры
    quizzes = load_all_quizzes()
    for qid, quiz in quizzes.items():
        games[qid] = {
            'id': qid,
            'name': quiz['name'],
            'description': quiz.get('description', ''),
            'color': quiz.get('color', '#7c3aed'),
            'icon': quiz.get('icon', '🎮'),
            'icon_image': quiz.get('icon_image', ''),
            'type': 'quiz',
            'tier': quiz.get('tier', 'free'),
            'category': quiz.get('category', 'quiz'),
            'subcategory': quiz.get('subcategory', 'random'),
            'points_per_question': quiz.get('points_per_question', 100),
            'questions': quiz.get('questions', [])
        }
    
    return games


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
            'questions_count': len(g.get('questions', []))
        }
        for gid, g in games.items()
    }