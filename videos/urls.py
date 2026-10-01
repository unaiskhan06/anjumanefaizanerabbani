from django.urls import path

from . import views

app_name = "videos"

urlpatterns = [
    path("categories/", views.category_list, name="categories"),
    path("category/<slug:slug>/", views.category_detail, name="category"),
    path("video/<slug:category_slug>/<slug:slug>/", views.video_detail, name="detail"),
    path("videos/", views.all_videos, name="all"),
    path("popular/", views.popular, name="popular"),
    path("search/", views.search, name="search"),
    path("search/suggest/", views.search_suggest, name="suggest"),
]
