from datetime import datetime
from dateutil.relativedelta import relativedelta
from calendar import month_abbr

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
    # BaleCategory,
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

    for b in bls:
        if b.name == selected_bl:
            selected_bl = b

    # if BL does not exists or user is not authorized to view its statistics
    if isinstance(selected_bl, str):
        return redirect("fir_stats/quarterly.html")

    return render(
        request,
        "fir_stats/quarterly.html",
        {
            "bl": selected_bl,
            "bls": bls,
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

    return redirect("stats:quarterly_stats")


@fir_auth_required
@user_passes_test(can_view_statistics)
def compare(request):
    year = datetime.now().year - 1
    return render(request, "fir_stats/compare.html", {"year": year})


@fir_auth_required
@user_passes_test(can_view_statistics)
def sandbox(request):
    categories = IncidentCategory.objects.all()
    display_severity_op = all([a.name.isnumeric() for a in SeverityChoice.objects.all()])
    form = IncidentForm(for_user=request.user, permissions="incidents.view_statistics")

    return render(
        request,
        "fir_stats/sandbox.html",
        {
            "form": form,
            "categories": categories,
            "display_severity_op": display_severity_op,
        },
    )


@fir_auth_required
@user_passes_test(can_view_statistics)
def attributes(request):
    form = IncidentForm(for_user=request.user, permissions="incidents.view_statistics")
    categories = IncidentCategory.objects.all()
    display_severity_op = all([a.name.isnumeric() for a in SeverityChoice.objects.all()])
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


# @fir_auth_required
# @user_passes_test(can_view_statistics)
# def major(request):
#    q_major = Q(is_major=True)
#    balecats = BaleCategory.objects.filter(Q(parent_category__isnull=False))
#    certcats = IncidentCategory.objects.all()
#    parent_bls = BusinessLine.get_root_nodes()
#
#    num_months = 3
#
#    cal = [a.lower() for a in month_abbr if a]
#    bale = []
#    cert = []
#    bls = []
#
#    today = datetime.today()
#
#    cert.append(["Category"])
#    for i in range(num_months):
#        then = today - relativedelta(months=num_months - i)
#        cert[0].append(cal[then.month - 1])
#
#    cert[0].append("Total")
#    for certcat in certcats:
#        line = []
#        q_certcat = Q(category=certcat) & q_major
#        line.append(certcat.name)
#        add = False
#        total = 0
#        for i in range(num_months):
#            then = today - relativedelta(months=num_months - i)
#            q_date = q_certcat & Q(date__month=then.month, date__year=then.year)
#            count = (
#                Incident.authorization.for_user(
#                    request.user, "incidents.view_statistics"
#                )
#                .filter(q_date)
#                .count()
#            )
#            line.append(count)
#
#            if count != 0:
#                add = True
#                total += count
#
#        line.append(total)
#
#        if add:
#            cert.append(line)
#
#    bale.append(["Bale category"])
#    for i in range(num_months):
#        then = today - relativedelta(months=num_months - i)
#        bale[0].append(cal[then.month - 1])
#
#    for balecat in balecats:
#        line = []
#        q_balecat = Q(category__bale_subcategory=balecat) & q_major
#        line.append(str(balecat))
#        add = False
#        for i in range(num_months):
#            then = today - relativedelta(months=num_months - i)
#            q_date = q_balecat & Q(date__month=then.month, date__year=then.year)
#            count = (
#                Incident.authorization.for_user(
#                    request.user, "incidents.view_statistics"
#                )
#                .filter(q_date)
#                .count()
#            )
#            line.append(count)
#            if count != 0:
#                add = True
#
#        if add:
#            bale.append(line)
#
#    bls.append(["Business Line"])
#    for i in range(num_months):
#        then = today - relativedelta(months=num_months - i)
#        bls[0].append(cal[then.month - 1])
#    bls[0].append("Total")
#
#    for bl in parent_bls:
#        line = []
#        q_bl = Q(main_business_lines=bl) & q_major
#        line.append(str(bl))
#        add = False
#
#        total = 0
#        for i in range(num_months):
#            then = today - relativedelta(months=num_months - i)
#            q_date = q_bl & Q(date__month=then.month, date__year=then.year)
#
#            count = (
#                Incident.authorization.for_user(
#                    request.user, "incidents.view_statistics"
#                )
#                .filter(q_date)
#                .count()
#            )
#            line.append(count)
#            if count != 0:
#                add = True
#                total += count
#        line.append(total)
#        if add:
#            bls.append(line)
#
#    total_major = 0
#    for i in range(num_months):
#        d = today - relativedelta(months=num_months - i)
#        total_major += (
#            Incident.authorization.for_user(request.user, "incidents.view_statistics")
#            .filter(date__month=d.month, date__year=d.year)
#            .count()
#        )
#
#    past_months = Q()
#    for i in range(num_months):
#        d = today - relativedelta(months=num_months - i)
#        past_months |= Q(date__month=d.month, date__year=d.year)
#
#    return render(
#        request,
#        "fir_stats/major.html",
#        {
#            "bale": bale,
#            "cert": cert,
#            "total_major": total_major,
#            "bls": bls,
#            "incident_list": Incident.authorization.for_user(
#                request.user, "incidents.view_incidents"
#            )
#            .filter(q_major & past_months)
#            .order_by("-date"),
#        },
#    )
