from django.core.exceptions import ValidationError
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
        upload_to="audio/", blank=True,
        validators=[FileExtensionValidator(["mp3", "m4a", "ogg", "wav", "aac"])],
        help_text="Audio file (MP3, M4A, etc.). Leave empty if uploading only a cover image.",
    )
    image = models.ImageField(
        "Cover image", upload_to="audio/covers/", blank=True,
        help_text="Optional. If no audio file is provided, this image will display on the site as an image card.",
    )
    lyrics_image = models.ImageField(
        "Lyrics image", upload_to="audio/lyrics/", blank=True,
        help_text="Upload lyrics sheet / Kalaam photo. Users can view the full image in high resolution on the website.",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.audio_file and not self.image and not self.lyrics_image:
            raise ValidationError("Please provide an audio file, a cover image, or a lyrics image.")
