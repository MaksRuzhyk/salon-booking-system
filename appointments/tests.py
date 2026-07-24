from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import AppointmentForm
from .models import Appointment, Procedure


class AppointmentFormTests(TestCase):
    def setUp(self):
        self.master = User.objects.create_user(username='master', password='test-pass-123')
        self.inactive_master = User.objects.create_user(
            username='inactive', password='test-pass-123', is_active=False
        )
        self.procedure = Procedure.objects.create(
            procedure_name='Haircut', duration_minutes=60
        )
        self.appointment_date = date(2026, 7, 22)

    def form_data(self, **overrides):
        data = {
            'master': self.master.pk,
            'date': self.appointment_date,
            'start_time': '10:00',
            'end_time': '11:00',
            'procedure': self.procedure.pk,
            'client_name': 'Client',
        }
        data.update(overrides)
        return data

    def test_end_time_must_be_later_than_start_time(self):
        form = AppointmentForm(data=self.form_data(end_time='09:30'))

        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)

    def test_overlapping_appointment_is_rejected(self):
        Appointment.objects.create(
            master=self.master,
            date=self.appointment_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            procedure=self.procedure,
        )

        form = AppointmentForm(
            data=self.form_data(start_time='10:30', end_time='11:30')
        )

        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)

    def test_adjacent_appointment_is_allowed(self):
        Appointment.objects.create(
            master=self.master,
            date=self.appointment_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            procedure=self.procedure,
        )

        form = AppointmentForm(
            data=self.form_data(start_time='11:00', end_time='12:00')
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_inactive_master_is_rejected(self):
        form = AppointmentForm(data=self.form_data(master=self.inactive_master.pk))

        self.assertFalse(form.is_valid())
        self.assertIn('master', form.errors)


class AppointmentViewTests(TestCase):
    def setUp(self):
        self.master = User.objects.create_user(username='master', password='test-pass-123')
        self.inactive_master = User.objects.create_user(
            username='inactive', password='test-pass-123', is_active=False
        )
        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='test-pass-123'
        )
        self.procedure = Procedure.objects.create(
            procedure_name='Haircut', duration_minutes=60
        )
        self.appointment = Appointment.objects.create(
            master=self.master,
            date=date(2026, 7, 22),
            start_time=time(10, 0),
            end_time=time(11, 0),
            procedure=self.procedure,
        )
        Appointment.objects.create(
            master=self.inactive_master,
            date=date(2026, 7, 22),
            start_time=time(12, 0),
            end_time=time(13, 0),
            procedure=self.procedure,
        )
        self.client.force_login(self.master)

    def test_calendar_lists_only_active_non_superusers_as_masters(self):
        response = self.client.get(reverse('appointments:index'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['masters'], [self.master])

    def test_api_hides_inactive_master_appointments(self):
        response = self.client.get(
            reverse('appointments:appointments_api'),
            {'start': '2026-07-22T00:00:00', 'end': '2026-07-23T00:00:00'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([event['id'] for event in response.json()], [self.appointment.pk])

    def test_mutating_endpoints_reject_get(self):
        urls = [
            reverse('appointments:add'),
            reverse('appointments:edit', args=[self.appointment.pk]),
            reverse('appointments:delete', args=[self.appointment.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)
