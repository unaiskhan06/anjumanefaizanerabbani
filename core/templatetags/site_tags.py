from django import template

register = template.Library()


@register.filter
def absolute(url, request):
    """Turn a site-relative URL (e.g. /media/x.jpg) into an absolute one for social tags."""
    if not url:
        return ""
    url = str(url)
    if url.startswith(("http://", "https://")):
        return url
    return request.build_absolute_uri(url)


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """Return the current querystring with `page` replaced (keeps ?q= and ?type=)."""
    params = context["request"].GET.copy()
    params["page"] = page_number
    return "?" + params.urlencode()
