from django.urls import path
from .views import index, appointments_api, add_appointment, delete_appointment, edit_appointment
app_name = 'appointments'

urlpatterns = [
    path('', index, name='index'),
    path('appointments/api/', appointments_api, name='appointments_api'),
    path('create/', add_appointment, name='add'),
    path('delete/<int:appointment_id>/', delete_appointment, name='delete'),
    path('edit/<int:appointment_id>/', edit_appointment, name='edit'),
]