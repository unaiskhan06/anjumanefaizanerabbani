import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import ContactForm

logger = logging.getLogger(__name__)
RATE_LIMIT = 5          # messages …
RATE_WINDOW = 60 * 60   # … per hour, per IP address


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "unknown")


def _rate_limited(request):
    key = f"contact-rate:{_client_ip(request)}"
    cache.add(key, 0, RATE_WINDOW)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_WINDOW)
        count = 1
    return count > RATE_LIMIT


def _notify(message):
    if not settings.CONTACT_NOTIFY_EMAIL:
        return
    body = (f"Name: {message.name}\nEmail: {message.email}\nPhone: {message.phone or '-'}\n\n"
            f"{message.message}")
    try:
        send_mail(f"[Website] {message.subject}", body, settings.DEFAULT_FROM_EMAIL,
                  [settings.CONTACT_NOTIFY_EMAIL], fail_silently=False)
    except Exception:  # never break the form because email failed
        logger.exception("Could not send contact notification email")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST":
        if _rate_limited(request):
            messages.error(request, "You have sent several messages recently. Please try again in an hour.")
            return redirect("contact:contact")
        if form.is_valid():
            if not form.is_spam():
                _notify(form.save())
            messages.success(request, "JazakAllah Khair! Your message has been sent. We will reply soon.")
            return redirect("contact:contact")
    return render(request, "contact/contact.html", {"form": form})
