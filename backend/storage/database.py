"""База данных SQLite"""
import sqlite3
import os
import bcrypt
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'igrishe.db')


def get_db():
    """Подключение к базе"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицы если их нет"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_url TEXT DEFAULT '',
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ База данных готова')


def register_user(username, email, password):
    """Регистрирует пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существует ли
    cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        conn.close()
        return {'error': 'Пользователь с таким именем или email уже существует'}
    
    # Хэшируем пароль
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Создаём
    cursor.execute(
        'INSERT INTO users (username, email, password_hash, coins) VALUES (?, ?, ?, 100)',
        (username, email, password_hash)
    )
    conn.commit()
    
    user_id = cursor.lastrowid
    conn.close()
    
    return {
        'success': True,
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'level': 1,
            'avatar_url': '',
            'coins': 100
        }
    }


def login_user(login, password):
    """Вход пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Ищем по email ИЛИ имени
    cursor.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?',
        (login, login)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {'error': 'Неверный логин или пароль'}
    
    # Проверяем пароль
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        conn.close()
        return {'error': 'Неверный логин или пароль'}
    
    conn.close()
    
    return {
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'level': user['level'],
            'avatar_url': user['avatar_url'],
            'coins': user['coins']
        }
    }


def get_user_by_id(user_id):
    """Получает пользователя по ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'level': user['level'],
            'avatar_url': user['avatar_url'],
            'coins': user['coins']
        }
    return None


def update_coins(user_id, amount):
    """Обновляет баланс монет"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_coins_after_game(user_id, game_type, score, position):
    """Начисляет монеты после игры"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Базовые монеты за участие
    coins = 10
    
    # Бонус за победу
    if position == 1:
        coins += 50
    elif position == 2:
        coins += 30
    elif position == 3:
        coins += 15
    
    # Бонус за очки
    coins += min(score // 10, 40)  # максимум 40 монет за очки
    
    # Начисляем
    cursor.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (coins, user_id))
    
    # Обновляем игры и ответы
    cursor.execute('''
        UPDATE users SET 
            games_played = games_played + 1,
            correct_answers = correct_answers + ?
        WHERE id = ?
    ''', (score // 10, user_id))
    
    conn.commit()
    
    # Получаем новый баланс
    cursor.execute('SELECT coins, games_played, correct_answers FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'coins_earned': coins,
            'total_coins': result['coins'],
            'games_played': result['games_played'],
            'correct_answers': result['correct_answers']
        }
    return {'coins_earned': coins}


def add_table_columns():
    """Добавляет недостающие колонки в таблицу users"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN games_played INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN correct_answers INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0')
    except:
        pass
    
    conn.commit()
    conn.close()

    
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Пользователи (обновлённая)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_url TEXT DEFAULT '',
            equipped_avatar TEXT DEFAULT '',
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 100,
            games_played INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            premium_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Купленные предметы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_icon TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, item_name)
        )
    ''')
    
    # Достижения
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_name TEXT NOT NULL,
            achievement_icon TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, achievement_name)
        )
    ''')
    
    # История игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            position INTEGER DEFAULT 0,
            coins_earned INTEGER DEFAULT 0,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Настройки пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            sound_enabled INTEGER DEFAULT 1,
            music_enabled INTEGER DEFAULT 1,
            language TEXT DEFAULT 'ru',
            theme TEXT DEFAULT 'light',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ База данных обновлена')



# ========== ПРЕДМЕТЫ ==========

def save_user_items(user_id, owned_items):
    """Сохраняет купленные предметы"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Удаляем старые
    cursor.execute('DELETE FROM user_items WHERE user_id = ?', (user_id,))
    
    # Добавляем новые
    for item in owned_items:
        cursor.execute(
            'INSERT OR IGNORE INTO user_items (user_id, item_icon, item_name, item_type) VALUES (?, ?, ?, ?)',
            (user_id, item.get('icon', ''), item.get('name', ''), item.get('category', ''))
        )
    
    conn.commit()
    conn.close()


def load_user_items(user_id):
    """Загружает купленные предметы"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT item_icon, item_name, item_type FROM user_items WHERE user_id = ?', (user_id,))
    items = [{'icon': row['item_icon'], 'name': row['item_name'], 'category': row['item_type']} for row in cursor.fetchall()]
    conn.close()
    return items


# ========== АВАТАР ==========

def save_equipped_avatar(user_id, avatar):
    """Сохраняет выбранный аватар"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET equipped_avatar = ? WHERE id = ?', (avatar, user_id))
    conn.commit()
    conn.close()


# ========== ИСТОРИЯ ИГР ==========

def save_game_result(user_id, game_type, score, position, coins_earned):
    """Сохраняет результат игры"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO game_history (user_id, game_type, score, position, coins_earned) VALUES (?, ?, ?, ?, ?)',
        (user_id, game_type, score, position, coins_earned)
    )
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Получает статистику игрока"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_games,
            SUM(score) as total_score,
            SUM(coins_earned) as total_coins_earned,
            AVG(position) as avg_position
        FROM game_history 
        WHERE user_id = ?
    ''', (user_id,))
    
    stats = cursor.fetchone()
    conn.close()
    
    if stats and stats['total_games'] > 0:
        return {
            'total_games': stats['total_games'],
            'total_score': stats['total_score'],
            'total_coins_earned': stats['total_coins_earned'],
            'avg_position': round(stats['avg_position'], 1)
        }
    return {'total_games': 0, 'total_score': 0, 'total_coins_earned': 0, 'avg_position': 0}


# ========== НАСТРОЙКИ ==========

def save_user_settings(user_id, settings):
    """Сохраняет настройки"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, sound_enabled, music_enabled, language, theme)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, settings.get('sound', 1), settings.get('music', 1), settings.get('language', 'ru'), settings.get('theme', 'light')))
    conn.commit()
    conn.close()


def load_user_settings(user_id):
    """Загружает настройки"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'sound': row['sound_enabled'],
            'music': row['music_enabled'],
            'language': row['language'],
            'theme': row['theme']
        }
    return {'sound': 1, 'music': 1, 'language': 'ru', 'theme': 'light'}