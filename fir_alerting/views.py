from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Template
from json import dumps

from incidents.authorization.decorator import authorization_required
from incidents.views import is_incident_handler
from incidents.models import Incident, BusinessLine

from fir_alerting.models import RecipientTemplate, CategoryTemplate, EmailForm
from fir_email.helpers import send


def get_rec_template(query):
    template = list(RecipientTemplate.objects.filter(query))

    if len(template) > 0:
        return template[0]
    else:
        return None


@login_required
def emailform(request):
    email_form = EmailForm()

    return render(request, 'fir_alerting/emailform.html', {'form': email_form})


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def get_template(request, incident_id, template_type, bl=None, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
                              pk=incident_id)
    else:
        i = authorization_target

    try:
        cat_template = CategoryTemplate.objects.get(incident_category=i.category, type=template_type)
    except Exception, e:
        cat_template = None

    rec_template = None

    if not bl:
        q_bl = Q(business_line__in=i.concerned_business_lines.all())
        bl_name = i.get_business_lines_names()
    else:
        bl = get_object_or_404(BusinessLine, pk=bl)
        q_bl = Q(business_line=bl)
        bl_name = bl.name

    rec_template = get_rec_template(q_bl & Q(type=template_type))

    parents = list(set(i.concerned_business_lines.all()))

    while not rec_template and len(parents):
        parents = list(set([b.get_parent() for b in parents if not b.is_root()]))
        q_parents = Q(business_line__in=parents)

        rec_template = get_rec_template(q_parents & Q(type=template_type))

    if rec_template is None:
        rec_template = get_rec_template(Q(business_line=None) & Q(type=template_type))

    artifacts = {}
    for a in i.artifacts.all():
        if a.type not in artifacts:
            artifacts[a.type] = []
        artifacts[a.type].append(a.value.replace('http://', "hxxp://").replace('https://', 'hxxps://'))

    c = Context({
        'subject': i.subject.replace('http://', "hxxp://").replace('https://', 'hxxps://'),
        'bl': bl_name,
        'phishing_url': i.subject.replace('http://', "hxxp://").replace('https://', 'hxxps://'),
        'artifacts': artifacts,
        'incident_id': i.id
    })

    response = {
        'behalf': rec_template.behalf if rec_template else "",
        'to': rec_template.recipient_to if rec_template else "",
        'cc': rec_template.recipient_cc if rec_template else "",
        'bcc': rec_template.recipient_bcc if rec_template else "",
        'subject': Template(cat_template.subject).render(c) if cat_template else "",
        'body': Template(cat_template.body).render(c) if cat_template else "",
        'bl': bl_name,
    }

    return HttpResponse(dumps(response), content_type="application/json")


@login_required
@user_passes_test(is_incident_handler)
def send_email(request):
    if request.method == 'POST':
        try:
            send(
                request,
                to=request.POST['to'],
                subject=request.POST['subject'],
                body=request.POST['body'],
                cc=request.POST['cc'],
                bcc=request.POST['bcc'],
                behalf=request.POST['behalf']
            )

            return HttpResponse(dumps({'status': 'ok'}), content_type="application/json")

        except Exception, e:
            return HttpResponse(dumps({'status': 'ko', 'error': str(e)}), content_type="application/json")

    return HttpResponseBadRequest(dumps({'status': 'ko'}), content_type="application/json")
