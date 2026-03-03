from django.db import models
from django.contrib.auth.models import User
from match.models import Match

class Video(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to='videos/%Y/%m/%d', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"
    def __str__(self):
        return f"{self.title} (Матч:{self.match})"