from django.conf import settings

from .models import SiteSetting


def site(request):
    return {
        "site": SiteSetting.load(),
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DISPLAY_NAME": settings.SITE_DISPLAY_NAME,
        "SITE_URDU_NAME": settings.SITE_URDU_NAME,
    }
