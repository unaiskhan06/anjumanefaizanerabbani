from django.shortcuts import render

from core.utils import paginate

from .models import AudioTrack, GalleryImage


def gallery(request):
    return render(request, "gallery/gallery.html", {"page_obj": paginate(request, GalleryImage.objects.all(), 24)})


def audio(request):
    return render(request, "gallery/audio.html", {"page_obj": paginate(request, AudioTrack.objects.all(), 30)})
