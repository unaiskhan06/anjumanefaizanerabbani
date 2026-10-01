from django.shortcuts import render
from django.utils import timezone

from core.utils import paginate

from .models import Event


def event_list(request):
    today = timezone.localdate()
    upcoming = Event.objects.filter(date__gte=today).order_by("date", "time")
    past = Event.objects.filter(date__lt=today).order_by("-date", "-time")
    return render(request, "events/event_list.html", {
        "upcoming": upcoming,
        "page_obj": paginate(request, past, 9),
    })
