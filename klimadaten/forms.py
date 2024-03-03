from django import forms
from .models import Station


class CountryForm(forms.Form):
    country_choices = [(station, station) for station in
                       Station.objects.values_list('country', flat=True).distinct().order_by('country')]
    country_choices.insert(0, ('', 'Select a Country'))
    country = forms.ChoiceField(choices=country_choices, required=False, initial='SWITZERLAND')
