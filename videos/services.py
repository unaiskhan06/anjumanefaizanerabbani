from dataclasses import dataclass, field

from .models import Video
from .youtube import extract_youtube_id, is_shorts_url


@dataclass
class ImportReport:
    created: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    invalid: list = field(default_factory=list)


def bulk_import(text, category, video_type=Video.TYPE_FULL, published=True):
    """Create one video per line of `text`. Returns an ImportReport."""
    report = ImportReport()
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        video_id = extract_youtube_id(line)
        if not video_id:
            report.invalid.append(line)
            continue
        existing = Video.objects.filter(youtube_id=video_id).first()
        if video_id in seen or existing:
            report.duplicates.append(f"{line} (already added as “{existing}”)" if existing else line)
            continue
        seen.add(video_id)
        kind = Video.TYPE_SHORT if is_shorts_url(line) and video_type == Video.TYPE_FULL else video_type
        video = Video(youtube_url=line, category=category, video_type=kind, published=published)
        video.save()
        report.created.append(video)
    return report
