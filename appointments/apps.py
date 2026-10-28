from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppointmentsConfig(AppConfig):
    name = 'appointments'
    verbose_name = _('Appointments and procedures')
