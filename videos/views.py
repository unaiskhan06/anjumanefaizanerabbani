import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from core.utils import paginate

from .models import Category, Video

PER_PAGE = 12
TYPE_LABELS = {
    "short": ("YouTube Shorts", "شارٹس"),
    "kids": ("Kids Special", "بچوں کے لیے"),
    "audio": ("Audio Naats", "آڈیو نعتیں"),
    "full": ("Full Videos", "مکمل ویڈیوز"),
    "reel": ("Instagram Reels", "انستاگرام ریلز"),
}


def category_list(request):
    latest = Video.objects.filter(category=OuterRef("pk"), published=True).order_by("-created_at")
    categories = Category.objects.annotate(
        video_total=Count("videos", filter=Q(videos__published=True)),
        latest_youtube_id=Subquery(latest.values("youtube_id")[:1]),
    ).order_by("sort_order", "name")
    return render(request, "videos/category_list.html", {"page_obj": paginate(request, categories, PER_PAGE)})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    videos = Video.objects.published().filter(category=category)
    shorts = list(videos.filter(video_type=Video.TYPE_SHORT)[:12])
    shorts_row = None
    if shorts:
        shorts_row = {
            "id": f"shorts-{category.slug}", "title": "YouTube Shorts", "title_urdu": "شارٹس",
            "videos": shorts, "url": reverse("videos:all") + "?type=short", "is_short_row": True,
        }
    return render(request, "videos/category_detail.html", {
        "category": category,
        "page_obj": paginate(request, videos.exclude(video_type=Video.TYPE_SHORT), PER_PAGE),
        "shorts_row": shorts_row,
    })


def all_videos(request):
    video_type = request.GET.get("type", "")
    videos = Video.objects.published()
    title, title_urdu = "Latest Videos", "تازہ ویڈیوز"
    if video_type in TYPE_LABELS:
        title, title_urdu = TYPE_LABELS[video_type]
        videos = videos.filter(video_type=video_type)
        if video_type == Video.TYPE_KIDS:
            videos = Video.objects.published().filter(Q(video_type=video_type) | Q(category__slug="kids-special"))
    if video_type != Video.TYPE_SHORT:
        videos = videos.exclude(video_type=Video.TYPE_SHORT)
    return render(request, "videos/video_list.html", {
        "page_obj": paginate(request, videos, PER_PAGE),
        "title": title,
        "title_urdu": title_urdu,
        "video_type": video_type,
    })


def popular(request):
    videos = Video.objects.published().order_by("-is_featured", "-views", "-created_at")
    return render(request, "videos/popular.html", {"page_obj": paginate(request, videos, PER_PAGE)})


def _count_view(request, video):
    """Increase the view counter at most once per browser session."""
    viewed = request.session.get("viewed_videos", [])
    if video.pk in viewed:
        return
    Video.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.views += 1
    viewed.append(video.pk)
    request.session["viewed_videos"] = viewed[-500:]


def _video_jsonld(request, video):
    data = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": video.title,
        "description": Truncator(strip_tags(video.description) or video.title).chars(300),
        "thumbnailUrl": [request.build_absolute_uri(video.thumbnail)],
        "uploadDate": video.created_at,
        "embedUrl": video.embed_url,
        "contentUrl": video.watch_url,
        "url": request.build_absolute_uri(video.get_absolute_url()),
        "interactionStatistic": {
            "@type": "InteractionCounter",
            "interactionType": {"@type": "WatchAction"},
            "userInteractionCount": video.views,
        },
    }
    if video.is_live:
        data["publication"] = {"@type": "BroadcastEvent", "isLiveBroadcast": True}
    raw = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False)
    return mark_safe(raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def video_detail(request, category_slug, slug):
    video = get_object_or_404(Video.objects.select_related("category"), slug=slug, category__slug=category_slug)
    if not video.published and not request.user.is_staff:
        raise Http404("Video not available")
    _count_view(request, video)

    siblings = Video.objects.published().filter(category=video.category, video_type=video.video_type)
    previous_video = siblings.filter(created_at__lt=video.created_at).order_by("-created_at").first()
    next_video = siblings.filter(created_at__gt=video.created_at).order_by("created_at").first()
    more = siblings.exclude(pk=video.pk)

    return render(request, "videos/video_detail.html", {
        "video": video,
        "previous_video": previous_video,
        "next_video": next_video,
        "page_obj": paginate(request, more, PER_PAGE),
        "share_url": request.build_absolute_uri(video.get_absolute_url()),
        "jsonld": _video_jsonld(request, video),
    })


def _search_queryset(query):
    return Video.objects.published().filter(
        Q(title__icontains=query)
        | Q(title_urdu__icontains=query)
        | Q(artist__icontains=query)
        | Q(category__name__icontains=query)
        | Q(category__name_urdu__icontains=query)
    )


def search(request):
    query = request.GET.get("q", "").strip()[:100]
    results = _search_queryset(query) if query else Video.objects.none()
    return render(request, "videos/search.html", {
        "query": query,
        "page_obj": paginate(request, results, PER_PAGE),
    })


@require_GET
@cache_control(max_age=60, public=True)
def search_suggest(request):
    query = request.GET.get("q", "").strip()[:100]
    if len(query) < 2:
        return JsonResponse({"results": []})
    results = [
        {"title": v.title, "title_urdu": v.title_urdu, "category": v.category.name,
         "url": v.get_absolute_url(), "thumbnail": v.thumbnail}
        for v in _search_queryset(query)[:8]
    ]
    return JsonResponse({"results": results})
