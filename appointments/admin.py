from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .forms import AppointmentForm
from django.contrib import admin
from .models import Appointment, Procedure


class AppointmentAdmin(UnfoldModelAdmin):
    form = AppointmentForm
    list_display = ('master', 'procedure','date', 'start_time', 'end_time', 'client_name')

class ProcedureAdmin(UnfoldModelAdmin):
    list_display = ('procedure_name', 'duration_minutes')

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Procedure, ProcedureAdmin)
