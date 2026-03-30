from django import forms
from stands.models import Stand


class DashboardBookingForm(forms.Form):
    arrival_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )
    stand = forms.ModelChoiceField(
        queryset=Stand.objects.none(),
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        available_stands = kwargs.pop("available_stands", None)
        super().__init__(*args, **kwargs)

        if available_stands is not None:
            self.fields["stand"].queryset = available_stands.order_by("number")
