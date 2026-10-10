from django import forms

from .models import Category, Video


class BulkImportForm(forms.Form):
    links = forms.CharField(
        label="YouTube links",
        widget=forms.Textarea(attrs={"rows": 14, "cols": 90,
                                     "placeholder": "https://youtu.be/XXXXXXXXXXX\nhttps://www.youtube.com/watch?v=XXXXXXXXXXX"}),
        help_text="One link per line. Titles are fetched from YouTube automatically.",
    )
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="— choose a category —")
    video_type = forms.ChoiceField(choices=[], required=False)
    published = forms.BooleanField(required=False, initial=True, help_text="Untick to import as hidden drafts.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")]
        choices += [(cat.name, cat.name) for cat in Category.objects.all()]
        self.fields["video_type"].choices = choices

