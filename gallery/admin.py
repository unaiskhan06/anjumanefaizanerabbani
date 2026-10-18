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
    list_display = ("cover_preview", "title", "artist", "player", "lyrics_status", "created_at")
    list_display_links = ("cover_preview", "title")
    search_fields = ("title", "artist", "description")
    list_per_page = 30
    readonly_fields = ("created_at", "cover_preview_large", "lyrics_preview_large")
    fieldsets = (
        ("Audio, Cover & Lyrics", {
            "fields": (
                "title", "artist", "audio_file",
                "image", "cover_preview_large",
                "lyrics_image", "lyrics_preview_large",
            ),
            "description": (
                "Provide an audio file, a cover image, a lyrics sheet image, or all three. "
                "The full lyrics image can be viewed by visitors on the main website."
            ),
        }),
        ("Details (Optional)", {
            "fields": ("description", "created_at"),
        }),
    )

    @admin.display(description="")
    def cover_preview(self, obj):
        if not obj.image:
            if obj.lyrics_image:
                return format_html('<img src="{}" width="60" style="border-radius:6px;aspect-ratio:1;object-fit:cover" loading="lazy" alt="Lyrics preview">', obj.lyrics_image.url)
            return "—"
        return format_html('<img src="{}" width="60" style="border-radius:6px;aspect-ratio:1;object-fit:cover" loading="lazy" alt="">', obj.image.url)

    @admin.display(description="Cover Preview")
    def cover_preview_large(self, obj):
        if not obj.image:
            return "No cover image uploaded."
        return format_html('<img src="{}" style="max-width:240px;border-radius:8px;object-fit:cover" loading="lazy" alt="">', obj.image.url)

    @admin.display(description="Lyrics Preview")
    def lyrics_preview_large(self, obj):
        if not obj.lyrics_image:
            return "No lyrics image uploaded."
        return format_html('<a href="{}" target="_blank" rel="noopener"><img src="{}" style="max-width:320px;border-radius:8px;object-fit:contain;border:1px solid #e2e8f0;padding:4px" loading="lazy" alt="Lyrics"><br><span style="font-size:0.8rem;color:#0284c7">Click to view full image in new tab ↗</span></a>', obj.lyrics_image.url, obj.lyrics_image.url)

    @admin.display(description="Lyrics")
    def lyrics_status(self, obj):
        if obj.lyrics_image:
            return format_html('<a href="{}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:4px;font-size:0.85rem;color:#0284c7;font-weight:600">📜 View image ↗</a>', obj.lyrics_image.url)
        return format_html('<span style="color:#94a3b8">—</span>')

    @admin.display(description="Playback")
    def player(self, obj):
        if not obj.audio_file:
            label = "Lyrics only" if (obj.lyrics_image and not obj.image) else "Image only"
            return format_html('<span style="color:#64748b;font-size:0.85rem;background:#f1f5f9;padding:2px 8px;border-radius:4px">{}</span>', label)
        return format_html('<audio controls preload="none" src="{}" style="height:32px"></audio>', obj.audio_file.url)
