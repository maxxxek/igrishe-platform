#!/usr/bin/env python3
"""
🎮 ИГРИЩЕ — Главный сервер
"""

import http.server
import json
import sys
import os

# Добавляем текущую папку (backend) в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PORT, HOST, FRONTEND_DIR, STATIC_DIR, DEBUG
from storage.database import init_db, add_table_columns
from api.rooms import (
    handle_create, handle_join, handle_start, handle_state,
    handle_answer, handle_next, handle_reset, handle_games_list
)

class GameServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Указываем корень проекта как папку для статики
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        super().__init__(*args, directory=root_dir, **kwargs)
    
    def do_GET(self):
        # Статические страницы
        if self.path == '/' or self.path == '/hello':
            self.path = '/frontend/hello.html'
        elif self.path == '/tv':
            self.path = '/frontend/tv.html'
        elif self.path == '/player':
            self.path = '/frontend/player.html'
        
        # API
        elif self.path == '/api/games':
            data, status = handle_games_list()
            self._json(data, status)
            return
        
        elif self.path.startswith('/api/create'):
            game_id = 'quiz'
            if '?game=' in self.path:
                game_id = self.path.split('?game=')[1].split('&')[0]
            data, status = handle_create(game_id)
            self._json(data, status)
            return
        
        elif self.path.startswith('/api/state/'):
            code = self.path.split('/')[-1]
            data, status = handle_state(code)
            self._json(data, status)
            return
        
        return super().do_GET()
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        
        if self.path == '/api/join':
            code = body.get('code', '').upper()
            name = body.get('name', 'Игрок').strip() or 'Игрок'
            data, status = handle_join(code, name)
            self._json(data, status)
            return
        
        elif self.path == '/api/start':
            code = body.get('code', '').upper()
            data, status = handle_start(code)
            self._json(data, status)
            return
        
        elif self.path == '/api/answer':
            code = body.get('code', '').upper()
            player_id = body.get('player_id', '')
            answer = body.get('answer', 0)
            data, status = handle_answer(code, player_id, answer)
            self._json(data, status)
            return
                # ========== АВТОРИЗАЦИЯ ==========
        elif self.path == '/api/auth/register':
            from storage.database import register_user
            username = body.get('username', '').strip()
            email = body.get('email', '').strip()
            password = body.get('password', '')
            
            if not username or not email or not password:
                self._json({'error': 'Заполни все поля'}, 400)
                return
            
            if len(username) < 2:
                self._json({'error': 'Имя слишком короткое'}, 400)
                return
            
            if len(password) < 6:
                self._json({'error': 'Пароль минимум 6 символов'}, 400)
                return
            
            result = register_user(username, email, password)
            
            if 'error' in result:
                self._json({'error': result['error']}, 400)
                return
            
            self._json({
                'token': 'token-' + str(result['user']['id']),
                'user': result['user'],
                'wallet': {'coins': result['user']['coins']}
            })
            return
        
        elif self.path == '/api/auth/login':
            from storage.database import login_user
            login = body.get('login', '').strip()
            password = body.get('password', '')
            
            if not login or not password:
                self._json({'error': 'Заполни все поля'}, 400)
                return
            
            result = login_user(login, password)
            
            if 'error' in result:
                self._json({'error': result['error']}, 400)
                return
            
            self._json({
                'token': 'token-' + str(result['user']['id']),
                'user': result['user'],
                'wallet': {'coins': result['user']['coins']}
            })
            return
        
        elif self.path == '/api/next':
            code = body.get('code', '').upper()
            data, status = handle_next(code)
            self._json(data, status)
            return
        
        elif self.path == '/api/wallet':
            # Отдаём кошелёк (из localStorage будем синхронизировать)
            user_id = self.headers.get('X-User-Id', '')
            if user_id:
                from storage.database import get_user_by_id
                user = get_user_by_id(int(user_id))
                if user:
                    self._json({'coins': user.get('coins', 0)})
                    return
            self._json({'coins': 0})
            return
        
        elif self.path == '/api/user/sync':
            """Синхронизация всех данных пользователя"""
            user_id = body.get('user_id', '')
            if not user_id:
                self._json({'error': 'Нет user_id'}, 400)
                return
            
            from storage.database import (
                save_equipped_avatar, save_user_items, save_game_result,
                load_user_items, get_user_stats
            )
            
            # Сохраняем аватар
            equipped = body.get('equipped', {})
            if equipped.get('avatar'):
                save_equipped_avatar(int(user_id), equipped['avatar'])
            
            # Сохраняем купленные предметы
            owned_items = body.get('owned_items', [])
            if owned_items:
                save_user_items(int(user_id), owned_items)
            
            # Сохраняем настройки
            settings = body.get('settings', {})
            if settings:
                from storage.database import save_user_settings
                save_user_settings(int(user_id), settings)
            
            self._json({'ok': True})
            return

        elif self.path == '/api/wallet/sync':
            # Синхронизируем монеты
            user_id = body.get('user_id', '')
            coins = body.get('coins', 0)
            if user_id and coins > 0:
                from storage.database import update_coins
                update_coins(int(user_id), coins)
                self._json({'ok': True})
                return
            self._json({'error': 'Неверные данные'}, 400)
            return

        elif self.path == '/api/game/reward':
            code = body.get('code', '').upper()
            player_id = body.get('player_id', '')
            
            if code in rooms:
                room = rooms[code]
                if room.state == 'finished' and player_id in room.players:
                    # Вычисляем позицию игрока
                    scores = room.scores
                    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    position = next((i+1 for i, (pid, _) in enumerate(sorted_scores) if pid == player_id), len(sorted_scores))
                    
                    score = scores.get(player_id, 0)
                    
                    # Начисляем монеты (пока без привязки к user_id)
                    coins_earned = 10
                    if position == 1:
                        coins_earned += 50
                    elif position == 2:
                        coins_earned += 30
                    elif position == 3:
                        coins_earned += 15
                    coins_earned += min(score // 10, 40)
                    
                    self._json({
                        'coins_earned': coins_earned,
                        'position': position,
                        'score': score
                    })
                    return
            
            self._json({'error': 'Нельзя начислить'}, 400)
            return

        elif self.path == '/api/reset':
            code = body.get('code', '').upper()
            data, status = handle_reset(code)
            self._json(data, status)
            return
        
        self._json({'error': 'Неизвестный запрос'}, 404)
    
    def _json(self, data, status=200):
        text = json.dumps(data, ensure_ascii=False)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    from storage.database import init_db
    init_db()
    add_table_columns()
    print('=' * 60)
    print('🎮  И Г Р И Щ Е  —  Платформа v2.0')
    print('=' * 60)
    print(f'📺  ТВ:       http://localhost:{PORT}/tv')
    print(f'📱  Телефон:  http://localhost:{PORT}/player')
    print(f'🌐  Лендинг:  http://localhost:{PORT}/')
    print('=' * 60)
    print(f'🚀 Запуск на порту {PORT}...')
    
    server = http.server.HTTPServer((HOST, PORT), GameServer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Игрище остановлено!')
        server.shutdown()

if __name__ == '__main__':
    main()