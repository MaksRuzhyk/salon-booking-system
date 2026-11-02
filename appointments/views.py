from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Appointment, Procedure
from .forms import AppointmentForm
from django.utils.translation import gettext as _


def parse_required_datetime(value: str):
    if not value:
        return None
    try:
        return parse_datetime(value)
    except ValueError:
        return None

def can_manage(user, appointment):
    return user.is_staff or appointment.master_id == user.pk
def forbidden():
    return JsonResponse({
        'success': False, 'error': _('You can only manage your own appointments.'),
    }, status=403)


@login_required
def index(request):
    masters = User.objects.filter(is_active=True, is_superuser=False)
    if not request.user.is_staff:
        masters = masters.filter(pk=request.user.pk)
    procedures = Procedure.objects.all()


    return render(request, 'appointments/calendar.html', {
        'masters': masters,
        'procedures': procedures,
    })

@login_required
def appointments_api(request):
    start = parse_required_datetime(request.GET.get('start'))
    end = parse_required_datetime(request.GET.get('end'))
    if start is None or end is None:
        return JsonResponse({
            'error': "Parameters start and end are required in format YYYY-MM-DD",
        }, status=400)

    appointments = (
        Appointment.objects.select_related('procedure', 'master').filter
        (master__is_active=True, master__is_superuser=False,
        date__gte=start.date(), date__lt=end.date())
    )
    if not request.user.is_staff:
        appointments = appointments.filter(master=request.user)
    master_id = request.GET.get('master_id')
    if master_id:
        try:
            master_id = int(master_id)
        except ValueError:
            return JsonResponse({
                'error': "master id must be an integer",
            }, status=400)
        appointments = appointments.filter(master_id=master_id)

    events = []
    for appointment in appointments:
        events.append({
            'id': appointment.id,
            'title': appointment.procedure.procedure_name,
            'start': f'{appointment.date}T{appointment.start_time}',
            'end': f'{appointment.date}T{appointment.end_time}',
            'extendedProps': {
                'procedure_id': appointment.procedure_id,
                'client_name': appointment.client_name,
                'master_id': appointment.master_id,
            }
        })

    return JsonResponse(events, safe=False)

@login_required
@require_POST
def add_appointment(request):
    form = AppointmentForm(request.POST, user=request.user)
    if form.is_valid():
        appointment = form.save()
        return JsonResponse({
            'success': True,
            'id': appointment.id,
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
@require_POST
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not can_manage(request.user, appointment):
        return forbidden()
    appointment.delete()
    return JsonResponse({'success': True})

@login_required
@require_POST
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not can_manage(request.user, appointment):
        return forbidden()
    form = AppointmentForm(request.POST, instance=appointment)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
