"""Настройки сервера"""
import os

# Сервер
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
GAMES_DIR = os.path.join(DATA_DIR, "games")
QUESTIONS_DIR = os.path.join(DATA_DIR, "questions")
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Игра
MAX_PLAYERS = 8
ROOM_CODE_LENGTH = 4
DEFAULT_GAME = "quiz"

# Базы данных (будут использоваться позже)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/igrishe")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "igrishe-secret-key-change-in-production")
JWT_EXPIRE_DAYS = 30