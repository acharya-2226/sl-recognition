from django.db import models
from django.contrib.auth.models import User

TRACK_CHOICES = [
    ("NUM", "Number"),
    ("ASL", "ASL"),
    ("NSL", "NSL"),
]


class TrackVisibility(models.Model):
    track = models.CharField(max_length=3, choices=TRACK_CHOICES, unique=True)
    show_in_learning = models.BooleanField(default=True)
    show_in_practice = models.BooleanField(default=True)
    show_in_validation = models.BooleanField(default=True)
    show_in_tts = models.BooleanField(default=True)

    class Meta:
        ordering = ["track"]
        verbose_name = "Track visibility"
        verbose_name_plural = "Track visibility settings"

    def __str__(self):
        return f"{self.get_track_display()} visibility"


class LearningCategory(models.Model):
    track = models.CharField(max_length=3, choices=TRACK_CHOICES)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["track", "order"]
        verbose_name_plural = "Learning categories"

    def __str__(self):
        return f"{self.get_track_display()} - {self.name}"


class LearningItem(models.Model):
    category = models.ForeignKey(LearningCategory, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="signs/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "order"]

    def __str__(self):
        return f"{self.category.name} - {self.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    learning_item = models.ForeignKey(LearningItem, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "learning_item")

    def __str__(self):
        return f"{self.user} - {self.learning_item} ({'done' if self.completed else 'in progress'})"
