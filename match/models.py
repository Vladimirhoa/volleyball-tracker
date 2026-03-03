from django.db import models

class Match(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    my_score = models.IntegerField(default=0)
    opponent_score = models.IntegerField(default=0)
    date = models.DateTimeField()
    class Meta:
        verbose_name = "Матч"
        verbose_name_plural = "Матчи"
    def __str__(self):
        return f"{self.title} ({self.date.strftime('%Y-%m-%d')})"


