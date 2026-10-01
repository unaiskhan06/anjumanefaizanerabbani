from django.core.validators import FileExtensionValidator
from django.db import models


class GalleryImage(models.Model):
    image = models.ImageField(upload_to="gallery/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.caption or f"Image #{self.pk}"


class AudioTrack(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=150, blank=True)
    audio_file = models.FileField(
        upload_to="audio/",
        validators=[FileExtensionValidator(["mp3", "m4a", "ogg", "wav", "aac"])],
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title
