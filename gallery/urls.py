from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("gallery/", views.gallery, name="gallery"),
    path("audio/", views.audio, name="audio"),
]
