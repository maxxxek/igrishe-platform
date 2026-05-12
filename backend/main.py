#!/usr/bin/env python3
"""
🎮 ИГРИЩЕ — Главный сервер (полностью на играх-плагинах)
"""

import http.server
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PORT, HOST, STATIC_DIR, DEBUG
from storage.database import init_db, add_table_columns
from api.rooms import (
    handle_create, handle_join, handle_state,
    handle_reset, handle_games_list
)
from games import GAMES
from api.rooms import storage


class GameServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        super().__init__(*args, directory=root_dir, **kwargs)

    # ========== GET ==========
    def do_GET(self):
        # Получаем параметры из URL для GET запросов
        parsed_path = self.path.split('?')[0]
        
        if self.path in ['/', '/hello']:
            self.path = '/frontend/hello.html'
        elif self.path == '/tv':
            self.path = '/frontend/tv.html'
        elif self.path == '/player':
            self.path = '/frontend/player.html'
        
        elif self.path.startswith('/api/pari/question'):
            code = self.path.split('?code=')[-1]
            from api.rooms import storage
            room = storage.get(code)
            if room:
                from games import GAMES
                game = GAMES.get(room.game_id)
                if game and hasattr(game, 'get_question'):
                    self._json(game.get_question(room))
                    return
            self._json({'error': 'Не найдено'}, 404)
            return

        elif self.path.startswith('/api/pari/results'):
            code = self.path.split('?code=')[-1]
            from api.rooms import storage
            room = storage.get(code)
            if room:
                from games import GAMES
                game = GAMES.get(room.game_id)
                if game and hasattr(game, 'get_results'):
                    self._json(game.get_results(room))
                    return
            self._json({'error': 'Не найдено'}, 404)
            return

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
        
        elif self.path == '/api/pari/go-bet':
            self._handle_game_action({})  # ← исправлено
            return
        
        elif self.path == '/api/pari/go-answer':
            self._handle_game_action({})  # ← исправлено
            return
        
        elif self.path.startswith('/api/state/'):
            code = self.path.split('/')[-1]
            data, status = handle_state(code)
            self._json(data, status)
            return
        
        elif self.path.startswith('/api/game-page/'):
            game_type = self.path.split('/')[-1]
            game = GAMES.get(game_type)
            if game:
                self._json(game.get_pages())
            else:
                self._json({})
            return
        
        elif self.path.startswith('/api/avatars/'):
            code = self.path.split('/')[-1].upper()
            room = storage.get(code)
            if room:
                avatars = {}
                for pid, p in room.players.items():
                    avatars[pid] = p.get('avatar_url', '')
                self._json(avatars)
            else:
                self._json({})
            return
        
        elif self.path == '/api/wallet':
            user_id = self.headers.get('X-User-Id', '')
            if user_id:
                from storage.database import get_user_by_id
                user = get_user_by_id(int(user_id))
                if user:
                    self._json({
                        'coins': user.get('coins', 0),
                        'gems': user.get('gems', 0),
                        'premium': user.get('is_premium', 0),
                        'premium_until': user.get('premium_until', None)
                    })
                    return
            self._json({'coins': 0, 'gems': 0, 'premium': 0, 'premium_until': None})
            return

        return super().do_GET()

    # ========== POST ==========
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        # Общие API
        if self.path == '/api/join':
            code = body.get('code', '').upper()
            name = body.get('name', 'Игрок').strip() or 'Игрок'
            avatar_url = body.get('avatar_url', '')
            data, status = handle_join(code, name, avatar_url)
            self._json(data, status)
            return

        elif self.path == '/api/reset':
            data, status = handle_reset(body.get('code', '').upper())
            self._json(data, status)
            return

        # Авторизация
        elif self.path == '/api/auth/register':
            self._handle_auth_register(body)
            return
        elif self.path == '/api/auth/login':
            self._handle_auth_login(body)
            return

        # Загрузка аватара
        elif self.path == '/api/upload-avatar':
            self._handle_upload_avatar()
            return

        # Синхронизация
        elif self.path == '/api/user/sync':
            self._handle_user_sync(body)
            return
        elif self.path == '/api/wallet/sync':
            self._handle_wallet_sync(body)
            return

        # 🔥 ИГРОВЫЕ ДЕЙСТВИЯ
        elif self.path in [
            '/api/start', '/api/answer', '/api/next',
            '/api/vote', '/api/task_done',
            '/api/pari/ready', '/api/pari/bet', '/api/pari/answer',
            '/api/pari/next', '/api/pari/go-bet', '/api/pari/go-answer',
            '/api/pari/go-show-answers', '/api/pari/go-result',
            '/api/game/reward',
            '/api/mafia/role', '/api/mafia/host/action', 
            '/api/mafia/host/execute', '/api/mafia/host/end',
        ]:
            self._handle_game_action(body)
            return

        # GET-запросы для pari (вопрос/результат)
        elif self.path.startswith('/api/pari/question') or self.path.startswith('/api/pari/results'):
            code = body.get('code') or self.path.split('?code=')[-1]
            body['code'] = code
            self._handle_game_action(body)
            return

        else:
            self._json({'error': 'Неизвестный запрос'}, 404)

    # ========== ДЕЛЕГИРОВАНИЕ ИГРАМ ==========
    def _handle_game_action(self, body):
        print(f'🔥 Игровой запрос: {self.path}, body: {body}')
        code = body.get('code', '').upper() if body else ''
        
        # Если code не нашли в body, пробуем из URL
        if not code and hasattr(self, 'path'):
            if '?code=' in self.path:
                code = self.path.split('?code=')[-1].split('&')[0]
        
        room = storage.get(code)
        if not room:
            return self._json({'error': 'Комната не найдена'}, 404)

        game = GAMES.get(room.game_id)
        if not game:
            return self._json({'error': 'Игра не найдена'}, 404)

        result = game.handle(room, body, self.path)
        if result is not None:
            self._json(result)
        else:
            self._json({'error': 'Действие не поддерживается'}, 400)

    # ========== АВТОРИЗАЦИЯ ==========
    def _handle_auth_register(self, body):
        from storage.database import register_user
        u = body.get('username', '').strip()
        e = body.get('email', '').strip()
        p = body.get('password', '')
        if not u or not e or not p:
            return self._json({'error': 'Заполни все поля'}, 400)
        if len(u) < 2:
            return self._json({'error': 'Имя короткое'}, 400)
        if len(p) < 6:
            return self._json({'error': 'Пароль короткий'}, 400)
        r = register_user(u, e, p)
        if 'error' in r:
            return self._json({'error': r['error']}, 400)
        self._json({'token': 't-' + str(r['user']['id']), 'user': r['user'], 'wallet': {'coins': r['user']['coins']}})

    def _handle_auth_login(self, body):
        from storage.database import login_user
        l = body.get('login', '').strip()
        p = body.get('password', '')
        if not l or not p:
            return self._json({'error': 'Заполни все поля'}, 400)
        r = login_user(l, p)
        if 'error' in r:
            return self._json({'error': r['error']}, 400)
        self._json({'token': 't-' + str(r['user']['id']), 'user': r['user'], 'wallet': {'coins': r['user']['coins']}})

    # ========== АВАТАР ==========
    def _handle_upload_avatar(self):
        try:
            ct = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in ct:
                return self._json({'error': 'Неверный формат'}, 400)
            boundary = ct.split('boundary=')[-1].encode()
            raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            parts = raw.split(b'--' + boundary)
            for part in parts:
                if b'filename=' in part:
                    h_end = part.find(b'\r\n\r\n')
                    data = part[h_end+4:].rsplit(b'\r\n', 1)[0]
                    import uuid
                    fn = f"user_{uuid.uuid4().hex[:8]}.png"
                    d = os.path.join(STATIC_DIR, 'avatars')
                    os.makedirs(d, exist_ok=True)
                    with open(os.path.join(d, fn), 'wb') as f:
                        f.write(data)
                    self._json({'ok': True, 'avatar_url': f'/static/avatars/{fn}'})
                    return
            self._json({'error': 'Файл не найден'}, 400)
        except Exception as e:
            print(f'Ошибка загрузки: {e}')
            self._json({'error': 'Ошибка сервера'}, 500)

    # ========== СИНХРОНИЗАЦИЯ ==========
    def _handle_user_sync(self, body):
        uid = body.get('user_id', '')
        if not uid:
            return self._json({'error': 'Нет user_id'}, 400)
        from storage.database import save_equipped_avatar, save_user_items, save_user_settings
        eq = body.get('equipped', {})
        if eq.get('avatar'):
            save_equipped_avatar(int(uid), eq.get('avatar', ''))
        items = body.get('owned_items', [])
        if items:
            save_user_items(int(uid), items)
        settings = body.get('settings', {})
        if settings:
            save_user_settings(int(uid), settings)
        self._json({'ok': True})

    def _handle_wallet_sync(self, body):
        uid = body.get('user_id', '')
        coins = body.get('coins', 0)
        if uid and coins > 0:
            from storage.database import update_coins
            update_coins(int(uid), coins)
        self._json({'ok': True})

    # ========== УТИЛИТЫ ==========
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
    init_db()
    add_table_columns()
    print('=' * 60)
    print('🎮  И Г Р И Щ Е  —  Платформа v3.0 (игры-плагины)')
    print('=' * 60)
    print(f'📺  ТВ:       http://localhost:{PORT}/tv')
    print(f'📱  Телефон:  http://localhost:{PORT}/player')
    print(f'🌐  Лендинг:  http://localhost:{PORT}/')
    print('=' * 60)
    print(f'📦 Игр загружено: {len(GAMES)}')
    for gid, g in GAMES.items():
        print(f'   {g.name}')
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