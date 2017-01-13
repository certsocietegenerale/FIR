# -*- coding: utf-8 -*-


# Create your views here.
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST

from incidents.models import IncidentCategory, Incident, Comments, BusinessLine
from incidents.models import Label, Log, BaleCategory
from incidents.models import Attribute, ValidAttribute, IncidentTemplate, Profile
from incidents.models import IncidentForm, CommentForm
from incidents.authorization.decorator import authorization_required
from fir.config.base import INSTALLED_APPS
import importlib

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.core.urlresolvers import reverse
from django.db.models import Q, Max
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext
from json import dumps
from django.template import Template

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.forms.models import model_to_dict, modelform_factory
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import re, datetime
from dateutil.relativedelta import *
from dateutil.parser import parse
from bson import json_util

import copy
import math

from fir_artifacts import artifacts as libartifacts

cal = [
    'jan',
    'feb',
    'mar',
    'apr',
    'may',
    'jun',
    'jul',
    'aug',
    'sep',
    'oct',
    'nov',
    'dec',
]

APP_HOOKS = {}

for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        try:
            h = importlib.import_module('{}.hooks'.format(app))
            APP_HOOKS[app_name] = h.hooks
        except ImportError as e:
            print "No module named hooks for {}".format(app_name)




# helper =========================================================


def is_incident_handler(user):
    return user.has_perm('incidents.handle_incidents', obj=Incident)


def is_incident_reporter(user):
    return user.has_perm('incidents.handle_incidents', obj=Incident) or user.has_perm('incidents.report_events',
                                                                                      obj=Incident)


def is_incident_viewer(user):
    return user.has_perm('incidents.view_incidents', obj=Incident) or user.has_perm('incidents.report_events',
                                                                                    obj=Incident)


def can_view_statistics(user):
    return user.has_perm('incidents.view_statistics', obj=Incident)


comment_permissions = ['incidents.handle_incidents', ]
if getattr(settings, 'INCIDENT_VIEWER_CAN_COMMENT', False):
    comment_permissions.append('incidents.view_incidents')


# login / logout =================================================


def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if not request.POST.get('remember', None):
                request.session.set_expiry(0)

            try:
                Profile.objects.get(user=user)
            except ObjectDoesNotExist:
                profile = Profile()
                profile.user = user
                profile.hide_closed = False
                profile.incident_number = 50
                profile.save()

            if user.is_active:
                login(request, user)
                log("Login", user)
                init_session(request)
                return redirect('dashboard:main')
            else:
                return HttpResponse('Account disabled')
        else:
            return render(request, 'incidents/login.html', {'error': 'error'})
    else:
        return render(request, 'incidents/login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')


def init_session(request):
    pass
    # Put all the incident templates in the session
    request.session['incident_templates'] = list(IncidentTemplate.objects.exclude(name='default').values('name'))
    request.session['has_incident_templates'] = len(request.session['incident_templates']) > 0
    request.session['can_report_event'] = request.user.has_perm('incidents.handle_incidents', obj=Incident) or \
                                          request.user.has_perm('incidents.report_events', obj=Incident)


# audit trail =====================================================


def log(what, user, incident=None, comment=None):
    # dirty hack to not log when in debug mode
    import sys
    if getattr(settings, 'DEBUG', False):
        print "DEBUG: Not logging"
        return

    log = Log()
    log.what = what
    log.who = user
    log.incident = incident
    log.comment = comment

    log.save()


# incidents =======================================================

@login_required
@authorization_required('incidents.view_incidents', Incident, view_arg='incident_id')
def followup(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, ['incidents.view_incidents', 'incidents.handle_incidents']),
            pk=incident_id)
    else:
        i = authorization_target
    comments = i.comments_set.all().order_by('date')

    return render(
        request,
        'incidents/followup.html',
        {'incident': i, 'comments': comments, 'incident_show_id': settings.INCIDENT_SHOW_ID}
    )


@login_required
@user_passes_test(is_incident_viewer)
def index(request, is_incident=False):
    return render(request, 'events/index-all.html', {'incident_view': is_incident})


@login_required
@user_passes_test(is_incident_viewer)
def incidents_all(request):
    return incident_display(request, Q(is_incident=True))


@login_required
@user_passes_test(is_incident_viewer)
def events_all(request):
    return incident_display(request, Q(is_incident=False), False)


@login_required
@authorization_required('incidents.view_incidents', Incident, view_arg='incident_id')
def details(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, ['incidents.view_incidents', 'incidents.handle_incidents']),
            pk=incident_id)
    else:
        i = authorization_target
    form = CommentForm()
    if not request.user.has_perm('incidents.handle_incidents', obj=i):
        form.fields['action'].queryset = Label.objects.filter(group__name='action').exclude(
            name__in=['Closed', 'Opened', 'Blocked'])

    (artifacts, artifacts_count, correlated_count) = libartifacts.all_for_object(i, user=request.user)

    """
    Temp fix until i figure out how to set this
    """
    valid_attributes = i.category.validattribute_set.all()
    attributes = i.attribute_set.all()

    comments = i.comments_set.all().order_by('date')

    return render(
        request,
        "events/detail-all.html",
        {"event": i,
         "comment_form": form,
         "correlated_count": correlated_count,
         "artifacts_count": artifacts_count,
         "artifacts": artifacts,
         "attributes": attributes,
         "valid_attributes": valid_attributes,
         "comments": comments,
         "incident_show_id": settings.INCIDENT_SHOW_ID}
    )


@login_required
@user_passes_test(is_incident_reporter)
def new_event(request):
    if request.method == 'POST':
        form = IncidentForm(request.POST, for_user=request.user)

        form.status = _('Open')

        if form.is_valid():
            i = form.save(commit=False)

            if not form.cleaned_data['is_major']:
                i.is_major = form.cleaned_data['category'].is_major

            if i.is_major:
                i.is_incident = True

            i.opened_by = request.user
            i.save()
            form.save_m2m()
            i.refresh_main_business_lines()
            i.done_creating()

            if i.is_incident:
                return redirect("incidents:details", incident_id=i.id)
            else:
                return redirect("events:details", incident_id=i.id)

    else:
        template = request.GET.get('template', 'default')
        try:
            template = IncidentTemplate.objects.get(name=template)
            data = model_to_dict(template)
            data['description'] = Template(data['description']).render(RequestContext(request))
        except ObjectDoesNotExist:
            data = {}
        form = IncidentForm(initial=data, for_user=request.user)

    return render(request, 'events/new.html', {'form': form, 'mode': 'new'})


def diff(incident, form):
    comments = []
    for i in form:
        # skip the following fields from diff
        if i in ['description', 'concerned_business_lines', 'main_business_lines']:
            continue

        new = form[i]
        old = getattr(incident, i)

        if new != old:

            label = i

            if i == 'is_major':
                label = 'major'
            if i == 'concerned_business_lines':
                label = "business lines"
            if i == 'main_business_line':
                label = "main business line"
            if i == 'is_incident':
                label = 'incident'

            if old == "O":
                old = 'Open'
            if old == "C":
                old = 'Closed'
            if old == "B":
                old = 'Blocked'
            if new == "O":
                new = 'Open'
            if new == "C":
                new = 'Closed'
            if new == "B":
                new = 'Blocked'

            comments.append(u'Changed "%s" from "%s" to "%s";' % (label, old, new))

    return "\n".join(comments)


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def edit_incident(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
            pk=incident_id)
    else:
        i = authorization_target
    starred = i.is_starred

    if request.method == "POST":
        form = IncidentForm(request.POST, instance=i, for_user=request.user)

        if form.is_valid():
            Comments.create_diff_comment(i, form.cleaned_data, request.user)

            # update main BL
            form.save()
            i.refresh_main_business_lines()
            i.is_starred = starred
            i.save()
            i.done_updating()

            if i.is_incident:
                return redirect("incidents:details", incident_id=i.id)
            else:
                return redirect("events:details", incident_id=i.id)
    else:
        form = IncidentForm(instance=i, for_user=request.user)

    return render(request, 'events/new.html', {'i': i, 'form': form, 'mode': 'edit'})


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def delete_incident(request, incident_id, authorization_target=None):
    if request.method == "POST":
        if authorization_target is None:
            i = get_object_or_404(
                Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
                pk=incident_id)
        else:
            i = authorization_target
        msg = "Incident '%s' deleted." % i.subject
        i.delete()
        return HttpResponse(msg)
    else:
        return redirect("incidents:index")


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def change_status(request, incident_id, status, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
            pk=incident_id)
    else:
        i = authorization_target
    i.status = status
    i.save()

    status_name = 'Closed'
    if status == 'O':
        status_name = 'Opened'
    elif status == 'B':
        status_name = 'Blocked'

    c = Comments()
    c.comment = "Status changed to '%s'" % status_name
    c.date = datetime.datetime.now()
    c.action = get_object_or_404(Label, name=status_name, group__name='action')
    c.incident = i
    c.opened_by = request.user
    c.save()

    return redirect('dashboard:main')


# attributes ================================================================


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def add_attribute(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
            pk=incident_id)
    else:
        i = authorization_target
    if request.method == "POST":
        # First, check if it is a valid attribute
        valid_attribute = get_object_or_404(ValidAttribute, name=request.POST['name'])

        # Create a new attribute
        a = Attribute(name=valid_attribute.name, value=request.POST['value'])
        # Except if valid attribute has an unit and this particular attribute already exists
        # In this case, a single attribute should be keeped, with an updated value
        if valid_attribute.unit is not None and valid_attribute.unit != "":
            try:
                a = i.attribute_set.get(name=valid_attribute.name)
                a.value = str(int(a.value) + int(request.POST['value']))
            except:
                pass

        a.incident = i
        a.save()

        if request.is_ajax():
            return render(request, 'events/_attributes.html', {'attributes': i.attribute_set.all(), 'event': i})

    return redirect('incidents:details', incident_id=incident_id)


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def delete_attribute(request, incident_id, attribute_id, authorization_target=None):
    a = get_object_or_404(Attribute, pk=attribute_id)
    if request.method == "POST":
        a.delete()
    return redirect('incidents:details', incident_id=incident_id)


# comments ==================================================================

@login_required
def edit_comment(request, incident_id, comment_id):
    c = get_object_or_404(Comments, pk=comment_id, incident_id=incident_id)
    i = c.incident
    incident_handler = False
    if not request.user.has_perm('incidents.handle_incidents', obj=i):
        if c.opened_by != request.user:
            raise PermissionDenied()
    else:
        incident_handler = True

    if request.method == "POST":
        form = CommentForm(request.POST, instance=c)
        if not incident_handler:
            form.fields['action'].queryset = Label.objects.filter(group__name='action').exclude(
                name__in=['Closed', 'Opened', 'Blocked'])
        if form.is_valid():
            form.save()
            log("Edited comment %s" % (form.cleaned_data['comment'][:10] + "..."), request.user,
                incident=Incident.objects.get(id=incident_id))
            return redirect("incidents:details", incident_id=c.incident_id)
    else:
        form = CommentForm(instance=c)
        if not incident_handler:
            form.fields['action'].queryset = Label.objects.filter(group__name='action').exclude(
                name__in=['Closed', 'Opened', 'Blocked'])

    return render(request, 'events/edit_comment.html', {'c': c, 'form': form})


@login_required
def delete_comment(request, incident_id, comment_id):
    c = get_object_or_404(Comments, pk=comment_id, incident_id=incident_id)
    i = c.incident
    if not request.user.has_perm('incidents.handle_incidents', obj=i) and not c.opened_by == request.user:
        raise PermissionDenied()
    if request.method == "POST":
        msg = "Comment '%s' deleted." % (c.comment[:20] + "...")
        c.delete()
        log(msg, request.user, incident=Incident.objects.get(id=incident_id))
        return redirect('incidents:details', incident_id=c.incident_id)
    else:
        return redirect('incidents:details', incident_id=c.incident_id)


@login_required
def update_comment(request, comment_id):
    c = get_object_or_404(Comments, pk=comment_id)
    i = c.incident
    if request.method == 'GET':
        if not request.user.has_perm('incidents.view_incidents', obj=i):
            ret = {'status': 'error', 'errors': ['Permission denied', ]}
            return HttpResponseServerError(dumps(ret), content_type="application/json")
        serialized = serializers.serialize('json', [c, ])
        return HttpResponse(dumps(serialized), content_type="application/json")
    else:
        comment_form = CommentForm(request.POST, instance=c)
        if not request.user.has_perm('incidents.handle_incidents', obj=i):
            comment_form.fields['action'].queryset = Label.objects.filter(group__name='action').exclude(
                name__in=['Closed', 'Opened', 'Blocked'])

        if comment_form.is_valid():

            c = comment_form.save()

            log("Comment edited: %s" % (comment_form.cleaned_data['comment'][:20] + "..."), request.user,
                incident=c.incident)

            if c.action.name in ['Closed', 'Opened', 'Blocked']:
                c.incident.status = c.action.name[0]
                c.incident.save()

            i.refresh_artifacts(c.comment)

            return render(request, 'events/_comment.html', {'comment': c, 'event': i})
        else:
            ret = {'status': 'error', 'errors': comment_form.errors}
            return HttpResponseServerError(dumps(ret), content_type="application/json")


# events ====================================================================

@login_required
@user_passes_test(is_incident_viewer)
def event_index(request):
    return index(request, False)


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.

    '''
    query = None  # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})

            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


@login_required
@user_passes_test(is_incident_viewer)
def search(request):
    query_string = ''
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']

        if request.is_ajax():
            asc = request.GET.get('asc', 'false')
            q = Q()

            plan = re.search("plan:(\S+)", query_string)
            if plan:
                q = q & Q(plan__name=plan.group(1))
                query_string = query_string.replace("plan:" + plan.group(1), '')

            try:
                bl = re.search("bl:(\S+)", query_string).group(1)
                bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_incidents').filter(
                    name__icontains=bl)
                if bls:
                    q = q & (Q(concerned_business_lines__in=bls) | Q(main_business_lines__in=bls))
                    query_string = query_string.replace("bl:" + bl, '')
            except Exception:
                pass

            opened_by = re.search("opened_by:(\S+)", query_string)
            if opened_by:
                q = q & Q(opened_by__username=opened_by.group(1))
                query_string = query_string.replace('opened_by:' + opened_by.group(1), '')

            category = re.search("category:(\S+)", query_string)
            if category:
                q = q & Q(category__name__icontains=category.group(1))
                query_string = query_string.replace('category:' + category.group(1), '')

            status = re.search("status:(\S+)", query_string)
            if status:
                q = q & Q(status=status.group(1)[0])
                query_string = query_string.replace('status:' + status.group(1), '')

            artifacts = re.search("art:(\S+)", query_string)
            if artifacts:
                artifacts = artifacts.group(1)
                q = q & Q(id__in=[i.id for i in libartifacts.incs_for_art(artifacts)])
                query_string = query_string.replace('art:' + artifacts, '')

            if query_string.count('starred') > 0:
                q = q & Q(is_starred=True)
                query_string = query_string.replace('starred', '')

            severity = re.search("severity(?P<eval>[:<>])(?P<value>\d)", query_string)
            if severity:
                if severity.group('eval') == ':':
                    q = q & Q(severity=severity.group("value"))
                elif severity.group('eval') == ">":
                    q = q & Q(severity__gt=severity.group("value"))
                elif severity.group('eval') == "<":
                    q = q & Q(severity__lt=severity.group("value"))
                query_string = query_string.replace('severity' + severity.group('eval') + severity.group("value"), '')

            # app keyword_filters go here
            for app_name, hooks in APP_HOOKS.items():
                if "keyword_filter" in hooks:
                    q, query_string = hooks['keyword_filter'](q, query_string)

            pattern = re.compile('\s+')

            query_string = query_string.strip()

            other = pattern.split(query_string)
            if query_string != ['']:
                q_other = Q()
                for i in other:
                    q_other &= (
                        Q(subject__icontains=i) | Q(description__icontains=i) | Q(comments__comment__icontains=i)
                    )

                    # app search_filters go here
                    for app_name, hooks in APP_HOOKS.items():
                        if "search_filter" in hooks:
                            q_other, query_string = hooks['search_filter'](q_other, query_string)
            q = (q & q_other)

            # TODO a function that takes in incidents and returns them ordered

            order_param = request.GET.get('order_by', 'date')

            order_by = order_param

            if order_by not in ['date', 'subject', 'category', 'bl', 'severity', 'status', 'opened_by', 'detection',
                                'actor', 'confidentiality']:
                order_by = 'date'

            if order_by == "category":
                order_by = 'category__name'
            if order_by == 'detection':
                order_by = 'detection__name'
            if order_by == 'actor':
                order_by = 'actor__name'

            if asc == 'false':
                order_by = "-" + order_by

            found_entries = Incident.authorization.for_user(request.user, 'incidents.view_incidents').filter(q)

            if order_param == 'last_action':
                if asc:
                    found_entries = found_entries.annotate(Max('comments__date')).order_by('comments__date__max')
                else:
                    found_entries = found_entries.annotate(Max('comments__date')).order_by('-comments__date__max')

            else:
                found_entries = found_entries.order_by(order_by).all()

            # distinct
            found_entries = found_entries.distinct()

            # get hide_closed option from user profile
            if request.user.profile.hide_closed:
                found_entries = found_entries.filter(~Q(status='C'))

            # get number of pages from user profile
            page = request.GET.get('page')
            incident_number = request.user.profile.incident_number

            p = Paginator(found_entries, incident_number)

            try:
                found_entries = p.page(page)
            except PageNotAnInteger:
                found_entries = p.page(1)
            except EmptyPage:
                found_entries = p.page(1)

            return render(request, 'events/table.html',
                          {'incident_list': found_entries, 'order_param': order_param, 'asc': asc})
        else:
            return render(request, 'events/search.html', {'query_string': query_string})
    else:
        return redirect('incidents:index')

    if request.is_ajax():
        query_string = ''
        found_entries = None
        if ('q' in request.GET) and request.GET['q'].strip():
            query_string = request.GET['q']
        else:
            return redirect('incidents:index')
    else:
        return render(request, 'events/search.html', {'query_string': q})


# ajax ======================================================================

@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def toggle_star(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
            pk=incident_id)
    else:
        i = authorization_target

    i.is_starred = not i.is_starred

    i.save()

    return HttpResponse(dumps({'starred': i.is_starred}), content_type='application/json')


@login_required
@authorization_required(comment_permissions, Incident, view_arg='incident_id')
def comment(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, comment_permissions),
            pk=incident_id)
    else:
        i = authorization_target

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if not request.user.has_perm('incidents.handle_incidents'):
            comment_form.fields['action'].queryset = Label.objects.filter(group__name='action').exclude(
                name__in=['Closed', 'Opened', 'Blocked'])
        if comment_form.is_valid():
            com = comment_form.save(commit=False)
            com.incident = i
            com.opened_by = request.user
            com.save()
            log("Comment created: %s" % (com.comment[:20] + "..."), request.user, incident=com.incident)
            i.refresh_artifacts(com.comment)

            if com.action.name in ['Closed', 'Opened', 'Blocked']:
                com.incident.status = com.action.name[0]
                com.incident.save()

            return render(request, 'events/_comment.html', {'event': i, 'comment': com})
        else:
            ret = {'status': 'error', 'errors': comment_form.errors}
            return HttpResponseServerError(dumps(ret), content_type="application/json")

    return redirect('incidents:details', incident_id=incident_id)


# User ==========================================================================

@login_required
def toggle_closed(request):
    request.user.profile.hide_closed = not request.user.profile.hide_closed
    request.user.profile.save()
    response = {'status': 'ok', 'hide_closed': request.user.profile.hide_closed}
    return HttpResponse(dumps(response), content_type="application/json")


# Statistics ====================================================================

def delete_empty_keys(chart_data):
    to_delete = []

    for key in list(chart_data[0].keys()):
        delete = True
        for i in range(len(chart_data)):
            if chart_data[i].get(key) != 0:
                delete = False
        if delete:
            to_delete.append(key)

    for key in to_delete:
        for d in chart_data:
            del d[key]

    return chart_data


@login_required
@user_passes_test(can_view_statistics)
def yearly_stats(request):
    return render(request, 'stats/yearly.html')


@login_required
@user_passes_test(is_incident_handler)
def close_old(request):
    now = datetime.datetime.now()
    query = Q(date__lt=datetime.datetime(now.year, now.month, 1) - datetime.timedelta(days=90)) & ~Q(status="C")
    old = Incident.authorization.for_user(request.user, 'incidents.handle_incidents').filter(query)
    for i in old:
        if i.status != "C":
            i.close_timeout()

    return redirect('stats:quarterly_bl_stats_default')


@login_required
@user_passes_test(can_view_statistics)
def quarterly_bl_stats(request, business_line=None, num_months=3):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics')

    try:
        bl = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').get(name=business_line)
    except:
        bl = bls[0]

    today = datetime.date.today()
    q_month = Q()
    for i in xrange(num_months):
        previous = today - relativedelta(months=i + 1)
        month = previous.month
        year = previous.year

        q_month |= Q(date__month=month, date__year=year)

    q = q_month & Q(confidentiality__lte=2)
    qbl = (
        Q(concerned_business_lines=bl) | Q(main_business_lines=bl) | Q(concerned_business_lines__in=bl.get_children()))
    q &= qbl

    incident_list = [i for i in
                     Incident.authorization.for_user(request.user, 'incidents.view_incidents').filter(q).order_by(
                         '-date').distinct()]
    unclosed = qbl & Q(date__lt=today - relativedelta(months=3)) & ~Q(status='C')
    unclosed_incident_list = [i for i in
                              Incident.authorization.for_user(request.user, 'incidents.view_incidents').filter(
                                  unclosed).order_by('-date').distinct()]

    return render(request, 'stats/quarterly.html',
                  {'bl': bl, 'incident_list': incident_list, 'unclosed_incident_list': unclosed_incident_list,
                   'bls': bls})


@login_required
@user_passes_test(can_view_statistics)
def yearly_compare(request, year=None):
    if year is None:
        year = datetime.datetime.now().year - 1

    return render(request, 'stats/yearly_compare.html', {'year': year})


# comparison ===============================================================

@login_required
@user_passes_test(can_view_statistics)
def data_sandbox(request):
    # parse request parameters from GET requests

    category_selection_ids = [int(c) for c in request.GET.getlist('category_selection')]

    if category_selection_ids == []:
        category_selection = IncidentCategory.objects.all()
    else:
        category_selection = IncidentCategory.objects.filter(id__in=category_selection_ids)

    start = parse(request.GET['from_date'])
    end = parse(request.GET['to_date'])
    divisor = request.GET['divisor']
    graph_type = request.GET['graph_type']

    dates = []
    delta = relativedelta(end, start)
    months = delta.years * 12 + delta.months

    for i in xrange(months):
        dates.append(end - relativedelta(months=i + 1))

    q_categories = Q()
    for c in category_selection:
        q_categories |= Q(category=c)

    bls = []
    child_bls = []

    for bl in request.GET.getlist('concerned_business_lines'):
        bls.append(int(bl))
        bl = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').get(id=bl)
        child_bls += bl.get_descendants()

    if len(bls) > 0:
        q_bl = Q(concerned_business_lines__in=bls + child_bls) | Q(main_business_lines__in=bls)
    else:
        bls = None
        q_bl = Q()

    if request.GET["detection"] != "":
        q_detection = Q(detection=int(request.GET["detection"]))
    else:
        q_detection = Q()

    if request.GET["severity"] != "":
        if request.GET['severity_comparator'] == 'lt':
            q_severity = Q(severity__lt=int(request.GET["severity"]))
        elif request.GET['severity_comparator'] == 'gt':
            q_severity = Q(severity__gt=int(request.GET["severity"]))
        else:
            q_severity = Q(severity=int(request.GET["severity"]))
    else:
        q_severity = Q()

    if request.GET.get('is_incident', False):  # only incidents
        q_is_incident = Q(is_incident=True)
    else:
        q_is_incident = Q()

    if request.GET.get('is_major', False):  # only major incidents
        q_is_major = Q(is_major=True)
    else:
        q_is_major = Q()

    q_all = q_categories & q_detection & q_severity & q_is_incident & q_is_major & q_bl

    chart_data = []

    if graph_type == 'table':
        if divisor == 'all':
            qs = Q()
            for i in xrange(months):
                qs |= Q(date__year=dates[i].year, date__month=dates[i].month)

            incidents = Incident.authorization.for_user(request.user, 'incidents.view_incidents').filter(
                qs & q_all).distinct()
            for inc in incidents:
                plot = {}
                plot['date'] = str(inc.date)
                plot['id'] = inc.id
                plot['subject'] = inc.subject
                plot['category'] = inc.category.name
                plot['confidentiality_display'] = inc.get_confidentiality_display()
                plot['severity'] = inc.severity
                plot['business_lines_names'] = inc.get_business_lines_names()
                plot['status_display'] = inc.get_status_display()
                plot['detection'] = str(inc.detection)
                plot['actor'] = str(inc.actor)
                plot['last_comment_action'] = inc.get_last_comment().action.name
                plot['last_comment_date'] = str(inc.get_last_comment().date)
                plot['opened_by'] = str(inc.opened_by)
                plot['plan'] = str(inc.plan)
                chart_data.append(plot)

    if graph_type == 'line':

        if divisor == 'all':
            for i in xrange(months):
                plot = {}
                plot['date'] = str(dates[i].year) + "-" + str(dates[i].month)
                plot['N'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year, date__month=dates[i].month) & q_all).distinct().count()
                plot['N-1'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year - 1, date__month=dates[i].month) & q_all).distinct().count()
                chart_data.append(plot)

        if divisor == 'category':
            for i in xrange(months):
                plot = {}
                plot['date'] = str(dates[i].year) + "-" + str(dates[i].month)

                for cat in category_selection:
                    plot[cat.name] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                        Q(date__year=dates[i].year, date__month=dates[i].month,
                          category=cat) & q_detection & q_severity & q_is_incident & q_is_major & q_bl).distinct().count()
                chart_data.append(plot)

    if graph_type == 'bar':

        if divisor == 'months':
            for i in xrange(months):
                plot = {}
                plot['label'] = '%s-%s' % (dates[i].year, dates[i].month)
                plot['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year, date__month=dates[i].month) & q_all).distinct().count()
                plot['text'] = plot['value']
                chart_data.append(plot)

        if divisor == 'monitoring':
            for i in xrange(months):
                plot = {}
                plot['label'] = '%s-%s' % (dates[i].year, dates[i].month)
                plot['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year, date__month=dates[i].month, plan__name='A') & q_all).distinct().count()
                plot['text'] = plot['value']
                chart_data.append(plot)

        if divisor == 'open':
            for i in xrange(months):
                plot = {}
                plot['label'] = '%s-%s' % (dates[i].year, dates[i].month)
                plot['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year, date__month=dates[i].month, status='O') & q_all).distinct().count()
                plot['text'] = plot['value']
                chart_data.append(plot)

        if divisor == 'blocked':
            for i in xrange(months):
                plot = {}
                plot['label'] = '%s-%s' % (dates[i].year, dates[i].month)
                plot['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    Q(date__year=dates[i].year, date__month=dates[i].month, status='B') & q_all).distinct().count()
                plot['text'] = plot['value']
                chart_data.append(plot)

    if graph_type == 'donut' or graph_type == 'stacked':

        if divisor == 'severity':
            for i in xrange(months):
                plot = {}
                plot['entry'] = '%s-%s' % (dates[i].year, dates[i].month)
                append = False
                for severity in xrange(1, 5):
                    plot['%s/4' % severity] = Incident.authorization.for_user(request.user,
                                                                              'incidents.view_statistics').filter(
                        Q(date__year=dates[i].year, date__month=dates[i].month,
                          severity=severity) & q_severity & q_categories & q_detection & q_is_incident & q_is_major & q_bl).distinct().count()
                    if plot['%s/4' % severity] > 0:
                        append = True
                if append:
                    chart_data.append(plot)

        if divisor == 'subentity':
            if not bls:
                children = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    depth=1)
            else:
                bl = BusinessLine.objects.get(id=bl)
                children = bl.get_children()

            for i in xrange(months):
                plot = {}
                for cbl in children:
                    plot[cbl.name] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                        Q(date__year=dates[i].year, date__month=dates[i].month,
                          concerned_business_lines=cbl) & q_categories & q_detection & q_severity & q_is_incident & q_is_major).distinct().count()

                plot['entry'] = '%s-%s' % (dates[i].year, dates[i].month)
                chart_data.append(plot)

        if divisor == 'actor':
            for i in xrange(months):
                plot = {}
                for actor in Label.objects.filter(group__name='actor'):
                    plot[actor.name] = Incident.authorization.for_user(request.user,
                                                                       'incidents.view_statistics').filter(
                        Q(date__year=dates[i].year, date__month=dates[i].month, actor=actor) & q_all).distinct().count()

                plot['entry'] = '%s-%s' % (dates[i].year, dates[i].month)
                chart_data.append(plot)

        if divisor == 'category':
            for i in xrange(months):
                plot = {}
                for category in category_selection:
                    plot[category.name] = Incident.authorization.for_user(request.user,
                                                                          'incidents.view_statistics').filter(
                        Q(date__year=dates[i].year, date__month=dates[i].month,
                          category=category) & q_detection & q_severity & q_is_incident & q_is_major & q_bl).distinct().count()

                plot['entry'] = '%s-%s' % (dates[i].year, dates[i].month)
                chart_data.append(plot)

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def sandbox(request, divisor='all'):
    form = IncidentForm(request.POST, for_user=request.user, permissions='incidents.view_statistics')

    if request.method == 'POST':
        fr = request.POST['from_date'][:7]
        to = request.POST['to_date'][:7]
    else:
        today = datetime.datetime.today()
        fr = "%s-%s" % (today.year - 1, today.month)
        to = "%s-%s" % (today.year, today.month)

    categories = IncidentCategory.objects.all()
    categories_checked = [int(c) for c in request.POST.getlist('category_selection')]

    return render(
        request,
        'stats/sandbox.html',
        {'start': fr,
         'end': to,
         'form': form,
         'categories': categories,
         'categories_checked': categories_checked,
         })


@login_required
@user_passes_test(can_view_statistics)
def stats_attributes(request):
    form = IncidentForm(for_user=request.user, permissions='incidents.view_statistics')
    categories = IncidentCategory.objects.all()
    attributes = ValidAttribute.objects.exclude(unit__isnull=True)

    now = datetime.datetime.now()
    one_year_ago = now - relativedelta(years=1)
    fr = one_year_ago.strftime('%Y-%m-%d %H:%M')
    to = now.strftime('%Y-%m-%d %H:%M')

    return render(
        request,
        'stats/attributes.html',
        {'start': fr,
         'end': to,
         'form': form,
         'categories': categories,
         'attributes': attributes})


def stats_attributes_filter(request):
    '''Return query filter from request'''
    # Select only checked categories
    q_categories = Q()
    category_selection_ids = [int(c) for c in request.GET.getlist('category_selection')]
    if len(category_selection_ids) > 0:
        q_categories = Q(category_id__in=category_selection_ids)

    # Between the two specified dates
    start = parse(request.GET['from_date'])
    end = parse(request.GET['to_date'])
    q_dates = Q(date__range=(start, end))

    # Only specified business lines
    q_bl = Q()
    bls = []
    child_bls = []

    for bl in request.GET.getlist('concerned_business_lines'):
        bls.append(int(bl))
        bl = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').get(id=bl)
        child_bls += bl.get_descendants()

    if len(bls) > 0:
        q_bl = Q(concerned_business_lines__in=bls + child_bls) | Q(main_business_lines__in=bls)

    # Only the ones detected by specified entity
    q_detection = Q()
    if request.GET["detection"] != "":
        q_detection = Q(detection=int(request.GET["detection"]))

    # Only of the specified severity
    q_severity = Q()
    if request.GET["severity"] != "":
        if request.GET['severity_comparator'] == 'lt':
            q_severity = Q(severity__lt=int(request.GET["severity"]))
        elif request.GET['severity_comparator'] == 'lte':
            q_severity = Q(severity__lte=int(request.GET["severity"]))
        elif request.GET['severity_comparator'] == 'gt':
            q_severity = Q(severity__gt=int(request.GET["severity"]))
        elif request.GET['severity_comparator'] == 'gte':
            q_severity = Q(severity__gte=int(request.GET["severity"]))
        else:
            q_severity = Q(severity=int(request.GET["severity"]))

    # Only incidents if needed
    q_is_incident = Q()
    if request.GET.get('is_incident', False):
        q_is_incident = Q(is_incident=True)

    # Only major incidents if needed
    q_is_major = Q()
    if request.GET.get('is_major', False):
        q_is_major = Q(is_major=True)

    return q_categories & q_dates & q_detection & q_severity & q_is_incident & q_is_major & q_bl


def stats_attributes_get_data(filter, attribute_ids, user, permission='incidents.view_statistics'):
    incidents = Incident.authorization.for_user(user, permission).filter(filter).order_by('date').distinct().reverse()
    incident_ids = [i.id for i in incidents]

    valid_attributes = ValidAttribute.objects.filter(pk__in=attribute_ids)
    valid_attribute_names = [a.name for a in valid_attributes]

    all_attributes = {}
    for name in valid_attribute_names:
        all_attributes[name] = Attribute.objects.filter(incident_id__in=incident_ids, name=name).distinct()

    return (incidents, all_attributes)


def stats_attributes_date_ranges(start, end):
    start = start.replace(tzinfo=None)
    end = end.replace(tzinfo=None)
    delta = end - start

    result = []
    # Less than 3 days, use hours
    if delta.days < 3:
        for i in xrange(int(delta.total_seconds()) / 3600 + 1):
            fr = start + relativedelta(hours=i, minute=0, second=0, microsecond=0)
            to = fr + relativedelta(hours=1)
            result.append({
                "label": fr.strftime('%m-%d %H:%M'),
                "from": fr,
                "to": to,
                "x": (fr - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            })
    # Between 3 days and 1 month, use days
    elif delta.days < 31:
        for i in xrange(int(delta.total_seconds()) / 86400 + 1):
            fr = start + relativedelta(days=i, hour=0, minute=0, second=0, microsecond=0)
            to = fr + relativedelta(days=1)
            result.append({
                "label": fr.strftime('%m-%d'),
                "from": fr,
                "to": to,
                "x": (fr - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            })
    # Between 1 month a 10 months, use weeks
    elif delta.days < 305:
        for i in xrange(int(delta.total_seconds()) / 604800 + 1):
            fr = start + relativedelta(weeks=i, weekday=MO(-1), hour=0, minute=0, second=0, microsecond=0)
            to = fr + relativedelta(days=7)
            result.append({
                "label": str(fr.isocalendar()[1]),
                "from": fr,
                "to": to,
                "x": (fr - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            })
    # Between 10 months and 5 years, use months
    elif delta.days < 1825:
        for i in xrange(int(delta.total_seconds()) / 2592000 + 1):
            fr = start + relativedelta(months=i, day=1, hour=0, minute=0, second=0, microsecond=0)
            to = fr + relativedelta(months=1)
            result.append({
                "label": fr.strftime('%m/%y'),
                "from": fr,
                "to": to,
                "x": (fr - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            })
    # Otherwise, use years
    else:
        for i in xrange(int(delta.total_seconds()) / 31536000 + 1):
            fr = start + relativedelta(years=i, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            to = fr + relativedelta(years=1)
            result.append({
                "label": fr.strftime('%Y'),
                "from": fr,
                "to": to,
                "x": (fr - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            })

    return result


@login_required
@user_passes_test(can_view_statistics)
def stats_attributes_table(request):
    main_filter = stats_attributes_filter(request)

    result = []
    attribute_selection = request.GET.getlist("attribute_selection")
    if request.GET['bars'] != '0':
        attribute_selection.append(request.GET['bars'])
    (incidents, all_attributes) = stats_attributes_get_data(main_filter, attribute_selection, request.user,
                                                            permission='incidents.view_incidents')

    for incident in incidents:
        attribute_count = 0
        attributes = {}
        for valid_attribute in all_attributes:
            attributes[valid_attribute] = []
            for attribute in all_attributes[valid_attribute]:
                if attribute.incident_id == incident.id:
                    attribute_count += 1
                    attributes[valid_attribute].append(attribute.value)
            attributes[valid_attribute] = ', '.join(attributes[valid_attribute])

        if not request.GET.get('only_with_attribute', False) or attribute_count > 0:
            values = {}
            values['date'] = str(incident.date)
            values['category'] = incident.category.name
            values['subject'] = incident.subject
            values['business_lines_names'] = incident.get_business_lines_names()

            if incident.is_incident:
                values['url'] = reverse('incidents:details', args=[incident.id])
            else:
                values['url'] = reverse('events:details', args=[incident.id])

            values['attributes'] = attributes

            result.append(values)

    return HttpResponse(dumps(result), content_type="application/json")


def stats_attributes_by_time_range(request):
    main_filter = stats_attributes_filter(request)
    attribute_selection = request.GET.getlist("attribute_selection")
    if request.GET['bars'] != '0':
        attribute_selection.append(request.GET['bars'])
    (incidents, all_attributes) = stats_attributes_get_data(main_filter, attribute_selection, request.user)
    datetime_ranges = stats_attributes_date_ranges(parse(request.GET['from_date']), parse(request.GET['to_date']))

    for i, datetime_range in enumerate(datetime_ranges):
        # Get incident ids for selected time range
        incident_ids = []
        for incident in incidents:
            if datetime_range['from'] <= incident.date.replace(tzinfo=None) < datetime_range['to']:
                incident_ids.append(incident.id)

        with_attribute = []
        attributes = {}
        for valid_attribute in all_attributes:
            attributes[valid_attribute] = []
            for attribute in all_attributes[valid_attribute]:
                if attribute.incident_id in incident_ids:
                    if attribute.incident_id not in with_attribute:
                        with_attribute.append(attribute.incident_id)
                    attributes[valid_attribute].append(attribute.value)

        yield (datetime_range, incident_ids, attributes, len(with_attribute))


@login_required
@user_passes_test(can_view_statistics)
def stats_attributes_over_time(request):
    incident_values = []
    attribute_values = {}
    i = 0

    bars_attribute = None
    if request.GET['bars'] != '0':
        bars_attribute = ValidAttribute.objects.get(pk=int(request.GET['bars']))

    for date_range, incidents, attributes, with_attribute_count in stats_attributes_by_time_range(request):
        # First, init dictionnary values (only the first time)
        if i == 0:
            for valid_attribute in attributes:
                attribute_values[valid_attribute] = {}
                if bars_attribute is not None and bars_attribute.name == valid_attribute:
                    attribute_values[valid_attribute]['total'] = []
                else:
                    if request.GET.get('total', False):
                        attribute_values[valid_attribute]['total'] = []
                    if request.GET.get('average', False):
                        attribute_values[valid_attribute]['avg'] = []
                    if request.GET.get('deviation', False):
                        attribute_values[valid_attribute]['std'] = []

        # Compute bars_attribute, if any
        if bars_attribute is not None:
            attribute_values[bars_attribute.name]['total'].append(copy.deepcopy(date_range))
            attribute_values[bars_attribute.name]['total'][i]['y'] = sum(
                int(x) for x in attributes[bars_attribute.name])
        # Otherwise, compute incidents
        else:
            incident_values.append(copy.deepcopy(date_range))
            if request.GET.get('only_with_attribute', False):
                incident_values[i]['y'] = with_attribute_count
            else:
                incident_values[i]['y'] = len(incidents)

        # Compute all other attributes
        for valid_attribute in attributes:
            if bars_attribute is None or bars_attribute.name != valid_attribute:
                total = sum(int(x) for x in attributes[valid_attribute])
                if request.GET.get('total', False):
                    attribute_values[valid_attribute]['total'].append(copy.deepcopy(date_range))
                    attribute_values[valid_attribute]['total'][i]['y'] = total
                if request.GET.get('average', False):
                    attribute_values[valid_attribute]['avg'].append(copy.deepcopy(date_range))
                    if bars_attribute is None:
                        if request.GET.get('only_with_attribute', False):
                            attribute_values[valid_attribute]['avg'][i]['y'] = average([total], with_attribute_count)
                        else:
                            attribute_values[valid_attribute]['avg'][i]['y'] = average([total], len(incidents))
                    else:
                        attribute_values[valid_attribute]['avg'][i]['y'] = average([total], attribute_values[
                            bars_attribute.name]['total'][i]['y'])
                if request.GET.get('deviation', False):
                    attribute_values[valid_attribute]['std'].append(copy.deepcopy(date_range))
                    attribute_values[valid_attribute]['avg'][i]['y'] = 0
                    if request.GET.get('average', False):
                        deviation = map(lambda x: (int(x) - attribute_values[valid_attribute]['avg'][i]['y']) ** 2,
                                        attributes[valid_attribute])
                        attribute_values[valid_attribute]['std'][i]['y'] = math.sqrt(average(deviation, len(deviation)))

        i = i + 1

    result = []

    # Add bars attribute, if any
    if bars_attribute is not None:
        result.append(
            {"key": bars_attribute.name, "values": attribute_values[bars_attribute.name]['total'], "bar": True})
    # Otherwise, take incidents as bars
    else:
        result.append({"key": "Incidents", "values": incident_values, "bar": True})

    # Add every attribute
    for attribute in attribute_values:
        if bars_attribute is None or bars_attribute.name != attribute:
            for stat in attribute_values[attribute]:
                result.append({"key": "%s %s" % (stat, attribute), "values": attribute_values[attribute][stat]})

    return HttpResponse(dumps(result, default=json_util.default), content_type="application/json")


def average(values, size):
    if size > 0:
        return sum(values) / size
    else:
        return 0


@login_required
@user_passes_test(can_view_statistics)
def stats_attributes_basic(request):
    main_filter = stats_attributes_filter(request)

    attribute_selection = request.GET.getlist("attribute_selection")

    bars_attribute = None
    if request.GET['bars'] != '0':
        attribute_selection.append(request.GET['bars'])
        bars_attribute = ValidAttribute.objects.get(pk=int(request.GET['bars']))

    (incidents, all_attributes) = stats_attributes_get_data(main_filter, attribute_selection, request.user)

    incidents_with_attribute = []
    for valid_attribute in all_attributes:
        for attribute in all_attributes[valid_attribute]:
            if attribute.incident_id not in incidents_with_attribute:
                incidents_with_attribute.append(attribute.incident_id)

    attributes = {}
    if bars_attribute is not None:
        attributes[bars_attribute.name] = {}
        attributes[bars_attribute.name]['total'] = sum(int(x.value) for x in all_attributes[bars_attribute.name])

    for valid_attribute in all_attributes:
        if bars_attribute is None or bars_attribute.name != valid_attribute:
            attributes[valid_attribute] = {}
            total = sum(int(x.value) for x in all_attributes[valid_attribute])
            if request.GET.get('total', False):
                attributes[valid_attribute]['total'] = total
            if request.GET.get('average', False):
                attributes[valid_attribute]['average'] = 0
                if bars_attribute is None:
                    if request.GET.get('only_with_attribute', False):
                        attributes[valid_attribute]['average'] = average([total], len(incidents_with_attribute))
                    else:
                        attributes[valid_attribute]['average'] = average([total], len(incidents))
                else:
                    attributes[valid_attribute]['average'] = average([total], attributes[bars_attribute.name]['total'])
            if request.GET.get('deviation', False):
                attributes[valid_attribute]['standard deviation'] = 0
                if request.GET.get('average', False):
                    deviation = map(lambda x: (int(x.value) - attributes[valid_attribute]['average']) ** 2,
                                    all_attributes[valid_attribute])
                    attributes[valid_attribute]['standard deviation'] = math.sqrt(average(deviation, len(deviation)))

    result = {
        "incidents": len(incidents),
        "with_attribute": len(incidents_with_attribute),
        "attributes": attributes
    }

    return HttpResponse(dumps(result, default=json_util.default), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
# set slide=True for a sliding year (current month, 12 months backwards).
# slide=False for comparing Y-jan -> Y-dec and (Y-1)-jan -> (Y-1)-dec
def data_yearly_compare(request, year, type='all', slide=True):
    chart_data = []

    year = int(year)

    q = Q()

    if type == 'incidents':
        q = Q(is_incident=True)
    elif type == 'events':
        q = Q(is_incident=False)

    q = q & Q(confidentiality__lte=2)

    if slide:
        dates = []
        today = datetime.date.today().replace(year=year)
        for i in xrange(12):
            dates.append(today - relativedelta(months=i + 1))

        for i in xrange(12):
            chart_data.append({'date': str(dates[i].year) + "-" + str(dates[i].month),
                               str(year): Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q).filter(date__year=dates[i].year,
                                                                            date__month=dates[i].month).count(),
                               str(year - 1): Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q).filter(date__year=dates[i].year - 1,
                                                                                date__month=dates[i].month).count()
                               })

    else:
        for i in xrange(12):
            chart_data.append({'date': str(year) + "-" + str(i + 1),
                               str(year): Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q).filter(date__year=year, date__month=i + 1).count(),
                               str(year - 1): Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q).filter(date__year=year - 1,
                                                                                date__month=i + 1).count()
                               })

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_evolution(request, year, type='all', divisor='bl', slide=True):
    chart_data = []

    year = int(year)

    q = Q()

    if type == 'incidents':
        q = Q(is_incident=True)
    elif type == 'events':
        q = Q(is_incident=False)

    q = q & Q(confidentiality__lte=2)

    if divisor == 'bl':
        items = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)
    elif divisor == 'category':
        items = IncidentCategory.objects.all()

    for item in items:
        d = {}
        if divisor == 'bl':
            new_q = q & (Q(concerned_business_lines=item) | Q(main_business_lines=item) | Q(
                concerned_business_lines__in=item.get_children()))
        elif divisor == 'category':
            new_q = q & Q(category=item)

        d['label'] = item.name
        if slide:
            today = datetime.datetime.now().replace(day=1, year=year)
            dates = Q()
            for i in xrange(12):
                dates |= Q(date__month=(today - relativedelta(months=i)).month,
                           date__year=(today - relativedelta(months=i)).year)
            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(new_q & dates).distinct().count()
            dates = Q()
            for i in xrange(12):
                dates |= Q(date__month=(today - relativedelta(months=i)).month,
                           date__year=(today - relativedelta(months=i)).year - 1)

            previous_value = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(new_q & dates).distinct().count()
        else:
            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(new_q & Q(date__year=year)).distinct().count()
            previous_value = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(new_q & Q(date__year=year - 1)).distinct().count()

        if previous_value > 0:
            delta = d['value'] - previous_value
            delta = delta / float(previous_value)
            delta = delta * 100
            delta = int(round(delta))
            if delta > 0:
                d['text'] = "+" + str(delta) + "%"
            else:
                d['text'] = str(delta) + "%"
        else:
            d['text'] = "new!"

        d['text'] = str(d['text'])
        if d['value'] != 0 or previous_value != 0:
            chart_data.append(d)

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_incidents(request):
    chart_data = []

    dates = []
    today = datetime.date.today()
    for i in xrange(12):
        dates.append(today - relativedelta(months=i + 1))
    for i in xrange(12):
        chart_data.append({'date': str(dates[i].year) + "-" + str(dates[i].month),
                           today.year - 1: Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(date__year=dates[i].year, date__month=dates[i].month,
                                                                   confidentiality__lte=2).count()})

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_field(request, field):
    field_dict = {}
    total = 0

    q = Q(date__year=datetime.date.today().year)

    for i in Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q):
        field_dict[str(getattr(i, field))] = field_dict.get(str(getattr(i, field)), 0) + 1
        total += 1

    chart_data = []
    for label, value in field_dict.items():
        if field == 'severity':
            label += "/4"
        chart_data.append(
            {'label': label, 'value': value, 'percentage': float(str(round(float(value) / total, 2) * 100))})

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_bl(request, year=datetime.date.today().year, type='all'):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)

    chart_data = []
    total = 0

    q = Q(date__year=year)

    if type == 'incidents':
        q = q & Q(is_incident=True)
    elif type == 'events':
        q = q & Q(is_incident=False)

    q = q & Q(confidentiality__lte=2)

    for bl in bls:
        d = {}
        d['label'] = bl.name
        d['value'] = bl.get_incident_count(q)
        if d['value'] > 0:
            chart_data.append(d)
        total += d['value']

    for d in chart_data:
        d['percentage'] = float(str(round(float(d['value']) / total, 2) * 100))

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type="application/json")


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_bl_detection(request):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)
    q = Q(date__year=datetime.datetime.now().year)
    q = q & Q(confidentiality__lte=2)

    chart_data = []

    for bl in bls:
        d = {}
        d['entry'] = bl.name
        cert = bl.get_incident_count(q & Q(detection__name='CERT'))
        ext = bl.get_incident_count(q & Q(detection__name='External'))
        d['CERT'] = cert
        d['External'] = ext
        if d['CERT'] != 0 or d['External'] != 0:
            chart_data.append(d)

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_bl_severity(request):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)

    q = Q(date__year=datetime.datetime.now().year)
    q = q & Q(confidentiality__lte=2)

    chart_data = []

    for bl in bls:
        d = {}
        d['entry'] = bl.name

        append = False
        for i in xrange(4):
            d[str(i + 1) + '/4'] = bl.get_incident_count(q & Q(severity=i + 1))
            if d[str(i + 1) + '/4'] > 0:
                append = True

        if append:
            chart_data.append(d)

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_bl_category(request):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)
    categories = IncidentCategory.objects.all()

    q = Q(date__year=datetime.datetime.now().year)
    q = q & Q(confidentiality__lte=2)

    chart_data = []

    for bl in bls:

        d = {}
        d['entry'] = bl.name

        append = False
        for c in categories:
            d[c.name] = bl.get_incident_count(q & Q(category=c))
            if d[c.name] > 0:
                append = True

        if append:
            chart_data.append(d)

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def data_yearly_bl_plan(request):
    bls = BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics').filter(depth=1)
    plans = Label.objects.filter(group__name='plan')

    q = Q(date__year=datetime.datetime.now().year)
    q = q & Q(confidentiality__lte=2)

    chart_data = []

    for bl in bls:

        d = {}
        d['entry'] = bl.name

        append = False
        for p in plans:
            d[p.name] = bl.get_incident_count(q & Q(plan=p))
            if d[p.name] > 0:
                append = True

        if append:
            chart_data.append(d)

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def data_incident_variation(request, business_line, num_months=3):
    bl = get_object_or_404(BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics'), name=business_line)

    categories = IncidentCategory.objects.all()

    chart_data = []

    q = Q(concerned_business_lines=bl) | Q(main_business_lines=bl) | Q(concerned_business_lines__in=bl.get_children())
    q &= Q(confidentiality__lte=2)

    total = 0
    total_previous = 0
    for cat in categories:

        d = {}
        current = datetime.datetime.today() - relativedelta(months=1)

        d['category'] = cat.name
        current_month = q & Q(date__month=current.month, date__year=current.year, category=cat)

        d['values'] = {}
        d['values']['new'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(current_month).distinct().count()
        total += d['values']['new']

        previous = current - relativedelta(months=1)

        previous_month = q & Q(date__month=previous.month, date__year=previous.year, category=cat)
        previous_count = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(previous_month).distinct().count()
        d['values']['variation'] = d['values']['new'] - previous_count

        total_previous += previous_count

        if d['values']['variation'] > 0:
            d['values']['variation'] = "+" + str(d['values']['variation'])
        else:
            d['values']['variation'] = str(d['values']['variation'])

        if d['values']['variation'] != "0" or d['values']['new'] != 0:
            chart_data.append(d)

    if total - total_previous > 0:
        total_previous = "+" + str(total - total_previous)
    else:
        total_previous = str(total - total_previous)

    chart_data.append({'category': 'Total', 'values': {'new': total, 'variation': total_previous}})

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def data_quarterly_bl(request, business_line, divisor, num_months=3, is_incident=True):
    bl = get_object_or_404(BusinessLine.authorization.for_user(request.user, 'incidents.view_statistics'),
                           name=business_line)
    children = bl.get_children()

    q = Q(main_business_lines=bl) | Q(concerned_business_lines=bl) | Q(concerned_business_lines__in=children)
    q = q & Q(confidentiality__lte=2)

    chart_data = []

    if divisor == 'incidents':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['label'] = cal[today.month - 1]
            date_q = q & Q(date__month=today.month, date__year=today.year)

            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                date_q).distinct().count()
            d['text'] = d['value']

            chart_data.append(d)

    elif divisor == 'severity':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['entry'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            d['1/4'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                Q(severity=1) & q_date).distinct().count()
            d['2/4'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                Q(severity=2) & q_date).distinct().count()
            d['3/4'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                Q(severity=3) & q_date).distinct().count()
            d['4/4'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                Q(severity=4) & q_date).distinct().count()

            chart_data.append(d)

    elif divisor == 'category':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['entry'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            for cat in IncidentCategory.objects.all():
                d[cat.name] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    q_date & Q(category=cat)).distinct().count()

            chart_data.append(d)

    elif divisor == 'entity':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['entry'] = cal[today.month - 1]

            q_date = q & Q(date__month=today.month, date__year=today.year)
            d[bl.name] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                q_date).distinct().count()

            for entity in bl.get_children():
                d[entity.name] = entity.get_incident_count(q_date)
                d[bl.name] -= d[entity.name]

            chart_data.append(d)

    elif divisor == 'actor':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['entry'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            for actor in Label.objects.filter(group__name='actor').distinct():
                d[actor.name] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                    q_date & Q(actor=actor)).distinct().count()

            chart_data.append(d)

    elif divisor == 'monitoring':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['label'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                q_date & Q(plan__name='A')).distinct().count()
            d['text'] = d['value']

            chart_data.append(d)

    elif divisor == 'open':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['label'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                q_date & Q(status='O')).distinct().count()
            d['text'] = d['value']
            chart_data.append(d)

    elif divisor == 'blocked':
        for i in xrange(num_months):
            d = {}

            today = datetime.datetime.today() - relativedelta(months=num_months - i)
            d['label'] = cal[today.month - 1]
            q_date = q & Q(date__month=today.month, date__year=today.year)

            d['value'] = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(
                q_date & Q(status='B')).distinct().count()
            d['text'] = d['value']
            chart_data.append(d)

    chart_data = delete_empty_keys(chart_data)

    return HttpResponse(dumps(chart_data), content_type='application/json')


@login_required
@user_passes_test(can_view_statistics)
def quarterly_major(request, start_date=None, num_months=3):
    q_major = Q(is_major=True)
    q_confid = Q(confidentiality__lte=2)
    balecats = BaleCategory.objects.filter(Q(parent_category__isnull=False))
    certcats = IncidentCategory.objects.all()
    parent_bls = BusinessLine.get_root_nodes()

    num_months = int(num_months)

    bale = []
    cert = []
    bls = []

    if start_date is None:
        today = datetime.datetime.today()
    else:
        today = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    cert.append(['Category'])
    for i in xrange(num_months):
        then = today - relativedelta(months=num_months - i)
        cert[0].append(cal[then.month - 1])
    cert[0].append('Total')
    for certcat in certcats:
        line = []
        q_certcat = Q(category=certcat) & q_major
        line.append(certcat.name)
        add = False
        total = 0
        for i in xrange(num_months):
            then = today - relativedelta(months=num_months - i)
            q_date = q_certcat & Q(date__month=then.month, date__year=then.year)
            count = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q_date & q_confid).count()
            line.append(count)

            if count != 0:
                add = True
                total += count

        line.append(total)

        if add:
            cert.append(line)

    bale.append(['Bale category'])
    for i in xrange(num_months):
        then = today - relativedelta(months=num_months - i)
        bale[0].append(cal[then.month - 1])

    for balecat in balecats:
        line = []
        q_balecat = Q(category__bale_subcategory=balecat) & q_major
        line.append(balecat.__unicode__)
        add = False
        for i in xrange(num_months):
            then = today - relativedelta(months=num_months - i)
            q_date = q_balecat & Q(date__month=then.month, date__year=then.year)
            count = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q_date & q_confid).count()
            line.append(count)
            if count != 0:
                add = True

        if add:
            bale.append(line)

    bls.append(['Business Line'])
    for i in xrange(num_months):
        then = today - relativedelta(months=num_months - i)
        bls[0].append(cal[then.month - 1])
    bls[0].append('Total')

    for bl in parent_bls:
        line = []
        q_bl = Q(main_business_lines=bl) & q_major
        line.append(bl.__unicode__)
        add = False

        total = 0
        for i in xrange(num_months):
            then = today - relativedelta(months=num_months - i)
            q_date = q_bl & Q(date__month=then.month, date__year=then.year)

            count = Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(q_date & q_confid).count()
            line.append(count)
            if count != 0:
                add = True
                total += count
        line.append(total)
        if add:
            bls.append(line)

    total_major = 0
    for i in xrange(num_months):
        d = today - relativedelta(months=num_months - i)
        total_major += Incident.authorization.for_user(request.user, 'incidents.view_statistics').filter(date__month=d.month, date__year=d.year, confidentiality__lte=2).count()

    past_months = Q()
    for i in xrange(num_months):
        d = today - relativedelta(months=num_months - i)
        past_months |= Q(date__month=d.month, date__year=d.year)

    return render(request, 'stats/major.html', {'bale': bale, 'cert': cert, 'total_major': total_major, 'bls': bls,
                                                'incident_list': Incident.authorization.for_user(request.user, 'incidents.view_incidents').filter(
                                                    q_major & past_months & q_confid).order_by('-date')})


# Dashboard =======================================================

def incidents_order(request):
    order_param = request.GET.get('order_by', 'date')
    asc = request.GET.get('asc', 'false')
    order_by = order_param

    if order_param == 'last_action':
        order_by = 'comments__date__max'

    if asc == 'false':
        order_by = "-%s" % order_by

    return (order_by, order_param, asc)


def incident_display(request, filter, incident_view=True, paginated=True):
    (order_by, order_param, asc) = incidents_order(request)

    permissions = 'incidents.view_incidents'

    if order_param == 'last_action':
        incident_list = Incident.authorization.for_user(request.user, permissions).filter(filter).annotate(
            Max('comments__date')).order_by(order_by)
    else:
        pre_list = Incident.authorization.for_user(request.user, permissions)
        incident_list = pre_list.filter(filter).order_by(order_by)

    if paginated:
        page = request.GET.get('page', 1)
        incidents_per_page = request.user.profile.incident_number
        p = Paginator(incident_list, incidents_per_page)

        try:
            incident_list = p.page(page)
        except (PageNotAnInteger, EmptyPage):
            incident_list = p.page(1)

    return render(request, 'events/table.html', {
        'incident_list': incident_list,
        'incident_view': incident_view,
        'order_param': order_param,
        'asc': asc,
        'incident_show_id': settings.INCIDENT_SHOW_ID
    })


@login_required
@user_passes_test(is_incident_viewer)
def dashboard_main(request):
    return render(request, 'dashboard/index.html')


@login_required
@user_passes_test(is_incident_viewer)
def dashboard_starred(request):
    return incident_display(request, Q(is_starred=True) & ~Q(status='C'), True, False)


@login_required
@user_passes_test(is_incident_viewer)
def dashboard_open(request):
    return incident_display(request, Q(status='O'))


@login_required
@user_passes_test(is_incident_viewer)
def dashboard_blocked(request):
    return incident_display(request, Q(status='B'))


@login_required
@user_passes_test(is_incident_viewer)
def dashboard_old(request):
    permissions = ['incidents.view_incidents', 'incidents.handle_incidents']
    incident_list = Incident.authorization.for_user(request.user, permissions).filter(status='O').annotate(
        Max('comments__date')).order_by('comments__date__max')[
                    :20]

    return render(request, 'events/table.html', {
        'incident_list': incident_list,
        'incident_view': True,
        'order_param': 'last_action',
        'asc': 'true'
    })


# User profile ============================================================
@login_required
def user_self_service(request):
    user_fields = []
    if settings.USER_SELF_SERVICE.get('CHANGE_EMAIL', True):
        user_fields.append('email')
    if settings.USER_SELF_SERVICE.get('CHANGE_NAMES', True):
        user_fields.extend(('first_name', 'last_name'))
    if len(user_fields):
        user_form = modelform_factory(User, fields=user_fields)
    else:
        user_form = False
    if settings.USER_SELF_SERVICE.get('CHANGE_PROFILE', True):
        profile_form = modelform_factory(Profile, exclude=('user',))
    else:
        profile_form = False
    if request.method == "POST":
        post_data = request.POST.dict()
        if user_form:
            user_data = {field:post_data[field] for field in user_fields if field in post_data}
            user_form = user_form(user_data, instance=request.user)
            if user_form.is_valid():
                user_form.save()
        if profile_form:
            profile_data = {field:post_data[field] for field in profile_form.base_fields.keys() if field in post_data}
            profile_form = profile_form(profile_data, instance=request.user.profile)
            if profile_form.is_valid():
                profile_form.save()
    else:
        if user_form:
            user_form = user_form(instance=request.user)
        if profile_form:
            profile_form = profile_form(instance=request.user.profile)
    if settings.USER_SELF_SERVICE.get('CHANGE_PASSWORD', True):
        password_form = PasswordChangeForm(request.user)
    else:
        password_form = False
    return render(request, 'user/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form
    })


@login_required
@require_POST
def user_change_password(request):
    if not settings.USER_SELF_SERVICE.get('CHANGE_PASSWORD', True):
        messages.error(request, "Error: Password change administratively disabled.")
        return HttpResponseServerError(dumps({'status': 'error', 'errors': ['password change disabled.',]}),
                                       content_type="application/json")
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Success! Password updated.")
            return HttpResponse(dumps({'status': 'success'}), content_type="application/json")

    ret = {'status': 'error', 'errors': form.errors}
    messages.error(request, form.errors)
    return HttpResponseServerError(dumps(ret), content_type="application/json")
