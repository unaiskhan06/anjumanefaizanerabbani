from django.core.cache import cache
from django.core.paginator import Paginator
from django.utils.text import slugify

HOME_CACHE_KEY = "home:data"
SETTINGS_CACHE_KEY = "core:site_setting"


def unique_slug(instance, value, field="slug", max_length=None, fallback="item"):
    """Build a slug from `value` that is unique for the instance's model."""
    max_length = max_length or instance._meta.get_field(field).max_length
    base = (slugify(value) or slugify(fallback) or "item")[: max_length - 6].strip("-")
    slug, n = base, 2
    qs = type(instance)._default_manager.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(**{field: slug}).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def paginate(request, queryset, per_page=12):
    """Return a page object; out-of-range or invalid page numbers fall back safely."""
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def clear_public_cache():
    cache.delete_many([HOME_CACHE_KEY, SETTINGS_CACHE_KEY])
