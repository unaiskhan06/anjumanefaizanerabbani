from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage

VALID = {"name": "Ahmed", "email": "ahmed@example.com", "phone": "+91 98765 43210",
         "subject": "Program booking", "message": "Assalamu Alaikum, please share details."}


@override_settings(CONTACT_NOTIFY_EMAIL="committee@example.com")
class ContactTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_valid_message_saved_and_emailed(self):
        r = self.client.post(reverse("contact:contact"), VALID, follow=True)
        self.assertContains(r, "Your message has been sent")
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_validation_errors(self):
        r = self.client.post(reverse("contact:contact"), {**VALID, "email": "nope", "message": "hi"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(r, "field-error")

    def test_honeypot_discards_spam(self):
        self.client.post(reverse("contact:contact"), {**VALID, "website": "http://spam"})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_rate_limit(self):
        for _ in range(5):
            self.client.post(reverse("contact:contact"), VALID)
        r = self.client.post(reverse("contact:contact"), VALID, follow=True)
        self.assertContains(r, "try again in an hour")
        self.assertEqual(ContactMessage.objects.count(), 5)
