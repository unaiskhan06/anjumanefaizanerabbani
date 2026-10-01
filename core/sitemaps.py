from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from events.models import Event
from videos.models import Category, Video


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ["core:home", "videos:categories", "videos:popular", "videos:all", "core:playlists",
                "events:list", "gallery:audio", "gallery:gallery", "core:about", "contact:contact"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.6


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Category.objects.all()


class VideoSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    limit = 5000

    def items(self):
        return Video.objects.published().order_by("-created_at")

    def lastmod(self, obj):
        return obj.created_at


class EventSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Event.objects.all()[:200]


sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "videos": VideoSitemap,
    "events": EventSitemap,
}
