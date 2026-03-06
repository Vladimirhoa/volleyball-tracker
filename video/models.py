from django.db import models
from django.contrib.auth.models import User
from match.models import Match
from datetime import datetime
import uuid
def user_directory_path(instance, filename):
    now = datetime.now()
    return f"videos/user_{instance.user.id}/{now.strftime('%Y/%m/%d')}/{filename}"

class Video(models.Model):
    STATUS_CHOICES = [
        ('processing', 'В очереди / Обрабатывается'),
        ('ready', 'Готово'),
        ('error', 'Ошибка'),
    ]

    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to=user_directory_path, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    progress = models.IntegerField(default=0)
    share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"

    def __str__(self):
        return f"{self.title} (Матч:{self.match})"

    @property
    def file_size(self):
        try:
            if self.video and hasattr(self.video, 'size'):
                return self.video.size
        except Exception:
            pass
        return None