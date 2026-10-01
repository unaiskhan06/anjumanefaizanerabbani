"""
Import the latest uploads and Shorts from the channel's public RSS feeds.

    python manage.py import_channel                      # uses YOUTUBE_CHANNEL_ID from .env
    python manage.py import_channel --channel-id UC...   # or pass it explicitly
    python manage.py import_channel --category bayan --publish
    python manage.py import_channel --only-shorts --publish

Each feed contains the ~15 most recent items. Regular uploads are saved as unpublished drafts
(unless --publish) in --category (default: first category). YouTube Shorts are detected from the
channel's Shorts playlist, saved with type "Short" in the "Shorts" category, and appear in the
home page "YouTube Shorts" row once published. Run it on a schedule (cron / PythonAnywhere
"Tasks") to pick up new videos automatically.
"""
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from videos.models import Category, Video
from videos.youtube import watch_url

UPLOADS_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
# YouTube's automatic "Shorts" playlist for a channel: UCxxxx -> UUSHxxxx
SHORTS_FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id=UUSH{}"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


class Command(BaseCommand):
    help = "Import new uploads and Shorts from the YouTube channel RSS feeds."

    def add_arguments(self, parser):
        parser.add_argument("--channel-id", default=settings.YOUTUBE_CHANNEL_ID,
                            help="YouTube channel ID (starts with UC). Defaults to YOUTUBE_CHANNEL_ID.")
        parser.add_argument("--category", help="Slug of the category for regular videos (default: first category).")
        parser.add_argument("--shorts-category", default="shorts",
                            help="Slug of the category for Shorts (created if missing). Default: shorts")
        parser.add_argument("--publish", action="store_true", help="Publish immediately instead of saving drafts.")
        parser.add_argument("--only-shorts", action="store_true", help="Import Shorts only.")
        parser.add_argument("--no-shorts", action="store_true", help="Skip the Shorts feed.")
        parser.add_argument("--timeout", type=int, default=15)

    def handle(self, *args, **opts):
        channel_id = (opts["channel_id"] or "").strip()
        if not channel_id.startswith("UC"):
            raise CommandError("Set YOUTUBE_CHANNEL_ID in .env or pass --channel-id UCxxxxxxxx.")

        shorts = [] if opts["no_shorts"] else self._fetch(SHORTS_FEED.format(channel_id[2:]), opts["timeout"],
                                                           required=opts["only_shorts"])
        short_ids = {e["id"] for e in shorts}
        created = 0

        if shorts:
            shorts_category = self._shorts_category(opts["shorts_category"])
            # Fix videos that were added earlier as normal videos but are really Shorts.
            fixed = 0
            for video in Video.objects.filter(youtube_id__in=short_ids).exclude(video_type=Video.TYPE_SHORT):
                video.video_type = Video.TYPE_SHORT
                video.save(update_fields=["video_type"])
                fixed += 1
            if fixed:
                self.stdout.write(f"  ~ {fixed} existing video(s) marked as Shorts")
            created += self._create(shorts, shorts_category, Video.TYPE_SHORT, opts["publish"])

        if not opts["only_shorts"]:
            uploads = [e for e in self._fetch(UPLOADS_FEED.format(channel_id), opts["timeout"])
                       if e["id"] not in short_ids]
            created += self._create(uploads, self._category(opts["category"]), None, opts["publish"])

        state = "published" if opts["publish"] else "saved as drafts (unpublished)"
        self.stdout.write(self.style.SUCCESS(f"Done: {created} new video(s) {state}."))

    def _create(self, entries, category, kind, publish):
        existing = set(Video.objects.filter(youtube_id__in=[e["id"] for e in entries])
                       .values_list("youtube_id", flat=True))
        created = 0
        for entry in reversed(entries):  # oldest first so the newest ends up on top
            if entry["id"] in existing:
                continue
            video_type = kind or (Video.TYPE_SHORT if "#shorts" in entry["title"].lower() else Video.TYPE_FULL)
            Video.objects.create(
                youtube_url=watch_url(entry["id"]),
                title=entry["title"][:255],
                description=entry["description"],
                category=category,
                video_type=video_type,
                published=publish,
            )
            created += 1
            self.stdout.write(f"  + [{video_type}] {entry['title']}")
        return created

    def _category(self, slug):
        if slug:
            try:
                return Category.objects.get(slug=slug)
            except Category.DoesNotExist:
                raise CommandError(f"No category with slug '{slug}'.")
        category = Category.objects.exclude(slug="shorts").first()
        if category is None:
            category = Category.objects.create(name="Latest Uploads", name_urdu="تازہ اپلوڈز")
        return category

    def _shorts_category(self, slug):
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": "Shorts", "name_urdu": "شارٹس", "sort_order": 90,
                      "description": "Short vertical clips from our YouTube channel."},
        )
        return category

    def _fetch(self, url, timeout, required=True):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                root = ET.fromstring(response.read())
        except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError) as exc:
            if required:
                raise CommandError(f"Could not read the feed {url}: {exc}")
            self.stderr.write(f"  ! Skipped feed {url}: {exc}")
            return []

        entries = []
        for node in root.findall("atom:entry", NS):
            video_id = node.findtext("yt:videoId", default="", namespaces=NS)
            if not video_id:
                continue
            entries.append({
                "id": video_id,
                "title": (node.findtext("atom:title", default="", namespaces=NS) or video_id).strip(),
                "description": (node.findtext("media:group/media:description", default="", namespaces=NS) or "").strip(),
            })
        return entries
