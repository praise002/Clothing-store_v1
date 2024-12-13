from django import forms

from apps.shop.models import Review

#required=False, doesn't print out value
class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        widget=forms.HiddenInput(attrs={"id": "star-rating"}),
    ) 
    text = forms.CharField(
        max_length=255,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": "5",
                "placeholder": "Enter your review",
                "style": "resize: none",
            }
        ),
    )

    class Meta:
        model = Review
        fields = ["rating", "text"]

# NOTE: WHEN REVIEW IS SUBMITTED FORM SHOULD BE CLOSED