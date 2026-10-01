from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from core.utils import unique_slug

from . import youtube


class Category(models.Model):
    name = models.CharField(max_length=120)
    name_urdu = models.CharField("Name (Urdu)", max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True,
                            help_text="Leave blank to generate automatically.")
    image = models.ImageField(upload_to="categories/", blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True,
                                             help_text="Lower numbers appear first.")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, fallback="category")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("videos:category", args=[self.slug])


class PublishedVideoQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published=True).select_related("category")


class Video(models.Model):
    TYPE_FULL, TYPE_SHORT, TYPE_KIDS, TYPE_AUDIO = "full", "short", "kids", "audio"
    TYPE_CHOICES = [
        (TYPE_FULL, "Full video"),
        (TYPE_SHORT, "Short (vertical)"),
        (TYPE_KIDS, "Kids special"),
        (TYPE_AUDIO, "Audio / Naat only"),
    ]

    youtube_url = models.CharField(
        "YouTube link", max_length=300,
        help_text="Paste any YouTube link (watch, youtu.be, shorts, live, embed) or the 11-character video ID.",
    )
    youtube_id = models.CharField("YouTube ID", max_length=11, unique=True, editable=False)
    title = models.CharField(max_length=255, blank=True,
                             help_text="Leave blank to fetch the title from YouTube automatically.")
    title_urdu = models.CharField("Title (Urdu)", max_length=255, blank=True)
    slug = models.SlugField(max_length=280, unique=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="videos")
    video_type = models.CharField("Type", max_length=10, choices=TYPE_CHOICES, default=TYPE_FULL)
    artist = models.CharField("Artist / Speaker", max_length=150, blank=True)
    description = models.TextField(blank=True)
    custom_thumbnail = models.ImageField(upload_to="thumbnails/", blank=True,
                                         help_text="Optional. YouTube's thumbnail is used if empty.")
    is_featured = models.BooleanField("Featured", default=False)
    is_live = models.BooleanField("Live", default=False)
    published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = PublishedVideoQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["published", "-created_at"]),
            models.Index(fields=["category", "published", "-created_at"]),
            models.Index(fields=["video_type", "published"]),
        ]

    def __str__(self):
        return self.title or self.youtube_id or "New video"

    # ---- validation -------------------------------------------------------
    def clean(self):
        super().clean()
        video_id = youtube.extract_youtube_id(self.youtube_url)
        if not video_id:
            raise ValidationError({"youtube_url": "This does not look like a valid YouTube link. "
                                                  "Please paste a link such as https://youtu.be/XXXXXXXXXXX."})
        duplicate = Video.objects.filter(youtube_id=video_id).exclude(pk=self.pk).first()
        if duplicate:
            raise ValidationError({"youtube_url": f"This video has already been added as “{duplicate}”."})
        self.youtube_id = video_id
        if youtube.is_shorts_url(self.youtube_url) and self.video_type == self.TYPE_FULL:
            self.video_type = self.TYPE_SHORT

    def save(self, *args, **kwargs):
        video_id = youtube.extract_youtube_id(self.youtube_url)
        if not video_id:
            raise ValidationError("Invalid YouTube link.")
        self.youtube_id = video_id
        self.youtube_url = self.youtube_url.strip()
        if not self.title.strip():
            self.title = youtube.fetch_title(video_id) or f"Video {video_id}"
        if not self.slug:
            self.slug = unique_slug(self, self.title, fallback=video_id)
        super().save(*args, **kwargs)

    # ---- helpers ----------------------------------------------------------
    def get_absolute_url(self):
        return reverse("videos:detail", args=[self.category.slug, self.slug])

    @property
    def thumbnail(self):
        if self.custom_thumbnail:
            return self.custom_thumbnail.url
        return youtube.thumbnail_url(self.youtube_id)

    @property
    def thumbnail_large(self):
        if self.custom_thumbnail:
            return self.custom_thumbnail.url
        return youtube.thumbnail_url(self.youtube_id, "maxresdefault")

    @property
    def embed_url(self):
        return youtube.embed_url(self.youtube_id)

    @property
    def watch_url(self):
        if self.video_type == self.TYPE_SHORT:
            return f"https://www.youtube.com/shorts/{self.youtube_id}"
        return youtube.watch_url(self.youtube_id)

    @property
    def is_short(self):
        return self.video_type == self.TYPE_SHORT

    def thumbnail_tag(self, width=120):
        return format_html('<img src="{}" width="{}" style="border-radius:6px;aspect-ratio:16/9;object-fit:cover" '
                           'loading="lazy" alt="">', self.thumbnail, width)
