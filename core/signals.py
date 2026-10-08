"""Clear cached public data whenever the admin changes content, so edits show up immediately."""
from django.db.models.signals import post_delete, post_save

from events.models import Event
from videos.models import Category, Video

from .models import Announcement, Banner, DonationInfo, PartnerChannel, PlaylistLink, SiteSetting
from .utils import clear_public_cache


def _clear(**kwargs):
    clear_public_cache()


for model in (Video, Category, Banner, Announcement, PlaylistLink, PartnerChannel, SiteSetting, Event, DonationInfo):
    post_save.connect(_clear, sender=model, dispatch_uid=f"clear-cache-save-{model.__name__}")
    post_delete.connect(_clear, sender=model, dispatch_uid=f"clear-cache-delete-{model.__name__}")
