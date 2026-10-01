from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Video
from .services import bulk_import
from .youtube import extract_youtube_id

VID = "dQw4w9WgXcQ"


class ExtractIdTests(TestCase):
    def test_supported_formats(self):
        for url in [
            VID,
            f"https://www.youtube.com/watch?v={VID}",
            f"https://youtube.com/watch?feature=share&v={VID}&t=10",
            f"https://m.youtube.com/watch?v={VID}",
            f"https://youtu.be/{VID}?si=abc",
            f"youtu.be/{VID}",
            f"https://www.youtube.com/shorts/{VID}",
            f"https://www.youtube.com/embed/{VID}",
            f"https://www.youtube-nocookie.com/embed/{VID}?rel=0",
            f"https://www.youtube.com/live/{VID}?feature=share",
        ]:
            with self.subTest(url=url):
                self.assertEqual(extract_youtube_id(url), VID)

    def test_rejects_invalid(self):
        for url in ["", "hello", "https://vimeo.com/12345", "https://example.com/watch?v=" + VID,
                    "https://www.youtube.com/watch?v=short", "https://www.youtube.com/@channel"]:
            with self.subTest(url=url):
                self.assertIsNone(extract_youtube_id(url))


@mock.patch("videos.youtube.fetch_title", return_value="Fetched Title")
class VideoModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Naat Sharif")

    def test_category_slug(self, _):
        self.assertEqual(self.cat.slug, "naat-sharif")

    def test_save_extracts_id_fetches_title_and_slug(self, fetch):
        v = Video.objects.create(youtube_url=f"https://youtu.be/{VID}", category=self.cat)
        self.assertEqual(v.youtube_id, VID)
        self.assertEqual(v.title, "Fetched Title")
        self.assertEqual(v.slug, "fetched-title")
        self.assertEqual(v.thumbnail, f"https://img.youtube.com/vi/{VID}/hqdefault.jpg")
        fetch.assert_called_once()

    def test_unique_slugs(self, _):
        a = Video.objects.create(youtube_url="aaaaaaaaaaa", title="Same", category=self.cat)
        b = Video.objects.create(youtube_url="bbbbbbbbbbb", title="Same", category=self.cat)
        self.assertNotEqual(a.slug, b.slug)

    def test_clean_rejects_duplicate_and_invalid(self, _):
        Video.objects.create(youtube_url=VID, title="First", category=self.cat)
        dup = Video(youtube_url=f"https://www.youtube.com/watch?v={VID}", category=self.cat)
        with self.assertRaisesMessage(ValidationError, "already been added"):
            dup.full_clean()
        bad = Video(youtube_url="https://example.com", category=self.cat)
        with self.assertRaises(ValidationError):
            bad.full_clean()

    def test_shorts_url_sets_type(self, _):
        v = Video(youtube_url=f"https://youtube.com/shorts/{VID}", category=self.cat, title="S")
        v.full_clean()
        self.assertEqual(v.video_type, Video.TYPE_SHORT)

    def test_bulk_import_report(self, _):
        Video.objects.create(youtube_url="ccccccccccc", title="Existing", category=self.cat)
        report = bulk_import(f"https://youtu.be/{VID}\n{VID}\nnot a link\nccccccccccc\n\n", self.cat)
        self.assertEqual(len(report.created), 1)
        self.assertEqual(len(report.duplicates), 2)
        self.assertEqual(report.invalid, ["not a link"])


class ImportChannelTests(TestCase):
    def test_shorts_imported_with_type_and_category(self):
        from django.core.management import call_command
        Category.objects.create(name="Naat Sharif")
        feeds = {
            "playlist_id=UUSHabc": [{"id": "sssssssssss", "title": "A Short", "description": ""}],
            "channel_id=UCabc": [{"id": "sssssssssss", "title": "A Short", "description": ""},
                                 {"id": "fffffffffff", "title": "Full video", "description": ""}],
        }
        fetch = lambda self, url, timeout, required=True: next(v for k, v in feeds.items() if k in url)  # noqa: E731
        with mock.patch("videos.management.commands.import_channel.Command._fetch", fetch):
            call_command("import_channel", "--channel-id", "UCabc", "--publish", stdout=mock.MagicMock())
        short = Video.objects.get(youtube_id="sssssssssss")
        self.assertEqual((short.video_type, short.category.slug), (Video.TYPE_SHORT, "shorts"))
        self.assertEqual(short.watch_url, "https://www.youtube.com/shorts/sssssssssss")
        self.assertEqual(Video.objects.get(youtube_id="fffffffffff").video_type, Video.TYPE_FULL)
        self.assertEqual(Video.objects.count(), 2)


class OEmbedFallbackTests(TestCase):
    @mock.patch("urllib.request.urlopen", side_effect=OSError("offline"))
    def test_title_fallback_when_offline(self, _):
        cat = Category.objects.create(name="Bayan")
        v = Video.objects.create(youtube_url=VID, category=cat)
        self.assertEqual(v.title, f"Video {VID}")


class PublicViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="Naat Sharif", slug="naat-sharif")
        self.v1 = Video.objects.create(youtube_url="aaaaaaaaaaa", title="First Naat", category=self.cat)
        self.v2 = Video.objects.create(youtube_url="bbbbbbbbbbb", title="Second Naat", category=self.cat,
                                       title_urdu="دوسری نعت")
        self.hidden = Video.objects.create(youtube_url="ccccccccccc", title="Hidden", category=self.cat,
                                           published=False)

    def test_pages_render(self):
        urls = [
            reverse("core:home"), reverse("videos:categories"), self.cat.get_absolute_url(),
            reverse("videos:popular"), reverse("videos:all") + "?type=short", reverse("videos:search") + "?q=naat",
            reverse("core:playlists"), reverse("core:about"), reverse("events:list"), reverse("gallery:audio"),
            reverse("gallery:gallery"), reverse("contact:contact"), "/robots.txt", "/sitemap.xml",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_video_page_player_seo_and_views(self):
        url = self.v1.get_absolute_url()
        r = self.client.get(url)
        self.assertContains(r, "youtube-nocookie.com/embed/aaaaaaaaaaa?autoplay=1&amp;rel=0&amp;modestbranding=1")
        self.assertContains(r, '"@type": "VideoObject"')
        self.assertContains(r, 'property="og:image" content="https://img.youtube.com/vi/aaaaaaaaaaa/hqdefault.jpg"')
        self.client.get(url)
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.views, 1)  # counted once per session

    def test_unpublished_hidden(self):
        self.assertEqual(self.client.get(self.hidden.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("core:home")), "Hidden")

    def test_new_video_appears_immediately_on_home(self):
        self.client.get(reverse("core:home"))  # warm the cache
        Video.objects.create(youtube_url="ddddddddddd", title="Brand New Upload", category=self.cat)
        self.assertContains(self.client.get(reverse("core:home")), "Brand New Upload")

    def test_shorts_stay_out_of_category_rows(self):
        short = Video.objects.create(youtube_url="eeeeeeeeeee", title="A Short", category=self.cat,
                                     video_type=Video.TYPE_SHORT)
        r = self.client.get(reverse("core:home"))
        row = next(r for r in r.context["rows"] if r["id"] == "naat-sharif")
        self.assertNotIn(short, row["videos"])
        self.assertIn(short, next(r2 for r2 in r.context["rows"] if r2["id"] == "shorts")["videos"])
        r = self.client.get(self.cat.get_absolute_url())
        self.assertNotIn(short, r.context["page_obj"].object_list)
        self.assertIn(short, r.context["shorts_row"]["videos"])

    def test_announcements_section(self):
        import datetime, shutil, tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from django.utils import timezone
        from core.models import Announcement
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        settings_override = override_settings(MEDIA_ROOT=media)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        home = reverse("core:home")
        self.assertNotContains(self.client.get(home), "announcements-title")  # hidden when empty
        gif = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,"
               b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
        Announcement.objects.create(title="Urs Mubarak Notice", image=SimpleUploadedFile("a.gif", gif, "image/gif"))
        Announcement.objects.create(title="Old Notice", image=SimpleUploadedFile("b.gif", gif, "image/gif"),
                                    show_until=timezone.localdate() - datetime.timedelta(days=1))
        r = self.client.get(home)
        self.assertContains(r, "Urs Mubarak Notice")
        self.assertNotContains(r, "Old Notice")
        html = r.content.decode()
        self.assertLess(html.index("announcements-title"), html.index("chips-wrap"))

    def test_partner_channel_banner_on_home(self):
        from core.models import PartnerChannel
        PartnerChannel.objects.create(name="Ahmed Raza Rabbani", url="https://www.youtube.com/@ahmedrazarabbani786?si=x")
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, "Ahmed Raza Rabbani")
        self.assertContains(r, "https://www.youtube.com/@ahmedrazarabbani786?sub_confirmation=1")

    def test_search_and_suggest(self):
        r = self.client.get(reverse("videos:search"), {"q": "دوسری"})
        self.assertContains(r, "Second Naat")
        data = self.client.get(reverse("videos:suggest"), {"q": "first"}).json()
        self.assertEqual([x["title"] for x in data["results"]], ["First Naat"])

    def test_wrong_category_in_url_404(self):
        other = Category.objects.create(name="Bayan")
        self.assertEqual(self.client.get(reverse("videos:detail", args=[other.slug, self.v1.slug])).status_code, 404)


class AdminTests(TestCase):
    def test_default_admin_url_disabled(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.get("/manage/").status_code, 302)  # redirects to login

    @mock.patch("videos.youtube.fetch_title", return_value="Imported")
    def test_admin_screens_and_bulk_import(self, _):
        user = get_user_model().objects.create_superuser("boss", "b@example.com", "a-strong-pass-123")
        self.client.force_login(user)
        cat = Category.objects.create(name="Hamd")
        for url in ["/manage/", "/manage/videos/video/", "/manage/videos/video/add/", "/manage/videos/video/bulk-import/",
                    "/manage/core/sitesetting/", "/manage/contact/contactmessage/", "/manage/events/event/"]:
            with self.subTest(url=url):
                self.assertIn(self.client.get(url, follow=True).status_code, (200,))
        r = self.client.post("/manage/videos/video/bulk-import/",
                             {"links": f"{VID}\nbad line", "category": cat.pk, "video_type": "full", "published": "on"})
        self.assertContains(r, "1</strong> created")
        self.assertTrue(Video.objects.filter(youtube_id=VID).exists())
