from django.contrib import admin

from core.admin import image_preview

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "date", "time", "venue", "has_live")
    list_display_links = ("preview", "title")
    search_fields = ("title", "venue", "description")
    date_hierarchy = "date"
    readonly_fields = ("poster_preview",)

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.poster, 70)

    @admin.display(description="Poster preview")
    def poster_preview(self, obj):
        return image_preview(obj.poster, 300)

    @admin.display(boolean=True, description="Live link")
    def has_live(self, obj):
        return bool(obj.live_url)
