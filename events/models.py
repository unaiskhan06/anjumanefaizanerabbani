from django.db import models
from django.urls import reverse


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField(db_index=True)
    time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True)
    poster = models.ImageField(upload_to="events/", blank=True)
    description = models.TextField(blank=True)
    live_url = models.URLField("Live stream link", blank=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.title} ({self.date:%d %b %Y})"

    def get_absolute_url(self):
        return reverse("events:list") + f"#event-{self.pk}"
