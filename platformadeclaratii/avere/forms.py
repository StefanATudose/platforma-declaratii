from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class FileFieldForm(forms.Form):
    file_field = MultipleFileField()


class IndividForm(forms.Form):
    nume = forms.CharField(max_length=50, required=False)
    init_tata = forms.CharField(max_length=8, required=False)
    prenume = forms.CharField(max_length=50, required=False)
    functie = forms.CharField(max_length=80, required=False)
    institutie = forms.CharField(max_length=80, required=False)

    def clean(self):
        cleaned_data = super().clean()
        nume = cleaned_data.get('nume')
        init_tata = cleaned_data.get('init_tata')
        prenume = cleaned_data.get('prenume')
        functie = cleaned_data.get('functie')
        institutie = cleaned_data.get('institutie')

        if not (nume or init_tata or prenume or functie or institutie):
            raise forms.ValidationError('At least one field must be completed.')

        return cleaned_data

class ClasamentForm(forms.Form):
    functie = forms.CharField(max_length=80, required=False)
    institutie = forms.CharField(max_length=80, required=False)
