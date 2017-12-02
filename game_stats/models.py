from django.db import models
from authentication.models import User


class Game(models.Model):
    name = models.CharField(max_length=100)
    priority = models.IntegerField()
    image_url = models.CharField(max_length=255)


class Difficulty(models.Model):
    name = models.CharField(max_length=20)


class ScoreEntry(models.Model):
    user = models.ForeignKey(to=User)
    game = models.ForeignKey(to=Game)
    difficulty = models.ForeignKey(to=Difficulty)
    best_score = models.IntegerField()

    class Meta:
        unique_together=(('user', 'game', 'difficulty'),)
