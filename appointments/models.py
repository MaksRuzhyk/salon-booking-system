from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Procedure(models.Model):
    procedure_name = models.CharField(max_length=255, verbose_name='Назва процедури')
    duration_minutes = models.IntegerField(verbose_name='Тривалість процедури у хвилинах')


    @property
    def duration_display(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours and minutes:
            return f'{hours:02d}:{minutes:02d}'
        elif hours:
            return f'{hours:02d}:{minutes:02d}'
        else:
            return f'{minutes:02d}хв'

    def __str__(self):
        return f'{self.procedure_name}'

    class Meta:
        verbose_name_plural = 'Процедури'
        verbose_name = 'Процедура'

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
        return f'{self.procedure}'

    class Meta:
        verbose_name_plural = 'Записи'
        verbose_name = 'Запис'