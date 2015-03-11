import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from incidents.views import is_incident_handler
from incidents.models import Incident

from fir_todos.models import TodoItem, TodoItemForm


@require_POST
@login_required
@user_passes_test(is_incident_handler)
def create(request, incident_id):
	incident = get_object_or_404(Incident, pk=incident_id)

	form = TodoItemForm(request.POST)
	item = form.save(commit=False)
	item.incident = incident
	item.category = incident.category
	item.done = False
	item.save()

	return render(request, 'fir_todos/single.html', {'item': item})


@login_required
@user_passes_test(is_incident_handler)
def list(request, incident_id):
	incident = get_object_or_404(Incident, pk=incident_id)
	todos = incident.todoitem_set.all()
	form = TodoItemForm()

	return render(request, 'fir_todos/list.html',
		{'todos': todos, 'form': form, 'incident_id': incident_id})


@require_POST
@login_required
@user_passes_test(is_incident_handler)
def delete(request, todo_id):
	todo = get_object_or_404(TodoItem, pk=todo_id)
	todo.delete()

	return HttpResponse('')


@require_POST
@login_required
@user_passes_test(is_incident_handler)
def toggle_status(request, todo_id):
	todo = get_object_or_404(TodoItem, pk=todo_id)
	todo.done = not todo.done
	if todo.done:
		todo.done_time = datetime.datetime.now()
	todo.save()

	referer = request.META.get('HTTP_REFERER', None)
	dashboard = False
	if ('/incidents/' not in referer) and ('/events/' not in referer):
		dashboard = True

	return render(request, 'fir_todos/single.html', {'item': todo, 'dashboard': dashboard})


@login_required
@user_passes_test(is_incident_handler)
def dashboard(request):
	todos = TodoItem.objects.filter(business_line__name='CERT', done=False)
	todos = todos.select_related('incident', 'category')
	todos = todos.order_by('-incident__date')

	page = request.GET.get('page', 1)
	todos_per_page = request.user.profile.incident_number
	p = Paginator(todos, todos_per_page)

	try:
		todos = p.page(page)
	except (PageNotAnInteger, EmptyPage):
		todos = p.page(1)

	return render(request, 'fir_todos/dashboard.html', {'todos': todos})
