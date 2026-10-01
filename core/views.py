from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from videos.models import Category, Video

from .models import Announcement, Banner, PartnerChannel, PlaylistLink
from .utils import HOME_CACHE_KEY, paginate

ROW_SIZE = 12


def _category_row(categories, slug, title, title_urdu, base):
    category = categories.get(slug)
    videos = list(base.filter(category=category)[:ROW_SIZE]) if category else []
    url = category.get_absolute_url() if category else reverse("videos:categories")
    return {"id": slug, "title": title, "title_urdu": title_urdu, "videos": videos, "url": url}


def _build_home_data():
    base = Video.objects.published()
    # Shorts only appear in the "YouTube Shorts" row; every other row shows full-size videos.
    regular = base.exclude(video_type=Video.TYPE_SHORT)
    categories = {c.slug: c for c in Category.objects.all()}
    rows = [
        {"id": "latest", "title": "Latest Videos", "title_urdu": "تازہ ویڈیوز",
         "videos": list(regular[:ROW_SIZE]), "url": reverse("videos:all")},
        _category_row(categories, "naat-sharif", "Naat Sharif", "نعت شریف", regular),
        _category_row(categories, "bayan", "Bayan", "بیان", regular),
        {"id": "shorts", "title": "YouTube Shorts", "title_urdu": "شارٹس",
         "videos": list(base.filter(video_type=Video.TYPE_SHORT)[:ROW_SIZE]),
         "url": reverse("videos:all") + "?type=short", "is_short_row": True},
        {"id": "kids", "title": "Kids Special", "title_urdu": "بچوں کے لیے",
         "videos": list(regular.filter(Q(video_type=Video.TYPE_KIDS) | Q(category__slug="kids-special"))[:ROW_SIZE]),
         "url": reverse("videos:all") + "?type=kids"},
    ]
    today = timezone.localdate()
    return {
        "banners": list(Banner.objects.filter(active=True)),
        "announcements": list(Announcement.objects.filter(active=True)
                              .filter(Q(show_until__isnull=True) | Q(show_until__gte=today))),
        "partner_channels": list(PartnerChannel.objects.filter(active=True)),
        "categories": list(categories.values()),
        "rows": rows,
        "live_video": base.filter(is_live=True).first(),
        "next_event": Event.objects.filter(date__gte=today).order_by("date", "time").first(),
    }


def home(request):
    data = cache.get(HOME_CACHE_KEY)
    if data is None:
        data = _build_home_data()
        cache.set(HOME_CACHE_KEY, data, settings.HOME_CACHE_SECONDS)
    return render(request, "core/home.html", data)


def about(request):
    return render(request, "core/about.html")


def playlists(request):
    return render(request, "core/playlists.html", {"page_obj": paginate(request, PlaylistLink.objects.all(), 12)})


def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    return render(request, "robots.txt", {"sitemap_url": sitemap}, content_type="text/plain")
