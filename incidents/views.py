# -*- coding: utf-8 -*-
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

from incidents.models import Incident, Comments, model_status_changed
from incidents.models import Label, Log, IncidentStatus
from incidents.models import Attribute, IncidentTemplate, Profile
from incidents.forms import IncidentForm, CommentForm

from incidents.authorization.decorator import authorization_required
from fir.config.base import INSTALLED_APPS
import importlib

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from fir.decorators import fir_auth_required

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect, resolve_url
from django.template import RequestContext
from django.template import Template

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.urls.exceptions import NoReverseMatch
from django.forms.models import model_to_dict, modelform_factory
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.contrib import messages

import copy

from fir_artifacts import artifacts as libartifacts

APP_HOOKS = {}

for app in INSTALLED_APPS:
    if app.startswith("fir_"):
        app_name = app[4:]
        try:
            h = importlib.import_module("{}.hooks".format(app))
            APP_HOOKS[app_name] = h.hooks
        except ImportError:
            pass


# helper =========================================================


def is_incident_handler(user):
    return user.has_perm("incidents.handle_incidents", obj=Incident)


def is_incident_reporter(user):
    return user.has_perm("incidents.handle_incidents", obj=Incident) or user.has_perm(
        "incidents.report_events", obj=Incident
    )


def is_incident_viewer(user):
    return user.has_perm("incidents.view_incidents", obj=Incident) or user.has_perm(
        "incidents.report_events", obj=Incident
    )


comment_permissions = [
    "incidents.handle_incidents",
]
if getattr(settings, "INCIDENT_VIEWER_CAN_COMMENT", False):
    comment_permissions.append("incidents.view_incidents")


# login / logout =================================================


def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        redirect_to = request.POST.get("next", request.GET.get("next", ""))

        if not url_has_allowed_host_and_scheme(
            url=redirect_to, allowed_hosts=request.get_host()
        ):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        try:
            redirect_to = redirect(redirect_to)
        except NoReverseMatch:
            redirect_to = redirect(resolve_url(settings.LOGIN_REDIRECT_URL))

        user = authenticate(username=username, password=password, request=request)
        if user is not None:
            if not request.POST.get("remember", None):
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
                init_session(request)
                return redirect_to
            else:
                return HttpResponse("Account disabled")
        else:
            return render(request, "incidents/login.html", {"error": "error"})
    else:
        return render(request, "incidents/login.html")


def user_logout(request):
    logout(request)
    request.session.flush()
    if settings.LOGOUT_REDIRECT_URL is not None:
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return redirect("/login/")


def init_session(request):
    # Put all the incident templates in the session
    request.session["incident_templates"] = list(
        IncidentTemplate.objects.exclude(name="default").values("name")
    )
    request.session["has_incident_templates"] = (
        len(request.session["incident_templates"]) > 0
    )
    request.session["can_report_event"] = request.user.has_perm(
        "incidents.handle_incidents", obj=Incident
    ) or request.user.has_perm("incidents.report_events", obj=Incident)


# incidents =======================================================


@fir_auth_required
@authorization_required("incidents.view_incidents", Incident, view_arg="incident_id")
def followup(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(
                request.user, ["incidents.view_incidents", "incidents.handle_incidents"]
            ),
            pk=incident_id,
        )
    else:
        i = authorization_target
    comments = i.comments_set.all().order_by("date")

    return render(
        request,
        "incidents/followup.html",
        {
            "incident": i,
            "comments": comments,
            "incident_show_id": getattr(settings, "INCIDENT_SHOW_ID", False),
        },
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
        "final_status": IncidentStatus.objects.filter(flag="final"),
    }
    return render(request, "events/index-all.html", params)


@fir_auth_required
@authorization_required("incidents.view_incidents", Incident, view_arg="incident_id")
def details(request, incident_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(
            Incident.authorization.for_user(
                request.user, ["incidents.view_incidents", "incidents.handle_incidents"]
            ),
            pk=incident_id,
        )
    else:
        i = authorization_target
    form = CommentForm()
    if not request.user.has_perm("incidents.handle_incidents", obj=i):
        form.fields["action"].queryset = Label.objects.filter(
            group__name="action"
        ).exclude(name__in=["Closed", "Opened", "Blocked"])

    artifacts, artifacts_count, correlated_count = libartifacts.all_for_object(
        i, user=request.user
    )

    valid_attributes = i.category.validattribute_set.all()
    attributes = i.attribute_set.all()

    comments = i.comments_set.all().order_by("date")

    return render(
        request,
        "events/detail-all.html",
        {
            "event": i,
            "comment_form": form,
            "correlated_count": correlated_count,
            "artifacts_count": artifacts_count,
            "artifacts": artifacts,
            "attributes": attributes,
            "valid_attributes": valid_attributes,
            "comments": comments,
            "incident_show_id": getattr(settings, "INCIDENT_SHOW_ID", False),
            "status": IncidentStatus.objects.all(),
        },
    )


@fir_auth_required
@user_passes_test(is_incident_reporter)
def new_event(request):
    if request.method == "POST":
        form = IncidentForm(request.POST, for_user=request.user)

        if form.is_valid():
            i = form.save(commit=False)

            if not form.cleaned_data["is_major"]:
                i.is_major = form.cleaned_data["category"].is_major

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
        template = request.GET.get("template", "default")
        try:
            template = IncidentTemplate.objects.get(name=template)
            data = model_to_dict(template)
            data["description"] = Template(data["description"]).render(
                RequestContext(request)
            )
        except ObjectDoesNotExist:
            data = {}
        form = IncidentForm(initial=data, for_user=request.user)

    return render(request, "events/new.html", {"form": form, "mode": "new"})


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
        previous_incident = copy.copy(i)
        form = IncidentForm(request.POST, instance=i, for_user=request.user)

        if form.is_valid():
            Comments.create_diff_comment(
                previous_incident, form.cleaned_data, request.user
            )
            form.save()
            if previous_incident.status != form.cleaned_data["status"]:
                model_status_changed.send(
                    sender=Incident,
                    instance=i,
                    previous_status=previous_incident.status,
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
@authorization_required("incidents.handle_incidents", Incident, view_arg="incident_id")
def delete_incident(request, incident_id, authorization_target=None):
    if request.method == "POST":
        if authorization_target is None:
            i = get_object_or_404(
                Incident.authorization.for_user(
                    request.user, "incidents.handle_incidents"
                ),
                pk=incident_id,
            )
        else:
            i = authorization_target
        msg = "Incident '%s' deleted." % i.subject
        i.delete()
        return HttpResponse(msg)
    else:
        return redirect("incidents:index")


# events ====================================================================


@fir_auth_required
@user_passes_test(is_incident_viewer)
def event_index(request):
    return index(request, False)


# Dashboard =======================================================


@fir_auth_required
@user_passes_test(is_incident_viewer)
def dashboard_main(request):
    params = {
        "is_dashboard": True,
        "incident_show_id": getattr(settings, "INCIDENT_SHOW_ID", False),
        "incident_id_prefix": getattr(settings, "INCIDENT_ID_PREFIX", ""),
        "initial_status": IncidentStatus.objects.get(flag="initial"),
        "final_status": IncidentStatus.objects.filter(flag="final"),
        "status": IncidentStatus.objects.all(),
    }

    return render(request, "dashboard/index.html", params)


# User profile ============================================================
@fir_auth_required
def user_profile(request):
    user_fields = []
    if settings.USER_SELF_SERVICE.get("CHANGE_EMAIL", True):
        user_fields.append("email")
    if settings.USER_SELF_SERVICE.get("CHANGE_NAMES", True):
        user_fields.extend(("first_name", "last_name"))
    if len(user_fields):
        user_form = modelform_factory(User, fields=user_fields)
    else:
        user_form = False
    if settings.USER_SELF_SERVICE.get("CHANGE_PROFILE", True):
        profile_form = modelform_factory(Profile, exclude=("user",))
    else:
        profile_form = False
    if request.method == "POST":
        post_data = request.POST.dict()
        if user_form:
            user_data = {
                field: post_data[field] for field in user_fields if field in post_data
            }
            user_form = user_form(user_data, instance=request.user)
            if user_form.is_valid():
                user_form.save()
        if profile_form:
            profile_data = {
                field: post_data[field]
                for field in profile_form.base_fields.keys()
                if field in post_data
            }
            profile_form = profile_form(profile_data, instance=request.user.profile)
            if profile_form.is_valid():
                profile_form.save()
    else:
        if user_form:
            user_form = user_form(instance=request.user)
        if profile_form:
            profile_form = profile_form(instance=request.user.profile)
    if settings.USER_SELF_SERVICE.get("CHANGE_PASSWORD", True):
        password_form = PasswordChangeForm(request.user)
    else:
        password_form = False

    oidc_enabled = (
        "fir_auth_oidc.backend.ClaimMappingOIDCAuthenticationBackend"
        in settings.AUTHENTICATION_BACKENDS
    )

    return render(
        request,
        "user/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "password_form": password_form,
            "oidc_enabled": oidc_enabled,
        },
    )
