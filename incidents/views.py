# -*- coding: utf-8 -*-


# Create your views here.
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from incidents.models import Incident, Comments, model_status_changed
from incidents.models import Label, Log
from incidents.models import Attribute, ValidAttribute, IncidentTemplate, Profile
from incidents.forms import IncidentForm, CommentForm

from incidents.authorization.decorator import authorization_required
from fir.config.base import INSTALLED_APPS
import importlib

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from fir.decorators import fir_auth_required
from django.core import serializers

from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext
from json import dumps
from django.template import Template

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.forms.models import model_to_dict, modelform_factory
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib import messages

import re, datetime

from fir_artifacts import artifacts as libartifacts

APP_HOOKS = {}

for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        try:
            h = importlib.import_module('{}.hooks'.format(app))
            APP_HOOKS[app_name] = h.hooks
        except ImportError:
            pass



# helper =========================================================


def is_incident_handler(user):
    return user.has_perm('incidents.handle_incidents', obj=Incident)


def is_incident_reporter(user):
    return user.has_perm('incidents.handle_incidents', obj=Incident) or user.has_perm('incidents.report_events',
                                                                                      obj=Incident)


def is_incident_viewer(user):
    return user.has_perm('incidents.view_incidents', obj=Incident) or user.has_perm('incidents.report_events',
                                                                                    obj=Incident)


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
                log("Login success", user)
                init_session(request)
                return redirect('dashboard:main')
            else:
                log("Login attempted from locked account", user)
                return HttpResponse('Account disabled')
        else:
            log("Login failed for "+username, None)
            return render(request, 'incidents/login.html', {'error': 'error'})
    else:
        return render(request, 'incidents/login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    if settings.LOGOUT_REDIRECT_URL is not None:
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return redirect('/login/')

def init_session(request):
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
        print("DEBUG: Not logging")
        return

    log = Log()
    log.what = what
    log.who = user
    log.incident = incident
    log.comment = comment

    log.save()


# incidents =======================================================

@fir_auth_required
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

@fir_auth_required
@user_passes_test(is_incident_viewer)
def incident_display(request, is_incident=False, is_search=False):
    query_string = request.GET.get("q", "").strip()

    if is_search and not query_string:
        return redirect("incidents:index")
    params = {
        "incident_view": is_incident,
        "query_string": query_string,
        "incident_show_id": getattr(settings, "INCIDENT_SHOW_ID", False),
        "incident_id_prefix": getattr(settings, "INCIDENT_ID_PREFIX", ""),
    }
    return render(request, "events/index-all.html", params)

@fir_auth_required
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


@fir_auth_required
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


@fir_auth_required
@authorization_required("incidents.handle_incidents", Incident, view_arg="incident_id")
def edit_incident(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, "incidents.handle_incidents"),
            pk=incident_id,
        )
    else:
        i = authorization_target
    starred = i.is_starred

    if request.method == "POST":
        previous_status = i.status
        form = IncidentForm(request.POST, instance=i, for_user=request.user)

        if form.is_valid():
            if previous_status == form.cleaned_data["status"]:
                previous_status = None
            # update main BL
            form.save()
            if previous_status is not None:
                model_status_changed.send(
                    sender=Incident, instance=i, previous_status=previous_status
                )
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

    return render(request, "events/new.html", {"i": i, "form": form, "mode": "edit"})


@fir_auth_required
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


@fir_auth_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def change_status(request, incident_id, status, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
            pk=incident_id)
    else:
        i = authorization_target
    previous_status = i.status
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
    model_status_changed.send(sender=Incident, instance=i, previous_status=previous_status)
    return redirect('dashboard:main')


# attributes ================================================================


@fir_auth_required
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

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'events/_attributes.html', {'attributes': i.attribute_set.all(), 'event': i})

    return redirect('incidents:details', incident_id=incident_id)


@fir_auth_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def delete_attribute(request, incident_id, attribute_id, authorization_target=None):
    a = get_object_or_404(Attribute, pk=attribute_id)
    if request.method == "POST":
        a.delete()
    return redirect('incidents:details', incident_id=incident_id)


# comments ==================================================================

@fir_auth_required
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


@fir_auth_required
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


@fir_auth_required
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
                if c.action.name[0] != c.incident.status:
                    previous_status = c.incident.status
                    c.incident.status = c.action.name[0]
                    c.incident.save()
                    model_status_changed.send(sender=Incident, instance=c.incident, previous_status=previous_status)

            i.refresh_artifacts(c.comment)

            return render(request, 'events/_comment.html', {'comment': c, 'event': i})
        else:
            ret = {'status': 'error', 'errors': comment_form.errors}
            return HttpResponseServerError(dumps(ret), content_type="application/json")


# events ====================================================================

@fir_auth_required
@user_passes_test(is_incident_viewer)
def event_index(request):
    return index(request, False)


# ajax ======================================================================

@fir_auth_required
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

            if com.action.name in ['Closed', 'Opened', 'Blocked'] and com.incident.status != com.action.name[0]:
                previous_status = com.incident.status
                com.incident.status = com.action.name[0]
                com.incident.save()
                model_status_changed.send(sender=Incident, instance=com.incident, previous_status=previous_status)

            return render(request, 'events/_comment.html', {'event': i, 'comment': com})
        else:
            ret = {'status': 'error', 'errors': comment_form.errors}
            return HttpResponseServerError(dumps(ret), content_type="application/json")

    return redirect('incidents:details', incident_id=incident_id)


# User ==========================================================================

@fir_auth_required
def toggle_closed(request):
    request.user.profile.hide_closed = not request.user.profile.hide_closed
    request.user.profile.save()
    response = {'status': 'ok', 'hide_closed': request.user.profile.hide_closed}
    return HttpResponse(dumps(response), content_type="application/json")


# Dashboard =======================================================

@fir_auth_required
@user_passes_test(is_incident_viewer)
def dashboard_main(request):
    params = {
        "is_dashboard": True,
        "incident_show_id": getattr(settings, "INCIDENT_SHOW_ID", False),
        "incident_id_prefix": getattr(settings, "INCIDENT_ID_PREFIX", ""),
    }

    return render(request, "dashboard/index.html", params)

# User profile ============================================================
@fir_auth_required
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

    oidc_enabled = (
        "fir_auth_oidc.backend.ClaimMappingOIDCAuthenticationBackend"
        in settings.AUTHENTICATION_BACKENDS
    )

    return render(request, "user/profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "password_form": password_form,
        "oidc_enabled": oidc_enabled,
    })


@fir_auth_required
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
