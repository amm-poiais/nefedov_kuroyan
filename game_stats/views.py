from django.db import connection

from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from game_stats.models import *
from game_stats.utils import get_top10, get_player_pos, get_player_high_score
from game_stats.serializers import ScoreEntrySerializer, GameSerializer


class UpdateScoreView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, game_id, difficulty_id) -> Response:
        new_score = request.data.get('score', None)
        if not new_score:
            return Response({"error": "You must provide new score"}, status=400)
        player = request.user

        try:
            game = Game.objects.get(pk=game_id)
            difficulty = Difficulty.objects.get(pk=difficulty_id)
        except Game.DoesNotExist:
            return Response({"error": "Invalid game id"}, status=400)
        except Difficulty.DoesNotExist:
            return Response({"error": "Invalid difficulty id"}, status=400)
        
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

        top10 = get_top10(game_id, difficulty_id)
        top10_serializer = ScoreEntrySerializer(top10, many=True)
        return Response({
            "your_place": get_player_pos(game_id, difficulty_id, player.id),
            "your_high_score": get_player_high_score(game_id, difficulty_id, player.id),
            "top10": top10_serializer.data,
        })

    def get(self, request, game_id, difficulty_id) -> Response:
        player: User = request.user
        top10players = get_top10(game_id, difficulty_id)

        top10_serializer = ScoreEntrySerializer(top10players, many=True)

        response_dict = {
            "top10": top10_serializer.data
        }

        if player:
            response_dict["your_place"] = get_player_pos(game_id, difficulty_id, player.id)
            response_dict["your_high_score"] = get_player_high_score(game_id, difficulty_id, player.id)

        return Response(response_dict)


class GameView(views.APIView):
    permission_classes = ()

    def get(self, request):
        games = Game.objects.all()
        serializer = GameSerializer(games, many=True)

        return Response(serializer.data)
