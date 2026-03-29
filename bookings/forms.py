from django import forms
from .models import Booking
from stands.models import Stand

class BookingForm(forms.ModelForm):

    stands = forms.ModelMultipleChoiceField(
        queryset=Stand.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    arrival_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control"
            }
        )
    )

    departure_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control"
            }
        )
    )

    class Meta:
        model = Booking
        fields = "__all__"
