from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))

    class Meta:
        model = Appointment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = User.objects.filter(is_active=True, is_superuser=False)

    def clean(self):
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            self.add_error(
                'end_time',
                'Час завершення повинен бути пізніше часу початку.',
            )
            return cleaned_data

        if master and date and start_time and end_time:
            overlapping = Appointment.objects.filter(
                master=master,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                self.add_error(
                    'start_time',
                    'У цього майстра вже є запис на вибраний час.',
                )

        return cleaned_data