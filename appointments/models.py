from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _



class Procedure(models.Model):
    procedure_name = models.CharField(max_length=255, verbose_name=_('procedure name'))
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                                   verbose_name=_('duration in minutes'))

    @property
    def duration_display(self):
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours:
            return f'{hours:02d}:{minutes:02d}'
        return _('%(minutes)02d min') % {'minutes': minutes}

    def __str__(self):
        return self.procedure_name

    class Meta:
        verbose_name_plural = _('procedures')
        verbose_name = _('procedure')
        ordering = ['procedure_name']

class Appointment(models.Model):
    master = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('master'))
    date = models.DateField(verbose_name=_('date'))
    start_time = models.TimeField(verbose_name=_('start time'))
    end_time = models.TimeField(verbose_name=_('end time'))
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name=_('procedure'))
    client_name = models.CharField(max_length=255, blank=True, verbose_name=_('client name'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))

    @property
    def duration(self):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return end - start

    def __str__(self):
        return str(self.procedure)

    class Meta:
        verbose_name_plural = _('appointments')
        verbose_name = _('appointment')
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['master', 'date'], name='appointment_master_date_index'),
        ]