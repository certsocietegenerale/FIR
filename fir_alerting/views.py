from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Template
from django.conf import settings
from json import dumps

from incidents.views import is_incident_handler
from incidents.models import Incident, BusinessLine

from fir_alerting.models import RecipientTemplate, CategoryTemplate, EmailForm


@login_required
@user_passes_test(is_incident_handler)
def emailform(request):
    email_form = EmailForm()

    return render(request, 'fir_alerting/emailform.html', {'form': email_form})


@login_required
@user_passes_test(is_incident_handler)
def get_template(request, incident_id, template_type, bl=None):
    i = get_object_or_404(Incident, pk=incident_id)

    try:
        cat_template = CategoryTemplate.objects.get(incident_category=i.category, type=template_type)
    except Exception, e:
        cat_template = None

    rec_template = None
    if not bl:
        q_bl = Q()
        bls = i.concerned_business_lines.all()
        for b in bls:
            q_bl |= Q(business_line=b)
        bl_name = i.get_business_lines_names()
    else:
        bl = get_object_or_404(BusinessLine, pk=bl)
        q_bl = Q(business_line=bl)
        bl_name = bl.name

    try:
        rec_template = RecipientTemplate.objects.get((q_bl | Q(business_line=None)) & Q(type=template_type))
    except Exception, e:
        print "Email template ERROR: ", e
        parents = list(set(i.concerned_business_lines.all()))

        while not rec_template and parents != [None]:
            try:
                parents = list(set([b.parent for b in parents]))
                q_parent = Q()
                for p in parents:
                    q_parent |= Q(business_line=p)
                template = list(RecipientTemplate.objects.filter((q_parent | Q(business_line=None)) & Q(type=template_type)))
                if len(template) > 0:
                    rec_template = template[0]
            except Exception as e:
                print "Email template ERROR 2: ", e
                break

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
            from django.core.mail import EmailMultiAlternatives
            behalf = request.POST['behalf']
            to = request.POST['to']
            cc = request.POST['cc']
            bcc = request.POST['bcc']

            subject = request.POST['subject']
            body = request.POST['body']

            if hasattr(settings, 'REPLY_TO'):
                reply_to = {'Reply-To': settings.REPLY_TO, 'Return-Path': settings.REPLY_TO}
            else:
                reply_to = {}

            e = EmailMultiAlternatives(
                subject=subject,
                from_email=behalf,
                to=to.split(';'),
                cc=cc.split(';'),
                bcc=bcc.split(';'),
                headers=reply_to
            )
            e.attach_alternative(body, 'text/html')
            e.content_subtype = 'html'
            e.send()

            return HttpResponse(dumps({'status': 'ok'}), content_type="application/json")

        except Exception, e:
            return HttpResponse(dumps({'status': 'ko', 'error': str(e)}), content_type="application/json")

    return HttpResponseBadRequest(dumps({'status': 'ko'}), content_type="application/json")
