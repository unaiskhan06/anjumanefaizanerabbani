"""
Fill the database with demo content so the site looks complete on first run.

    python manage.py seed_demo                 # categories, videos, banners, events, settings, gallery
    python manage.py seed_demo --no-gallery    # skip importing photos from the assets folder
    python manage.py seed_demo --assets PATH   # folder with "home page images" and "gallery" sub-folders

Safe to run more than once: existing rows are kept and nothing is duplicated.
"""
import datetime
import urllib.request
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.images import optimized_jpeg, placeholder_jpeg
from core.models import Banner, PartnerChannel, PlaylistLink, SiteSetting
from core.utils import clear_public_cache
from events.models import Event
from gallery.models import GalleryImage
from videos.models import Category, Video

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
CHANNEL = "https://www.youtube.com/@anjumanefaizanerabbani"
PARTNER_CHANNELS = [
    {"name": "Ahmed Raza Rabbani", "url": "https://www.youtube.com/@ahmedrazarabbani786",
     "tagline": "Islamic naat, kalam and manqabat — subscribe and turn on notifications.",
     "avatar": "https://yt3.googleusercontent.com/5F4_WzxBrBKZz5akVjPJvGRw2c3veW5Wlg2JeY9zC9YgSoiZBdLrmhvxeAqKsn6IU5340UoVvDQ=s240-c-k-c0x00ffffff-no-rj"},
]

CATEGORIES = [
    ("Naat Sharif", "نعت شریف", "naat-sharif", "Naat Sharif in praise of the Beloved Prophet ﷺ."),
    ("Hamd", "حمد", "hamd", "Hamd — praise of Allah Ta'ala."),
    ("Bayan", "بیان", "bayan", "Bayanaat and speeches by respected Ulama."),
    ("Tasawwuf", "تصوف", "tasawwuf", "Talks and gatherings on Tasawwuf and spirituality."),
    ("Kids Special", "بچوں کے لیے", "kids-special", "Naat and programs presented by children."),
    ("Quran o Hadees", "قرآن و حدیث", "quran-o-hadees", "Tilawat, Dars-e-Quran and Hadees."),
]

MEELAD = "Jashn E Eid E Meelad Un Nabi (S.A.W) 2026"
# Real public videos from the ANJUMANEFAIZANERABBANI channel (oldest first).
VIDEOS = [
    ("74ossg1IDQs", f"{MEELAD} | Day 3", "naat-sharif", "full", ""),
    ("Hx-XRs-vIfo", f"{MEELAD} | Day 4", "hamd", "full", ""),
    ("YL5bjqsRmhk", f"{MEELAD} | Day 5", "tasawwuf", "full", ""),
    ("qOSbebe37Q8", f"{MEELAD} | Day 6", "quran-o-hadees", "full", ""),
    ("VgSGxLGniJ4", f"{MEELAD} | Day 7", "kids-special", "kids", ""),
    ("n7RduX2rSjg", f"{MEELAD} | Day 8", "naat-sharif", "full", ""),
    ("0WGJIWGPJ4k", f"{MEELAD} | Day 9", "bayan", "full", ""),
    ("ZTva-JJ2fC8", f"{MEELAD} | Day 10", "naat-sharif", "full", ""),
    ("_NrwAAi1lmk", f"{MEELAD} | Day 11", "bayan", "full", ""),
    ("hzH5F8Lm0mI", f"{MEELAD} | Day 12", "naat-sharif", "full", ""),
    ("mxYYTLrLbvs", "Eid E Meelad Un Nabi (S.A.W) 2026 | Bayaan", "bayan", "full",
     "Hazrath Allama Dr Sayyed Hamid Rabbani Saheb Qibla"),
    ("dxkBFsJGHP0", f"{MEELAD} | 1501th Jashn — Highlights", "naat-sharif", "full", ""),
]
FEATURED = {"mxYYTLrLbvs", "dxkBFsJGHP0", "hzH5F8Lm0mI"}

BANNERS = [
    ("Jashn-e-Eid-e-Meelad-un-Nabi ﷺ 2026", "1501th Celebration",
     "Watch every day of the Mehfil — Naat Sharif, Bayan and Dua — right here.", "/category/naat-sharif/"),
    ("Weekly Mehfil-e-Naat & Zikr", "Every Week",
     "Join the gathering in Chennai or watch the live stream from anywhere.", "/events/"),
    ("Bayanaat of the Ulama", "Bayan",
     "Listen to heart-touching bayanaat on love of the Prophet ﷺ and good character.", "/category/bayan/"),
]

ABOUT = (
    "Anjuman-e-Faizan-e-Rabbani is a community committee based in Chennai, devoted to spreading the love "
    "of Allah Ta'ala and His Beloved Prophet ﷺ through Naat Sharif, Hamd, Bayan and spiritual gatherings.\n\n"
    "Every year the Anjuman organises the Jashn-e-Eid-e-Meelad-un-Nabi ﷺ along with regular Mehfils, "
    "and shares the programs on our YouTube channel ANJUMANEFAIZANERABBANI so that families everywhere can "
    "take part."
)
MISSION = ("To keep the tradition of Naat, Zikr and learning alive, bring the community together in "
           "remembrance of Allah and His Messenger ﷺ, and make these blessed programs easy to watch for everyone.")
VISION = ("A united, well-mannered community — young and old — connected to the Quran, the Sunnah and the "
          "teachings of the Awliya, with every home reached by the message of love and peace.")
SCHEDULE = "Thursday after Isha — Mehfil-e-Naat & Zikr\nSunday 7 PM — Dars-e-Quran o Hadees\nMonthly — Gyarvi Sharif Mehfil"


class Command(BaseCommand):
    help = "Create demo categories, videos, banners, events, playlists, site settings and gallery photos."

    def add_arguments(self, parser):
        parser.add_argument("--assets", default=str(Path(settings.BASE_DIR) / "asserts"),
                            help="Folder containing 'home page images' and 'gallery' sub-folders.")
        parser.add_argument("--no-gallery", action="store_true", help="Do not import gallery photos.")

    def handle(self, *args, **opts):
        assets = Path(opts["assets"])
        home_images = self._images(assets / "home page images")
        with transaction.atomic():
            self._settings()
            categories = self._categories()
            self._videos(categories)
            self._banners(home_images)
            self._events(home_images)
            self._playlists()
            self._partner_channels()
        if not opts["no_gallery"]:
            self._gallery(self._images(assets / "gallery"))
        clear_public_cache()
        self.stdout.write(self.style.SUCCESS("Demo data ready. Open http://127.0.0.1:8000/ to see the site."))

    # ------------------------------------------------------------------
    def _images(self, folder):
        if not folder.is_dir():
            return []
        return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)

    def _settings(self):
        site = SiteSetting.load()
        defaults = {
            "committee_name": "Anjuman E Faizan E Rabbani | Chennai",
            "youtube_url": CHANNEL,
            "whatsapp_number": "919791054168",
            "phone_label": "Committee Sadar",
            "phone": "+91 95512 23117",
            "phone2_label": "Committee Admin",
            "phone2": "+91 97910 54168",
            "email": "anjumanefaizanerabbani@gmail.com",
            "address": "Chennai, Tamil Nadu, India",
            "weekly_schedule": SCHEDULE,
            "about_text": ABOUT,
            "mission": MISSION,
            "vision": VISION,
        }
        changed = [f for f, v in defaults.items() if not getattr(site, f)]
        for field in changed:
            setattr(site, field, defaults[field])
        site.save()
        self.stdout.write(f"Site settings: {len(changed)} empty field(s) filled.")

    def _categories(self):
        result = {}
        for order, (name, urdu, slug, desc) in enumerate(CATEGORIES):
            obj, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "name_urdu": urdu, "description": desc, "sort_order": order})
            result[slug] = obj
        self.stdout.write(f"Categories: {len(result)}")
        return result

    def _videos(self, categories):
        now = timezone.now()
        created = 0
        total = len(VIDEOS)
        for i, (vid, title, cat, kind, artist) in enumerate(VIDEOS):
            if Video.objects.filter(youtube_id=vid).exists():
                continue
            video = Video.objects.create(
                youtube_url=f"https://www.youtube.com/watch?v={vid}", title=title, category=categories[cat],
                video_type=kind, artist=artist, is_featured=vid in FEATURED, published=True,
                description=f"{title}\n\nOrganised by Anjuman E Faizan E Rabbani, Chennai.",
            )
            # Stagger dates so "latest" ordering and previous/next links look natural.
            Video.objects.filter(pk=video.pk).update(created_at=now - datetime.timedelta(hours=(total - i) * 20))
            created += 1
        self.stdout.write(f"Videos: {created} created")

    def _banners(self, images):
        if Banner.objects.exists():
            self.stdout.write("Banners: already present, skipped")
            return
        for order, (title, label, desc, link) in enumerate(BANNERS):
            banner = Banner(title=title, program_label=label, description=desc, link_url=link, sort_order=order)
            content = optimized_jpeg(images[order], 1920) if order < len(images) else placeholder_jpeg(title)
            banner.image.save(f"banner-{order + 1}.jpg", content, save=False)
            banner.save()
        self.stdout.write(f"Banners: {len(BANNERS)} created")

    def _events(self, images):
        if Event.objects.exists():
            self.stdout.write("Events: already present, skipped")
            return
        today = timezone.localdate()
        upcoming = Event(
            title="Monthly Mehfil-e-Zikr o Naat",
            date=today + datetime.timedelta(days=14), time=datetime.time(21, 0),
            venue="Chennai, Tamil Nadu",
            description="An evening of Naat Sharif, Zikr and Dua. Everyone is welcome with family.",
            live_url=CHANNEL + "/streams",
        )
        past = Event(
            title="Jashn-e-Eid-e-Meelad-un-Nabi ﷺ 2026 — Day 12",
            date=today - datetime.timedelta(days=20), time=datetime.time(20, 30),
            venue="Chennai, Tamil Nadu",
            description="The 1501th Jashn-e-Eid-e-Meelad-un-Nabi ﷺ celebration.",
            live_url="https://www.youtube.com/watch?v=hzH5F8Lm0mI",
        )
        for event, image in ((upcoming, images[3:4]), (past, images[4:5])):
            if image:
                event.poster.save(f"event-{event.date:%Y%m%d}.jpg", optimized_jpeg(image[0], 1200), save=False)
            event.save()
        self.stdout.write("Events: 2 created")

    def _playlists(self):
        links = [
            ("ANJUMANEFAIZANERABBANI — YouTube channel", CHANNEL),
            ("All videos", CHANNEL + "/videos"),
            ("Live streams", CHANNEL + "/streams"),
            ("Shorts", CHANNEL + "/shorts"),
            ("All playlists", CHANNEL + "/playlists"),
        ] + [(f"{c['name']} — YouTube channel", c["url"]) for c in PARTNER_CHANNELS]
        for order, (name, url) in enumerate(links):
            PlaylistLink.objects.get_or_create(url=url, defaults={"name": name, "sort_order": order})
        self.stdout.write(f"Playlists: {len(links)}")

    def _partner_channels(self):
        for order, data in enumerate(PARTNER_CHANNELS):
            channel, created = PartnerChannel.objects.get_or_create(
                url=data["url"], defaults={"name": data["name"], "tagline": data["tagline"], "sort_order": order})
            if created and not channel.image:
                try:
                    request = urllib.request.Request(data["avatar"], headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(request, timeout=10) as response:
                        picture = optimized_jpeg(BytesIO(response.read()), 240, 88)
                    channel.image.save(f"{channel.url.rsplit('@', 1)[-1]}.jpg", picture, save=True)
                except (OSError, ValueError) as exc:
                    self.stderr.write(f"  ! Could not download the picture for {channel.name}: {exc}")
        self.stdout.write(f"Partner channels: {len(PARTNER_CHANNELS)}")

    def _gallery(self, images):
        if not images:
            self.stdout.write("Gallery: no assets folder found, skipped")
            return
        if GalleryImage.objects.exists():
            self.stdout.write("Gallery: already has photos, skipped")
            return
        self.stdout.write(f"Gallery: importing {len(images)} photos (resizing, please wait)...")
        for n, path in enumerate(images, 1):
            item = GalleryImage()
            item.image.save(f"photo-{n:03d}.jpg", optimized_jpeg(path, 1600), save=True)
        self.stdout.write(f"Gallery: {len(images)} photos imported")
