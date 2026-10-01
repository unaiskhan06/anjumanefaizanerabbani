from django.contrib import admin
from django.utils.html import format_html

from core.admin import image_preview

from .models import AudioTrack, GalleryImage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "caption", "created_at")
    list_display_links = ("preview", "caption")
    search_fields = ("caption",)
    readonly_fields = ("preview_large",)
    list_per_page = 40

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.image, 90)

    @admin.display(description="Preview")
    def preview_large(self, obj):
        return image_preview(obj.image, 400)


@admin.register(AudioTrack)
class AudioTrackAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "player", "created_at")
    search_fields = ("title", "artist")

    @admin.display(description="Listen")
    def player(self, obj):
        if not obj.audio_file:
            return "—"
        return format_html('<audio controls preload="none" src="{}" style="height:32px"></audio>', obj.audio_file.url)
