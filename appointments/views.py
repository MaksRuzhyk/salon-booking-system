from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Appointment, Procedure
from .forms import AppointmentForm


@login_required
def index(request):
    masters = User.objects.filter(is_active=True, is_superuser=False)
    procedures = Procedure.objects.all()


    return render(request, 'appointments/calendar.html', {
        'masters': masters,
        'procedures': procedures,
    })

@login_required

def appointments_api(request):
    master_id = request.GET.get('master_id')
    start = parse_datetime(request.GET.get('start'))
    end = parse_datetime(request.GET.get('end'))

    appointments = Appointment.objects.select_related('procedure', 'master').filter(master__is_active=True, master__is_superuser=False)

    if master_id:
        appointments = appointments.filter(master_id=master_id)

    if start and end:
        appointments = appointments.filter(date__gte=start.date(), date__lt=end.date())

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
    form = AppointmentForm(request.POST)
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
    appointment.delete()
    return JsonResponse({'success': True})

@login_required
@require_POST
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    form = AppointmentForm(request.POST, instance=appointment)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
