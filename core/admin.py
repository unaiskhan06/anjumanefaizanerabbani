from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import Announcement, Banner, DonationInfo, PartnerChannel, PlaylistLink, SiteSetting

admin.site.site_header = f"{settings.SITE_DISPLAY_NAME} — Admin"
admin.site.site_title = f"{settings.SITE_NAME} admin"
admin.site.index_title = "Manage the website"
admin.site.site_url = "/"


def image_preview(image, width=120):
    if not image:
        return "—"
    return format_html('<img src="{}" width="{}" style="border-radius:6px;object-fit:cover" loading="lazy" alt="">',
                       image.url, width)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "program_label", "sort_order", "active")
    list_display_links = ("preview", "title")
    list_editable = ("sort_order", "active")
    list_filter = ("active",)
    readonly_fields = ("preview_large",)

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.image, 110)

    @admin.display(description="Preview")
    def preview_large(self, obj):
        return image_preview(obj.image, 420)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "show_until", "sort_order", "active", "created_at")
    list_display_links = ("preview", "title")
    list_editable = ("sort_order", "active")
    list_filter = ("active",)
    search_fields = ("title",)
    fields = ("title", "image", "preview_large", "link_url", "show_until", "sort_order", "active")
    readonly_fields = ("preview_large",)

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.image, 140)

    @admin.display(description="Preview")
    def preview_large(self, obj):
        return image_preview(obj.image, 480)


@admin.register(PlaylistLink)
class PlaylistLinkAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "url", "sort_order")
    list_display_links = ("preview", "name")
    list_editable = ("sort_order",)

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.image, 90)


@admin.register(PartnerChannel)
class PartnerChannelAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "url", "sort_order", "active")
    list_display_links = ("preview", "name")
    list_editable = ("sort_order", "active")

    @admin.display(description="")
    def preview(self, obj):
        return image_preview(obj.image, 56)


@admin.register(DonationInfo)
class DonationInfoAdmin(admin.ModelAdmin):
    list_display = ("qr_preview", "title", "upi_id", "active", "updated_at")
    list_display_links = ("qr_preview", "title")
    list_editable = ("active",)
    list_filter = ("active",)
    readonly_fields = ("qr_preview_large", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "title_urdu", "description")}),
        ("QR Code & UPI", {"fields": ("qr_image", "qr_preview_large", "upi_id")}),
        ("Footer", {"fields": ("footer_note",)}),
        ("Status", {"fields": ("active", "created_at", "updated_at")}),
    )

    @admin.display(description="")
    def qr_preview(self, obj):
        return image_preview(obj.qr_image, 80)

    @admin.display(description="QR preview")
    def qr_preview_large(self, obj):
        return image_preview(obj.qr_image, 280)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("committee_name", "tagline")}),
        ("Social links", {"fields": ("youtube_url", "facebook_url", "instagram_url")}),
        ("Contact details", {"fields": ("whatsapp_number", ("phone_label", "phone"), ("phone2_label", "phone2"),
                                        "email", "address",
                                        ("map1_url", "map1_label"), ("map2_url", "map2_label"))}),
        ("Monthly schedule", {"fields": ("monthly_schedule",)}),
        ("About page", {"fields": ("about_text", "mission", "vision")}),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSetting.load()
        return redirect(reverse("admin:core_sitesetting_change", args=[obj.pk]))
