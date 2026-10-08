from django.core.cache import cache
from django.db import models

from .utils import SETTINGS_CACHE_KEY


class SiteSetting(models.Model):
    """A single row holding contact details, social links and About-page text."""

    committee_name = models.CharField(max_length=150, default="Anjuman E Faizan E Rabbani | Chennai")
    tagline = models.CharField(max_length=255, blank=True,
                               default="Naat, Bayan and spiritual gatherings from Chennai.")

    youtube_url = models.URLField("YouTube channel", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)

    whatsapp_number = models.CharField(max_length=20, blank=True,
                                       help_text="International format without + or spaces, e.g. 919791054168.")
    phone_label = models.CharField(max_length=60, blank=True, default="Committee Sadar")
    phone = models.CharField(max_length=30, blank=True)
    phone2_label = models.CharField(max_length=60, blank=True, default="Committee Admin")
    phone2 = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    map_embed_url = models.URLField(blank=True,
                                    help_text="Optional Google Maps embed link (Share → Embed a map → copy the src URL).")
    map1_url = models.URLField("Map link 1", blank=True)
    map1_label = models.CharField("Map label 1", max_length=120, blank=True)
    map2_url = models.URLField("Map link 2", blank=True)
    map2_label = models.CharField("Map label 2", max_length=120, blank=True)

    monthly_schedule = models.TextField("Monthly schedule", blank=True,
                                        help_text="One item per line, e.g. “Sunday after Isha — Gyarvi Sharif Mehfil”.")
    about_text = models.TextField("About / Our story", blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj = cache.get(SETTINGS_CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(SETTINGS_CACHE_KEY, obj, 300)
        return obj

    @property
    def schedule_items(self):
        return [line.strip() for line in self.monthly_schedule.splitlines() if line.strip()]

    @property
    def whatsapp_link(self):
        digits = "".join(ch for ch in self.whatsapp_number if ch.isdigit())
        return f"https://wa.me/{digits}" if digits else ""


class Banner(models.Model):
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    program_label = models.CharField(max_length=60, blank=True, help_text="Small label, e.g. “Weekly Mehfil”.")
    image = models.ImageField(upload_to="banners/")
    link_url = models.CharField("Link", max_length=300, blank=True,
                                help_text="Optional. A full URL or a site path like /popular/.")
    sort_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "hero banner"

    def __str__(self):
        return self.title


class Announcement(models.Model):
    """A landscape poster shown in the home-page "Announcements" section (hidden when there are none)."""

    title = models.CharField(max_length=150, help_text="Short title, shown under the image and read by screen readers.")
    image = models.ImageField("Landscape image", upload_to="announcements/",
                              help_text="Wide (landscape) picture, ideally 1600 × 900 px (16:9).")
    link_url = models.CharField("Link", max_length=300, blank=True,
                                help_text="Optional. A full URL or a site path like /events/. "
                                          "If empty, clicking opens the image full-size.")
    show_until = models.DateField(blank=True, null=True,
                                  help_text="Optional. The announcement hides itself automatically after this date.")
    sort_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title


class PlaylistLink(models.Model):
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to="playlists/", blank=True)
    url = models.URLField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "playlist / channel link"
        verbose_name_plural = "playlists & channel links"

    def __str__(self):
        return self.name


class PartnerChannel(models.Model):
    """An additional YouTube channel promoted with its own "Subscribe" banner on the home page."""

    name = models.CharField(max_length=150)
    name_urdu = models.CharField("Name (Urdu)", max_length=150, blank=True)
    url = models.URLField("YouTube channel link", help_text="e.g. https://www.youtube.com/@channelname")
    image = models.ImageField("Channel picture", upload_to="channels/", blank=True,
                              help_text="Optional round profile picture. The site logo is used if empty.")
    tagline = models.CharField(max_length=255, blank=True,
                               help_text="One short sentence shown under the channel name.")
    sort_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "partner YouTube channel"

    def __str__(self):
        return self.name

    @property
    def subscribe_url(self):
        return self.url.split("?")[0].rstrip("/") + "?sub_confirmation=1"


class DonationInfo(models.Model):
    """QR code and description for the Chanda (donation) section on the About page."""

    title = models.CharField(max_length=200, default="Support Our Religious & Community Activities")
    title_urdu = models.CharField("Title (Urdu/Arabic)", max_length=200, blank=True,
                                  default="ہماری دینی و فلاحی سرگرمیوں میں تعاون کریں")
    description = models.TextField(
        blank=True,
        default=(
            "We humbly invite you to contribute towards our Chanda Collection and support our "
            "religious, educational, and community welfare activities.\n\n"
            "Your generous contribution, whether small or large, is a valuable means of supporting "
            "these noble efforts. May Allah ﷻ accept your contribution, bless your wealth, and "
            "reward you abundantly for your generosity. Ameen."
        ),
        help_text="Rich description shown above the QR code.",
    )
    qr_image = models.ImageField("QR code image", upload_to="donation/",
                                 help_text="Upload the UPI / payment QR code image.")
    upi_id = models.CharField("UPI ID", max_length=120, blank=True,
                              help_text="e.g. anjumanefaizanerabbani2023@oksbi")
    footer_note = models.CharField(max_length=300, blank=True,
                                   default="جزاكم الله خيرًا — JazakAllahu Khairan — May Allah reward you with goodness.",
                                   help_text="Short line shown below the QR code.")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "donation / chanda info"
        verbose_name_plural = "donation / chanda info"
        ordering = ["-active", "-updated_at"]

    def __str__(self):
        return self.title
