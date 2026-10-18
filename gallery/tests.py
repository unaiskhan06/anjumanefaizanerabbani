import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AudioTrack

TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class AudioTrackModelTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.temp_media,
            STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                      "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_audio_only_is_valid(self):
        audio = SimpleUploadedFile("sample.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x00", content_type="audio/mpeg")
        track = AudioTrack(title="Naat 1", audio_file=audio)
        track.full_clean()
        track.save()
        self.assertTrue(track.audio_file)
        self.assertFalse(track.image)
        self.assertFalse(track.lyrics_image)

    def test_image_only_is_valid(self):
        img = SimpleUploadedFile("cover.gif", TINY_GIF, content_type="image/gif")
        track = AudioTrack(title="Naat Poster", image=img)
        track.full_clean()
        track.save()
        self.assertFalse(track.audio_file)
        self.assertTrue(track.image)

    def test_lyrics_only_is_valid(self):
        lyrics = SimpleUploadedFile("lyrics.gif", TINY_GIF, content_type="image/gif")
        track = AudioTrack(title="Kalaam Lyrics Sheet", lyrics_image=lyrics)
        track.full_clean()
        track.save()
        self.assertFalse(track.audio_file)
        self.assertFalse(track.image)
        self.assertTrue(track.lyrics_image)

    def test_all_three_audio_cover_and_lyrics_valid(self):
        audio = SimpleUploadedFile("sample.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x00", content_type="audio/mpeg")
        img = SimpleUploadedFile("cover.gif", TINY_GIF, content_type="image/gif")
        lyrics = SimpleUploadedFile("lyrics.gif", TINY_GIF, content_type="image/gif")
        track = AudioTrack(title="Complete Naat", audio_file=audio, image=img, lyrics_image=lyrics)
        track.full_clean()
        track.save()
        self.assertTrue(track.audio_file)
        self.assertTrue(track.image)
        self.assertTrue(track.lyrics_image)

    def test_empty_track_raises_validation_error(self):
        track = AudioTrack(title="Empty Track")
        with self.assertRaises(ValidationError):
            track.full_clean()


class AudioPageViewTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.temp_media,
            STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                      "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_audio_page_renders_playable_image_only_and_lyrics(self):
        audio = SimpleUploadedFile("track.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x00", content_type="audio/mpeg")
        img = SimpleUploadedFile("cover.gif", TINY_GIF, content_type="image/gif")
        lyrics = SimpleUploadedFile("lyrics.gif", TINY_GIF, content_type="image/gif")

        t1 = AudioTrack.objects.create(title="Playable Track", audio_file=audio)
        t2 = AudioTrack.objects.create(title="Image Track", image=img)
        t3 = AudioTrack.objects.create(title="Track with Lyrics", audio_file=audio, lyrics_image=lyrics)

        res = self.client.get(reverse("gallery:audio"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Playable Track")
        self.assertContains(res, "Image Track")
        self.assertContains(res, "Track with Lyrics")
        self.assertContains(res, "data-no-audio")
        self.assertContains(res, "data-ap-viewer")
        self.assertContains(res, "data-ap-zoom-in")
        self.assertContains(res, "data-ap-zoom-out")
        self.assertContains(res, "data-ap-audio-section")


class AudioTrackAdminTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.temp_media,
            STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                      "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
        )
        self.settings_override.enable()
        self.user = get_user_model().objects.create_superuser("adminuser", "admin@example.com", "pass12345678")
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_admin_pages_render(self):
        lyrics = SimpleUploadedFile("lyrics.gif", TINY_GIF, content_type="image/gif")
        track = AudioTrack.objects.create(title="Admin Test Track", lyrics_image=lyrics)
        res = self.client.get("/manage/gallery/audiotrack/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Admin Test Track")
        self.assertContains(res, "View image")

        res_change = self.client.get(f"/manage/gallery/audiotrack/{track.pk}/change/")
        self.assertEqual(res_change.status_code, 200)
        self.assertContains(res_change, "Lyrics image")
