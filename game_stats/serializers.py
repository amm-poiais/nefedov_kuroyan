from rest_framework import serializers

from authentication.models import User
from game_stats.models import ScoreEntry, Game, Difficulty


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class ScoreEntrySerializer(serializers.ModelSerializer):
    user = PlayerSerializer(read_only=True)

    class Meta:
        model = ScoreEntry
        fields = ('user', 'best_score',)
        depth = 1


class Top10Serializer(serializers.Serializer):
    player = PlayerSerializer()
    top10 = ScoreEntrySerializer(many=True)
