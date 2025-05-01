from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from fir.decorators import fir_auth_required
from fir_stats.permissions import can_view_statistics

from incidents.models import (
    BusinessLine,
    Incident,
    IncidentCategory,
    SeverityChoice,
    ValidAttribute,
    IncidentStatus,
)
from incidents.forms import IncidentForm


@fir_auth_required
@user_passes_test(can_view_statistics)
def yearly_stats(request):
    return render(request, "fir_stats/yearly.html")


@fir_auth_required
@user_passes_test(can_view_statistics)
def quarterly_stats(request):
    bls = list(
        BusinessLine.authorization.for_user(request.user, "incidents.view_statistics")
    )
    bl_all = BusinessLine(name="All")
    bls.insert(0, bl_all)
    selected_bl = request.GET.get("bl", "All")
    status = IncidentStatus.objects.all()

    for b in bls:
        if b.name == selected_bl:
            selected_bl = b

    # if BL does not exists or user is not authorized to view its statistics
    if isinstance(selected_bl, str):
        return redirect("stats:quarterly")

    return render(
        request,
        "fir_stats/quarterly.html",
        {
            "bl": selected_bl,
            "bls": bls,
            "status": status,
        },
    )


@fir_auth_required
def close_old(request):
    now = datetime.now()
    query = Q(date__lt=datetime(now.year, now.month, 1) - relativedelta(month=3)) & ~Q(
        status="C"
    )
    old = Incident.authorization.for_user(
        request.user, "incidents.handle_incidents"
    ).filter(query)

    for i in old:
        if i.status != "C":
            i.close_timeout(username=request.user.username)

    return redirect("stats:quarterly")


@fir_auth_required
@user_passes_test(can_view_statistics)
def compare(request):
    year = datetime.now().year - 1
    return render(request, "fir_stats/compare.html", {"year": year})


@fir_auth_required
@user_passes_test(can_view_statistics)
def sandbox(request):
    categories = IncidentCategory.objects.all()
    status = IncidentStatus.objects.all()
    display_severity_op = all(
        [a.name.isnumeric() for a in SeverityChoice.objects.all()]
    )
    form = IncidentForm(for_user=request.user, permissions="incidents.view_statistics")

    return render(
        request,
        "fir_stats/sandbox.html",
        {
            "form": form,
            "categories": categories,
            "display_severity_op": display_severity_op,
            "status": status,
        },
    )


@fir_auth_required
@user_passes_test(can_view_statistics)
def attributes(request):
    form = IncidentForm(for_user=request.user, permissions="incidents.view_statistics")
    categories = IncidentCategory.objects.all()
    display_severity_op = all(
        [a.name.isnumeric() for a in SeverityChoice.objects.all()]
    )
    attributes = ValidAttribute.objects.exclude(unit__isnull=True)

    return render(
        request,
        "fir_stats/attributes.html",
        {
            "form": form,
            "categories": categories,
            "attributes": attributes,
            "display_severity_op": display_severity_op,
        },
    )


@fir_auth_required
@user_passes_test(can_view_statistics)
def major(request):
    return render(
        request,
        "fir_stats/major.html",
    )
