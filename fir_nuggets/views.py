from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string

from django.http import HttpResponse
from json import dumps

from incidents.views import is_incident_handler
from incidents.models import Incident
from fir_nuggets.models import Nugget, NuggetForm


@login_required
@user_passes_test(is_incident_handler)
def list(request, event_id):
    e = get_object_or_404(Incident, pk=event_id)
    nuggets = e.nugget_set.all().order_by('start_timestamp')
    return render(request, 'fir_nuggets/list.html', {'nuggets': nuggets})


@login_required
@user_passes_test(is_incident_handler)
def new(request, event_id):
    e = get_object_or_404(Incident, pk=event_id)

    if request.method == "GET":
        nugget_form = NuggetForm()

    if request.method == 'POST':
        nugget_form = NuggetForm(request.POST)

        if nugget_form.is_valid():
            nugget = nugget_form.save(commit=False)
            nugget.incident = e
            nugget.found_by = request.user
            nugget.save()

            ret = {
                'status': 'success',
                'row': render_to_string("fir_nuggets/nugget_row.html", {'n': nugget, 'mode': 'row'}),
                'raw': render_to_string("fir_nuggets/nugget_row.html", {'n': nugget, 'mode': 'raw'}),
                'nugget_id': nugget.id,
                'mode': 'new',
            }

            e.refresh_artifacts(nugget.raw_data)

            return HttpResponse(dumps(ret), content_type='application/json')
        else:
            errors = render_to_string("fir_nuggets/nugget_form.html", {'mode': 'new', 'nugget_form': nugget_form, 'event_id': e.id})
            ret = {'status': 'error', 'data': errors}
            return HttpResponse(dumps(ret), content_type="application/json")

    return render(request, "fir_nuggets/nugget_form.html", {'nugget_form': nugget_form, 'mode': 'new', 'event_id': event_id})


@login_required
@user_passes_test(is_incident_handler)
def edit(request, nugget_id):
    n = get_object_or_404(Nugget, pk=nugget_id)

    if request.method == "GET":
        nugget_form = NuggetForm(instance=n)
        return render(request, "fir_nuggets/nugget_form.html", {'mode': 'edit', 'nugget_form': nugget_form, 'nugget_id': n.id})

    if request.method == "POST":
        nugget_form = NuggetForm(request.POST, instance=n)

        if nugget_form.is_valid():
            nugget = nugget_form.save()
            ret = {
                'status': 'success',
                'mode': 'edit',
                'nugget_id': nugget.id,
                'row': render_to_string("fir_nuggets/nugget_row.html", {'n': nugget, 'mode': 'row'}),
                'raw': render_to_string("fir_nuggets/nugget_row.html", {'n': nugget, 'mode': 'raw'}),
            }
            return HttpResponse(dumps(ret), content_type='application/json')

        else:
            errors = render_to_string("fir_nuggets/nugget_form.html", {'mode': 'edit', 'nugget_form': nugget_form, 'nugget_id': n.id})
            ret = {'status': 'error', 'data': errors}
            return HttpResponse(dumps(ret), content_type="application/json")


@login_required
@user_passes_test(is_incident_handler)
def delete(request, nugget_id):
    n = get_object_or_404(Nugget, pk=nugget_id)
    n.delete()
    return HttpResponse(nugget_id)
