from django.db import connection
from game_stats.models import *


def get_top10(game_id, difficulty_id):
    game = Game.objects.get(pk=game_id)
    difficulty = Difficulty.objects.get(pk=difficulty_id)

    top10players = ScoreEntry.objects.filter(game=game, difficulty=difficulty)
    return top10players.order_by('-best_score')[:10]


def get_player_pos(game_id, difficulty_id, player_id):
    with connection.cursor() as cursor:
        query_str = 'SELECT COUNT(1) AS place ' \
                    'FROM game_stats_scoreentry AS scoreentry ' \
                    'WHERE (scoreentry.game_id = %s) AND ' \
                    '      (scoreentry.difficulty_id = %s) AND ' \
                    '      (scoreentry.best_score > ( ' \
                    '        SELECT COALESCE(MAX(best_score), -1) ' \
                    '        FROM game_stats_scoreentry AS current_scoreentry ' \
                    '        WHERE (current_scoreentry.game_id = %s) AND ' \
                    '              (current_scoreentry.difficulty_id = %s) AND ' \
                    '              (current_scoreentry.user_id = %s) ' \
                    '        ) ' \
                    '      ) '
        data = cursor.execute(query_str, [
            game_id,
            difficulty_id,
            game_id,
            difficulty_id,
            player_id,
        ])
        return cursor.fetchone()[0]


def get_player_high_score(game_id, difficulty_id, player_id) -> int:
    try:
        score_entry = ScoreEntry.objects.get(game_id=game_id,
                                             difficulty_id=difficulty_id,
                                             user_id=player_id)
        return score_entry.best_score
    except ScoreEntry.DoesNotExist:
        return -1


def get_total_player_count(game_id = None, difficulty_id = None):
    with connection.cursor() as cursor:
        query_str = 'SELECT COUNT(1) AS players_count ' \
                    'FROM game_stats_scoreentry AS scoreentry ' \
                    'WHERE (scoreentry.game_id = %s) AND ' \
                    '      (scoreentry.difficulty_id = %s)'
        data = cursor.execute(query_str, [game_id, difficulty_id])
        return cursor.fetchone()[0]
