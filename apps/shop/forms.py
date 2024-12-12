from django import forms

from apps.shop.models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(required=False)
    text = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "5", "placeholder": "Enter your review", 
                                     "style": "resize: none"}),
    )

    class Meta:
        model = Review
        fields = ["rating", "text"]