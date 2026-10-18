import logging
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)

# Cloudinary standard/free tier raw asset upload limit is 10 MB (10,485,760 bytes).
CLOUDINARY_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@deconstructible
class SmartPDFStorage(Storage):
    """
    Smart hybrid storage for PDF documents:
    - If USE_CLOUDINARY is True and file size is <= 10MB, attempts upload to Cloudinary.
    - If file size exceeds 10MB (or if Cloudinary rejects due to account limits / errors),
      it transparently falls back to local FileSystemStorage.
    - Resolves URLs, open, exists, and delete checks dynamically based on where the file resides.
    """

    def __init__(self):
        self._local_storage = None
        self._cloudinary_storage = None

    @property
    def local_storage(self):
        if self._local_storage is None:
            self._local_storage = FileSystemStorage()
        return self._local_storage

    @property
    def cloudinary_storage(self):
        if self._cloudinary_storage is None and getattr(settings, "USE_CLOUDINARY", False):
            try:
                from cloudinary_storage.storage import RawMediaCloudinaryStorage
                self._cloudinary_storage = RawMediaCloudinaryStorage()
            except Exception as exc:
                logger.warning("Could not initialize RawMediaCloudinaryStorage: %s", exc)
                self._cloudinary_storage = None
        return self._cloudinary_storage

    def _get_file_size(self, content):
        size = getattr(content, "size", None)
        if size is not None:
            return size
        try:
            cur = content.tell()
            content.seek(0, os.SEEK_END)
            size = content.tell()
            content.seek(cur)
            return size
        except Exception:
            return None

    def _save(self, name, content):
        size = self._get_file_size(content)
        cloud = self.cloudinary_storage

        # If Cloudinary is configured and file fits within Cloudinary's 10MB limit:
        if cloud is not None and (size is None or size <= CLOUDINARY_MAX_BYTES):
            try:
                return cloud._save(name, content)
            except Exception as exc:
                logger.warning(
                    "Cloudinary upload failed for %s (%s). Falling back to local storage.",
                    name,
                    exc,
                )
                try:
                    content.seek(0)
                except Exception:
                    pass

        # If file is larger than 10MB or Cloudinary is not used / failed:
        return self.local_storage._save(name, content)

    def _open(self, name, mode="rb"):
        if self.local_storage.exists(name):
            return self.local_storage._open(name, mode=mode)
        if self.cloudinary_storage:
            try:
                return self.cloudinary_storage._open(name, mode=mode)
            except Exception:
                pass
        return self.local_storage._open(name, mode=mode)

    def exists(self, name):
        if self.local_storage.exists(name):
            return True
        if self.cloudinary_storage:
            try:
                return self.cloudinary_storage.exists(name)
            except Exception:
                return False
        return False

    def url(self, name):
        if not name:
            return ""
        if name.startswith("http://") or name.startswith("https://"):
            return name
        if self.local_storage.exists(name):
            return self.local_storage.url(name)
        if self.cloudinary_storage:
            try:
                return self.cloudinary_storage.url(name)
            except Exception:
                pass
        return self.local_storage.url(name)

    def delete(self, name):
        if self.local_storage.exists(name):
            self.local_storage.delete(name)
        if self.cloudinary_storage:
            try:
                self.cloudinary_storage.delete(name)
            except Exception:
                pass

    def get_available_name(self, name, max_length=None):
        return self.local_storage.get_available_name(name, max_length=max_length)

    def size(self, name):
        if self.local_storage.exists(name):
            return self.local_storage.size(name)
        if self.cloudinary_storage:
            try:
                return self.cloudinary_storage.size(name)
            except Exception:
                pass
        return None

    def path(self, name):
        if self.local_storage.exists(name):
            return self.local_storage.path(name)
        return self.local_storage.path(name)


def get_pdf_storage():
    return SmartPDFStorage()
