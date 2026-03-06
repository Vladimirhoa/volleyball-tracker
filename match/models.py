import uuid
from django.db import models
from django.contrib.auth.models import User
class Match(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    my_score = models.IntegerField(default=0)
    opponent_score = models.IntegerField(default=0)
    date = models.DateField()
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    class Meta:
        verbose_name = "Матч"
        verbose_name_plural = "Матчи"
    def __str__(self):
        return f"{self.title} ({self.date.strftime('%Y-%m-%d')})"


