from django import forms
from django.utils import timezone
from .models import FlowRate, PfasResult

class MaxFlowRateUpdateForm(forms.ModelForm):
    class Meta:
        model = FlowRate
        fields = ['flow_rate', 'unit']

class AnnualProductionForm(forms.Form):
    year = forms.IntegerField(widget=forms.HiddenInput(), initial=2023)
    flow_rate = forms.FloatField(required=True)
    unit = forms.ChoiceField(
        choices=[('mgd', 'MGD (Million Gallons per Day)'),
                 ('gpm', 'GPM (Gallons per Year)'),
                 ('gpy', 'GPY (Gallons per Year)'),
                 ('afpy', 'AFPY (Acre-feet per Year)')]
    )

class PfasResultUpdateForm(forms.ModelForm):
    """
    Form for updating PFAS result details.
    Includes all relevant fields for PFAS data entry and editing.
    """
    class Meta:
        model = PfasResult
        fields = [
            'analyte',
            'result',
            'unit',
            'sampling_date',
            'analysis_date',
            'lab_sample_id',
        ]

        widgets = {
            'analyte': forms.Select(choices=[
                ('', 'Select analyte'),
                ('PFBA', 'PFBA'),
                ('PFBS', 'PFBS'),
                ('PFHxS', 'PFHxS'),
                ('PFNA', 'PFNA'),
                ('PFDA', 'PFDA'),
                ('PFOA', 'PFOA'),
                ('PFOS', 'PFOS'),
            ]),
            'sampling_date': forms.DateInput(attrs={'type': 'date'}),
            'analysis_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_result(self):
        result = self.cleaned_data.get('result')
        if result is None:
            raise forms.ValidationError("Result is required and must be a valid number.")
        
        return result

    def clean_lab_sample_id(self):
        lab_sample_id = self.cleaned_data.get('lab_sample_id')
        if not lab_sample_id:
            raise forms.ValidationError("Lab Sample ID is required.")
        return lab_sample_id
    
    def clean_sampling_date(self):
        sampling_date = self.cleaned_data.get('sampling_date')
        if sampling_date and sampling_date > timezone.now().date():
            raise forms.ValidationError("Sampling date cannot be in the future.")
        return sampling_date

    def clean_analysis_date(self):
        analysis_date = self.cleaned_data.get('analysis_date')
        sampling_date = self.cleaned_data.get('sampling_date')

        if analysis_date:
            if sampling_date and analysis_date < sampling_date:
                raise forms.ValidationError("Analysis date cannot be before the sampling date.")
            if analysis_date > timezone.now().date():
                raise forms.ValidationError("Analysis date cannot be in the future.")
        return analysis_date