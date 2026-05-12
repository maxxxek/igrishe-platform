"""Реестр игр"""
from .quiz_game import QuizGame
from .truth_dare_game import TruthDareGame
from .mafia_game import MafiaGame
from .pari_game import PariGame

GAMES = {
    'quiz': QuizGame(),
    'truth_dare': TruthDareGame(),
    'mafia': MafiaGame(),
    'kto_blizhe': PariGame(),
}

print(f'📦 Загружено игр: {len(GAMES)}')
for gid, g in GAMES.items():
    print(f'   {g.name}')