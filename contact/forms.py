import re

from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Honeypot: hidden from people with CSS, bots tend to fill it in.
    website = forms.CharField(required=False, label="Leave this field empty",
                              widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}))

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "Optional"}),
            "subject": forms.TextInput(attrs={"placeholder": "How can we help?"}),
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "Write your message…"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter your name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not re.fullmatch(r"[+\d][\d\s\-()]{6,20}", phone):
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Your message is a little short. Please add a few more words.")
        return message

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
