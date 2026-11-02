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
        self.assertEqual(response.json()[0]['title'], self.procedure.procedure_name)
        self.assertEqual(
            response.json()[0]['extendedProps']['client_name'],
            self.appointment.client_name,
        )

    def test_mutating_endpoints_reject_get(self):
        urls = [
            reverse('appointments:add'),
            reverse('appointments:edit', args=[self.appointment.pk]),
            reverse('appointments:delete', args=[self.appointment.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_api_requires_start_and_end(self):
        response = self.client.get(reverse('appointments:appointments_api'))

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_api_rejects_invalid_dates(self):
        cases = [
            {'start': 'not-a-date', 'end': '2026-07-23T00:00:00'},
            {'start': '2026-02-30T00:00:00', 'end': '2026-03-01T00:00:00'},
        ]
        for params in cases:
            with self.subTest(params=params):
                response = self.client.get(
                    reverse('appointments:appointments_api'), params
                )
                self.assertEqual(response.status_code, 400)

    def test_api_rejects_non_numeric_master_id(self):
        response = self.client.get(
            reverse('appointments:appointments_api'),
            {
                'start': '2026-07-22T00:00:00',
                'end': '2026-07-23T00:00:00',
                'master_id': 'abc',
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_api_filters_by_master_id(self):
        other_master = User.objects.create_user(username='other', password='test-pass-123')
        Appointment.objects.create(
            master=other_master,
            date=date(2026, 7, 22),
            start_time=time(14, 0),
            end_time=time(15, 0),
            procedure=self.procedure,
        )

        response = self.client.get(
            reverse('appointments:appointments_api'),
            {
                'start': '2026-07-22T00:00:00',
                'end': '2026-07-23T00:00:00',
                'master_id': self.master.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([event['id'] for event in response.json()], [self.appointment.pk])

    def other_master_appointment(self):
        other = User.objects.create_user(username='other', password='test-pass-123')
        return Appointment.objects.create(
            master=other,
            date=date(2026, 7, 22),
            start_time=time(15, 0),
            end_time=time(16, 0),
            procedure=self.procedure,
        )

    def test_master_sees_only_own_appointments_in_api(self):
        self.other_master_appointment()

        response = self.client.get(
            reverse('appointments:appointments_api'),
            {'start': '2026-07-22T00:00:00', 'end': '2026-07-23T00:00:00'},
        )

        self.assertEqual([event['id'] for event in response.json()], [self.appointment.pk])

    def test_staff_sees_all_masters(self):
        other = self.other_master_appointment().master
        self.client.force_login(self.superuser)

        response = self.client.get(reverse('appointments:index'))

        self.assertQuerySetEqual(
            response.context['masters'], [self.master, other], ordered=False
        )

    def test_master_cannot_edit_other_masters_appointment(self):
        appointment = self.other_master_appointment()

        response = self.client.post(
            reverse('appointments:edit', args=[appointment.pk]),
            {'client_name': 'Hacked'},
        )

        self.assertEqual(response.status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.client_name, '')

    def test_master_cannot_delete_other_masters_appointment(self):
        appointment = self.other_master_appointment()

        response = self.client.post(reverse('appointments:delete', args=[appointment.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_master_cannot_create_appointment_for_other_master(self):
        other = User.objects.create_user(username='other', password='test-pass-123')

        response = self.client.post(reverse('appointments:add'), {
            'master': other.pk,
            'date': '2026-07-23',
            'start_time': '10:00',
            'end_time': '11:00',
            'procedure': self.procedure.pk,
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('master', response.json()['errors'])

    def test_master_can_delete_own_appointment(self):
        response = self.client.post(reverse('appointments:delete', args=[self.appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.filter(pk=self.appointment.pk).exists())

    def test_staff_can_delete_any_appointment(self):
        appointment = self.other_master_appointment()
        self.client.force_login(self.superuser)

        response = self.client.post(reverse('appointments:delete', args=[appointment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.filter(pk=appointment.pk).exists())


class ProcedureModelTests(TestCase):
    def test_duration_display(self):
        cases = [(45, '45 min'), (60, '01:00'), (90, '01:30')]
        for minutes, expected in cases:
            with self.subTest(minutes=minutes):
                procedure = Procedure(procedure_name='Test', duration_minutes=minutes)
                self.assertEqual(procedure.duration_display, expected)