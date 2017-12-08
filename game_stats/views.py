from django.db import connection

from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from game_stats.models import *
from game_stats.serializers import ScoreEntrySerializer, PlayerSerializer


class UpdateScoreView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get_top10(self, game_id, difficulty_id):
        game = Game.objects.get(pk=game_id)
        difficulty = Difficulty.objects.get(pk=difficulty_id)

        top10players = ScoreEntry.objects.filter(game=game, difficulty=difficulty)
        return top10players.order_by('-best_score')[:10]

    def get_player_pos(self, game_id, difficulty_id, player_id):
        with connection.cursor() as cursor:
            query_str = 'SELECT COUNT(1) AS place ' \
                        'FROM game_stats_scoreentry AS scoreentry ' \
                        'WHERE (scoreentry.game_id = %s) AND ' \
                        '      (scoreentry.difficulty_id = %s) AND ' \
                        '      (scoreentry.best_score > ( ' \
                        '        SELECT MAX(best_score) ' \
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

    def post(self, request: Request, game_id, difficulty_id):
        new_score = request.data.get('score', None)
        player = request.user
        game = Game.objects.get(pk=game_id)
        difficulty = Difficulty.objects.get(pk=difficulty_id)
        
        score_entries = ScoreEntry.objects.filter(user=player, game=game, difficulty=difficulty)

        got_higher = False
        if not score_entries:
            score_entry = ScoreEntry(user=player, game=game, difficulty=difficulty, best_score=new_score)
            score_entry.save()
            got_higher = True
        else:
            score_entry = score_entries[0]
            if score_entry.best_score < int(new_score):
                score_entry.best_score = new_score
                score_entry.save()
                got_higher = True

        top10 = self.get_top10(game_id, difficulty_id)
        top10_serializer = ScoreEntrySerializer(top10, many=True)
        return Response({
            "your_place": self.get_player_pos(game_id, difficulty_id, player.id),
            "got_higher": got_higher,
            "top10": top10_serializer.data,
        })

    def get(self, request, game_id, difficulty_id):
        player: User = request.user
        top10players = self.get_top10(game_id, difficulty_id)

        top10_serializer = ScoreEntrySerializer(top10players, many=True)

        return Response({
            "your_place": self.get_player_pos(game_id, difficulty_id, player.id),
            "top10": top10_serializer.data
        })
