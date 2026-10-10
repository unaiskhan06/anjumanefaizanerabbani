from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from . import instagram
from .forms import BulkImportForm
from .models import Category, Video
from .services import bulk_import


class VideoAdminForm(forms.ModelForm):
    """Custom form that populates the Type dropdown from Category names."""

    class Meta:
        model = Video
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")]
        choices += [(cat.name, cat.name) for cat in Category.objects.all()]
        self.fields["video_type"].widget = forms.Select(choices=choices)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_urdu", "slug", "sort_order", "video_count")
    list_editable = ("sort_order",)
    search_fields = ("name", "name_urdu")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Videos")
    def video_count(self, obj):
        return obj.videos.count()


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    form = VideoAdminForm
    list_display = ("thumb", "title", "category", "video_type", "published", "is_featured", "is_live",
                    "views", "created_at")
    list_display_links = ("thumb", "title")
    list_filter = ("category", "video_type", "published", "is_featured", "is_live")
    search_fields = ("title", "title_urdu", "artist", "youtube_id", "instagram_shortcode", "category__name")
    list_select_related = ("category",)
    list_per_page = 30
    date_hierarchy = "created_at"
    actions = ("make_published", "make_unpublished", "make_featured")
    readonly_fields = ("youtube_id", "instagram_shortcode", "slug", "thumbnail_preview", "player_preview", "views", "created_at")
    fieldsets = (
        ("Step 1 — Paste a YouTube or Instagram link, or upload a PDF", {"fields": ("youtube_url", "instagram_url", "pdf_file", "category", "video_type")}),
        ("Step 2 — Details (optional)", {
            "fields": ("title", "title_urdu", "artist", "description", "custom_thumbnail"),
            "description": "Leave the title blank and it will be fetched from YouTube when you save.",
        }),
        ("Visibility", {"fields": ("published", "is_featured", "is_live")}),
        ("Preview", {"fields": ("thumbnail_preview", "player_preview")}),
        ("Information", {"classes": ("collapse",), "fields": ("youtube_id", "instagram_shortcode", "slug", "views", "created_at")}),
    )

    class Media:
        js = ("js/admin_video.js",)

    @admin.display(description="")
    def thumb(self, obj):
        return obj.thumbnail_tag(96)

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.youtube_id and not obj.instagram_shortcode:
            return format_html('<div id="yt-thumb-preview">Paste a link above to see the thumbnail.</div>')
        return format_html('<div id="yt-thumb-preview">{}</div>', obj.thumbnail_tag(320))

    @admin.display(description="Player")
    def player_preview(self, obj):
        if obj.youtube_id:
            src = f"https://www.youtube-nocookie.com/embed/{obj.youtube_id}?rel=0"
            return format_html(
                '<div id="yt-player-preview" style="max-width:480px;aspect-ratio:16/9;background:#000;border-radius:8px;overflow:hidden">'
                '<iframe src="{}" title="Preview" style="width:100%;height:100%;border:0" loading="lazy" '
                'referrerpolicy="strict-origin-when-cross-origin" '
                'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>',
                src,
            )
        if obj.instagram_shortcode:
            src = instagram.embed_url(obj.instagram_shortcode, obj.instagram_url)
            return format_html(
                '<div id="yt-player-preview" style="max-width:360px;aspect-ratio:9/16;background:#000;border-radius:8px;overflow:hidden">'
                '<iframe src="{}" title="Preview" style="width:100%;height:100%;border:0" loading="lazy" '
                'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>',
                src,
            )
        return format_html('<div id="yt-player-preview">Paste a link above to preview the player.</div>')

    @admin.action(description="Publish selected videos")
    def make_published(self, request, queryset):
        self._bulk_update(request, queryset, "published", True, "published")

    @admin.action(description="Unpublish selected videos")
    def make_unpublished(self, request, queryset):
        self._bulk_update(request, queryset, "published", False, "unpublished")

    @admin.action(description="Mark selected as featured")
    def make_featured(self, request, queryset):
        self._bulk_update(request, queryset, "is_featured", True, "marked as featured")

    def _bulk_update(self, request, queryset, field, value, verb):
        # Save one by one so signals fire and the public cache is refreshed.
        count = 0
        for video in queryset:
            setattr(video, field, value)
            video.save(update_fields=[field])
            count += 1
        self.message_user(request, f"{count} video(s) {verb}.", messages.SUCCESS)

    # ---- bulk import page -------------------------------------------------
    def get_urls(self):
        custom = [path("bulk-import/", self.admin_site.admin_view(self.bulk_import_view),
                       name="videos_video_bulk_import")]
        return custom + super().get_urls()

    def bulk_import_view(self, request):
        if not self.has_add_permission(request):
            messages.error(request, "You do not have permission to add videos.")
            return redirect("admin:videos_video_changelist")
        report = None
        form = BulkImportForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            report = bulk_import(form.cleaned_data["links"], form.cleaned_data["category"],
                                 form.cleaned_data["video_type"], form.cleaned_data["published"])
            if report.created:
                messages.success(request, f"{len(report.created)} video(s) imported.")
            form = BulkImportForm(initial={"category": form.cleaned_data["category"],
                                           "video_type": form.cleaned_data["video_type"],
                                           "published": form.cleaned_data["published"]})
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Bulk import YouTube videos",
            "form": form,
            "report": report,
            "changelist_url": reverse("admin:videos_video_changelist"),
        }
        return TemplateResponse(request, "admin/videos/video/bulk_import.html", context)
