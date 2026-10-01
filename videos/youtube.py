"""Helpers for working with YouTube links, IDs and oEmbed metadata."""
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
PATH_PREFIXES = ("shorts", "embed", "live", "v", "e")


def extract_youtube_id(value):
    """
    Return the 11-character video ID from a YouTube link or bare ID, or None.

    Supports: watch?v=, youtu.be/, /shorts/, /embed/, /live/, /v/ and bare IDs.
    """
    if not value:
        return None
    value = value.strip()
    if ID_RE.match(value):
        return value
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    parts = [p for p in parsed.path.split("/") if p]

    candidate = None
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parts[0] if parts else None
    elif host in YOUTUBE_HOSTS:
        if parts[:1] == ["watch"] or not parts:
            candidate = urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        elif len(parts) >= 2 and parts[0] in PATH_PREFIXES:
            candidate = parts[1]
    return candidate if candidate and ID_RE.match(candidate) else None


def is_shorts_url(value):
    return "/shorts/" in (value or "")


def watch_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def embed_url(video_id, autoplay=True):
    params = "autoplay=1&rel=0&modestbranding=1" if autoplay else "rel=0&modestbranding=1"
    return f"https://www.youtube-nocookie.com/embed/{video_id}?{params}"


def thumbnail_url(video_id, quality="hqdefault"):
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"


def fetch_oembed(video_id, timeout=4):
    """Return the oEmbed dict for a video, or {} if YouTube is unreachable."""
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"format": "json", "url": watch_url(video_id)}
    )
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AnjumanSite)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("oEmbed lookup failed for %s: %s", video_id, exc)
        return {}


def fetch_title(video_id, timeout=4):
    return (fetch_oembed(video_id, timeout).get("title") or "").strip()
