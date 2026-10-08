"""Helpers for Instagram reel/post shortcodes and embed URLs."""
import re
import urllib.parse

SHORTCODE_RE = re.compile(r"^[A-Za-z0-9_-]{7,}$")
VALID_PATH_PREFIXES = ("p", "reel", "reels", "tv")


def extract_shortcode(value):
    """Return the Instagram shortcode from a reel/post URL, or None."""
    if not value:
        return None
    value = value.strip()
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if "instagram.com" not in host and "instagr.am" not in host:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] in VALID_PATH_PREFIXES:
        candidate = parts[1]
    elif len(parts) == 1:
        candidate = parts[0]
    else:
        return None
    return candidate if SHORTCODE_RE.match(candidate) else None


def embed_url(shortcode, original_url=""):
    """Instagram embed iframe URL. Reels use /reel/; older posts use /p/."""
    prefix = "p" if "/p/" in (original_url or "") else "reel"
    return f"https://www.instagram.com/{prefix}/{shortcode}/embed/"


def watch_url(shortcode):
    return f"https://www.instagram.com/reel/{shortcode}/"
