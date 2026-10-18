from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from core.utils import unique_slug

from . import instagram, youtube


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


from .storage import SmartPDFStorage, get_pdf_storage


class Video(models.Model):
    TYPE_FULL, TYPE_SHORT, TYPE_KIDS, TYPE_AUDIO, TYPE_REEL = "full", "short", "kids", "audio", "reel"
    TYPE_CHOICES = [
        (TYPE_FULL, "Full video"),
        (TYPE_SHORT, "Short (vertical)"),
        (TYPE_KIDS, "Kids special"),
        (TYPE_AUDIO, "Audio / Naat only"),
        (TYPE_REEL, "Instagram Reel"),
    ]

    youtube_url = models.CharField(
        "YouTube link", max_length=300, blank=True,
        help_text="Paste any YouTube link (watch, youtu.be, shorts, live, embed) or the 11-character video ID.",
    )
    instagram_url = models.URLField(
        "Instagram reel link", blank=True,
        help_text="Paste an Instagram reel/post link to play it inside the site.",
    )
    pdf_file = models.FileField(
        "PDF file", upload_to="pdfs/", blank=True, storage=get_pdf_storage,
        help_text="Upload a PDF document. You can upload a PDF without a YouTube or Instagram link.",
    )
    youtube_id = models.CharField("YouTube ID", max_length=11, unique=True, editable=False, blank=True, null=True)
    instagram_shortcode = models.CharField("Instagram shortcode", max_length=30, unique=True, editable=False,
                                           blank=True, null=True)
    title = models.CharField(max_length=255, blank=True,
                             help_text="Leave blank to fetch the title from the source automatically.")
    title_urdu = models.CharField("Title (Urdu)", max_length=255, blank=True)
    slug = models.SlugField(max_length=280, unique=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="videos", blank=True, null=True)
    video_type = models.CharField("Type", max_length=140, blank=True, default="")
    artist = models.CharField("Artist / Speaker", max_length=150, blank=True)
    description = models.TextField(blank=True)
    custom_thumbnail = models.ImageField(upload_to="thumbnails/", blank=True,
                                         help_text="Optional. YouTube/Instagram thumbnail is used if empty.")
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
        return self.title or self.youtube_id or self.instagram_shortcode or "New video"

    # ---- validation -------------------------------------------------------
    def _get_or_create_instagram_category(self):
        return Category.objects.get_or_create(
            slug="instagram-reels",
            defaults={"name": "Instagram Reels", "name_urdu": "انستاگرام ریلز"},
        )[0]

    def clean(self):
        super().clean()
        video_id = youtube.extract_youtube_id(self.youtube_url) if self.youtube_url else None
        shortcode = instagram.extract_shortcode(self.instagram_url) if self.instagram_url else None
        has_pdf = bool(self.pdf_file)
        if not video_id and not shortcode and not has_pdf:
            raise ValidationError({"youtube_url": "Paste a YouTube link, an Instagram reel link, or upload a PDF file."})
        if self.youtube_url and not video_id:
            raise ValidationError({"youtube_url": "This does not look like a valid YouTube link. "
                                                  "Please paste a link such as https://youtu.be/XXXXXXXXXXX."})
        if self.instagram_url and not shortcode:
            raise ValidationError({"instagram_url": "This does not look like a valid Instagram reel link. "
                                                    "Please paste a link such as https://www.instagram.com/reel/XXXX."})
        if video_id and Video.objects.filter(youtube_id=video_id).exclude(pk=self.pk).exists():
            raise ValidationError({"youtube_url": f"This YouTube video has already been added."})
        if shortcode and Video.objects.filter(instagram_shortcode=shortcode).exclude(pk=self.pk).exists():
            raise ValidationError({"instagram_url": "This Instagram reel has already been added."})
        self.youtube_id = video_id
        self.instagram_shortcode = shortcode
        if video_id and youtube.is_shorts_url(self.youtube_url) and self.video_type not in (self.TYPE_KIDS, self.TYPE_AUDIO, self.TYPE_REEL):
            self.video_type = self.TYPE_SHORT
        elif shortcode and not video_id:
            self.video_type = self.TYPE_REEL

    def save(self, *args, **kwargs):
        video_id = youtube.extract_youtube_id(self.youtube_url) if self.youtube_url else None
        shortcode = instagram.extract_shortcode(self.instagram_url) if self.instagram_url else None
        has_pdf = bool(self.pdf_file)
        if not video_id and not shortcode and not has_pdf:
            raise ValidationError("Paste a YouTube link, an Instagram reel link, or upload a PDF file.")
        self.youtube_id = video_id
        self.instagram_shortcode = shortcode
        if video_id and youtube.is_shorts_url(self.youtube_url) and self.video_type not in (self.TYPE_KIDS, self.TYPE_AUDIO, self.TYPE_REEL):
            self.video_type = self.TYPE_SHORT
        elif shortcode and not video_id:
            self.video_type = self.TYPE_REEL
        if not self.title.strip():
            if video_id:
                self.title = youtube.fetch_title(video_id) or f"Video {video_id}"
            elif shortcode:
                self.title = "Instagram Reel"
            elif has_pdf:
                self.title = self.pdf_file.name.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        if not self.category_id:
            self.category = self._get_or_create_instagram_category() if shortcode else None
        if not self.slug:
            fallback = video_id or shortcode or "pdf"
            self.slug = unique_slug(self, self.title, fallback=fallback)
        self.youtube_url = self.youtube_url.strip()
        self.instagram_url = self.instagram_url.strip()
        super().save(*args, **kwargs)

    # ---- helpers ----------------------------------------------------------
    def get_absolute_url(self):
        return reverse("videos:detail", args=[self.category.slug, self.slug])

    @property
    def thumbnail(self):
        if self.custom_thumbnail:
            return self.custom_thumbnail.url
        if self.youtube_id:
            return youtube.thumbnail_url(self.youtube_id)
        if self.instagram_shortcode:
            return f"{settings.STATIC_URL}img/reel-placeholder.svg"
        return f"{settings.STATIC_URL}img/reel-placeholder.svg"

    @property
    def thumbnail_large(self):
        if self.custom_thumbnail:
            return self.custom_thumbnail.url
        if self.youtube_id:
            return youtube.thumbnail_url(self.youtube_id, "maxresdefault")
        return f"{settings.STATIC_URL}img/reel-placeholder.svg"

    @property
    def embed_url(self):
        if self.youtube_id:
            return youtube.embed_url(self.youtube_id)
        if self.instagram_shortcode:
            return instagram.embed_url(self.instagram_shortcode, self.instagram_url)
        return ""

    @property
    def watch_url(self):
        if self.youtube_id:
            if self.video_type == self.TYPE_SHORT:
                return f"https://www.youtube.com/shorts/{self.youtube_id}"
            return youtube.watch_url(self.youtube_id)
        if self.instagram_shortcode:
            return instagram.watch_url(self.instagram_shortcode)
        return ""

    @property
    def is_short(self):
        return self.video_type == self.TYPE_SHORT

    @property
    def is_reel(self):
        return self.video_type == self.TYPE_REEL

    @property
    def is_vertical(self):
        return self.video_type in (self.TYPE_SHORT, self.TYPE_REEL)

    def thumbnail_tag(self, width=120):
        aspect = "9/16" if self.is_vertical else "16/9"
        return format_html('<img src="{}" width="{}" style="border-radius:6px;aspect-ratio:{};object-fit:cover" '
                           'loading="lazy" alt="">', self.thumbnail, width, aspect)
