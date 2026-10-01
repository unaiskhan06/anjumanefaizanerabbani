from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import sitemaps
from core.views import robots_txt

urlpatterns = [
    # Private admin panel. The default /admin/ URL intentionally does not exist.
    path("manage/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("events/", include("events.urls")),
    path("contact/", include("contact.urls")),
    path("", include("gallery.urls")),
    path("", include("videos.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
