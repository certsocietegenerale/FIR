from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Template
from django.conf import settings
from json import dumps
from datetime import datetime, timedelta

from celery.result import AsyncResult

from incidents.views import is_incident_handler
from incidents.models import Incident, BusinessLine
from fir_artifacts.models import Artifact

from fir_abuse.models import AbuseTemplate, ArtifactEnrichment, AbuseContact

from fir_celery.whois import Whois
from fir_celery.network_whois import NetworkWhois

from pprint import pprint


@login_required
@user_passes_test(is_incident_handler)
def emailform(request):
    email_form = EmailForm()

    return render(request, 'fir_abuse/emailform.html', {'form': email_form})


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


@login_required
@user_passes_test(is_incident_handler)
@receiver(post_save, sender=Artifact)
def analyze_artifacts(sender, instance=None, created=False, **kwargs):

    tasks = {
            'hostname': Whois.analyze.apply_async,
            'email': Whois.analyze.apply_async,
            'ip': NetworkWhois.analyze.apply_async
            }

    if created and instance.type in tasks:
        result = tasks[instance.type](args=[instance.id],
                task_id=str(instance.id)) #, eta=datetime.now() + timedelta(seconds=10))


@login_required
@user_passes_test(is_incident_handler)
def task_state(request, task_id):
    if request.method == 'GET' and task_id:
        task = AsyncResult(task_id)
        return HttpResponse(dumps({'state': task.state}), content_type="application/json")
    return HttpResponseBadRequest(dumps({'state': 'UNKNOWN'}), content_type="application/json")


@login_required
@user_passes_test(is_incident_handler)
def get_template(request, incident_id, artifact_id):
    i = get_object_or_404(Incident, pk=incident_id)

    try:
        artifact = Artifact.objects.get(pk=artifact_id)
        enrichment = ArtifactEnrichment.objects.get(artifact=artifact)

        abuse_contact = AbuseContact.objects.get(name=enrichment.name, incident_category=i.category, type=artifact.type)
        abuse_template = AbuseTemplate.objects.get(incident_category=i.category, type=artifact.type)
    except Exception as e:
        abuse_template = None

    artifacts = {}
    for a in i.artifacts.all():
        if a.type not in artifacts:
            artifacts[a.type] = []
        artifacts[a.type].append(a.value.replace('http://', "hxxp://").replace('https://', 'hxxps://'))

    c = Context({
        'subject': i.subject.replace('http://', "hxxp://").replace('https://', 'hxxps://'),
        'artifacts': artifacts,
        'incident_id': i.id,
        'bls': i.get_business_lines_names(),
        'incident_category': i.category.name,
        'trust': 1 if abuse_contact else 0
    })

    response = {
        'to': abuse_contact.to if abuse_contact else enrichment.email,
        'cc': "",
        'bcc': "",
        'subject': Template(abuse_template.subject).render(c) if abuse_template else "",
        'body': Template(abuse_template.body).render(c) if abuse_template else "",
    }

    return HttpResponse(dumps(response), content_type="application/json")
