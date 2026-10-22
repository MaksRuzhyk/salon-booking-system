from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Procedure(models.Model):
    procedure_name = models.CharField(max_length=255, verbose_name='Назва процедури')
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                                   verbose_name='Тривалість процедури у хвилинах')

    @property
    def duration_display(self):
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours:
            return f'{hours:02d}:{minutes:02d}'
        return f'{minutes:02d}хв'

    def __str__(self):
        return self.procedure_name

    class Meta:
        verbose_name_plural = 'Процедури'
        verbose_name = 'Процедура'
        ordering = ['procedure_name']

class Appointment(models.Model):
    master = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Майстер')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Початок процедури')
    end_time = models.TimeField(verbose_name='Кінець процедури')
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name='Процедура')
    client_name = models.CharField(max_length=255, blank=True, verbose_name="Ім'я клієнта")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Час створення запису')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Час оновлення запису')

    @property
    def duration(self):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return end - start

    def __str__(self):
        return str(self.procedure)

    class Meta:
        verbose_name_plural = 'Записи'
        verbose_name = 'Запис'
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['master', 'date'], name='appointment_master_date_index'),
        ]