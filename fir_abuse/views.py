from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Template
from json import dumps

from incidents.authorization.decorator import authorization_required
from incidents.views import is_incident_handler
from incidents.models import Incident
from fir_artifacts.models import Artifact
from fir_email.helpers import send
from fir_abuse.models import AbuseTemplate, AbuseContact, EmailForm
from fir_artifacts_enrichment.models import ArtifactEnrichment
from fir_artifacts_enrichment.tasks import enrich_artifact


@login_required
def emailform(request):
    email_form = EmailForm(auto_id='abuse_%s')

    return render(request, 'fir_abuse/emailform.html', {'form': email_form})


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
                bcc=request.POST['bcc']
            )

            return HttpResponse(dumps({'status': 'ok'}), content_type="application/json")

        except Exception, e:
            return HttpResponse(dumps({'status': 'ko', 'error': str(e)}), content_type="application/json")

    return HttpResponseBadRequest(dumps({'status': 'ko'}), content_type="application/json")


@login_required
@user_passes_test(is_incident_handler)
def task_state(request, task_id):
    if request.method == 'GET' and task_id:
        task = enrich_artifact.AsyncResult(task_id)
        return HttpResponse(dumps({'state': task.state}), content_type="application/json")
    return HttpResponseBadRequest(dumps({'state': 'UNKNOWN'}), content_type="application/json")


@login_required
@authorization_required('incidents.handle_incidents', Incident, view_arg='incident_id')
def get_template(request, incident_id, artifact_id, authorization_target=None):
    if authorization_target is None:
        i = get_object_or_404(Incident.authorization.for_user(request.user, 'incidents.handle_incidents'),
                pk=incident_id)
    else:
        i = authorization_target

    artifact = Artifact.objects.get(pk=artifact_id)

    try:
        enrichment = ArtifactEnrichment.objects.get(artifact=artifact)
        default_email = enrichment.email
        abuse_template = get_best_record(artifact.type, i.category, AbuseTemplate)

        for name in enrichment.name.split('\n'):
            abuse_contact = get_best_record(artifact.type, i.category, AbuseContact, {'name': name})

            if abuse_contact:
                break

    except ArtifactEnrichment.DoesNotExist:
        default_email = ""
        enrichment = None
        abuse_contact = None
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
        'artifact': artifact.value.replace('http://', "hxxp://").replace('https://', 'hxxps://'),
        'enrichment': enrichment.raw if enrichment else ''
    })

    response = {
        'to': abuse_contact.to if abuse_contact else default_email,
        'cc': abuse_contact.cc if abuse_contact else '',
        'bcc': abuse_contact.bcc if abuse_contact else '',
        'subject': Template(abuse_template.subject).render(c) if abuse_template else "",
        'body': Template(abuse_template.body).render(c) if abuse_template else "",
        'trust': 1 if abuse_contact else 0,
        'artifact': artifact.value.replace('http://', "hxxp://").replace('https://', 'hxxps://'),
    }

    if enrichment:
        response['enrichment_names'] = enrichment.name.split('\n')
        response['enrichment_emails'] = enrichment.email
        response['enrichment_raw'] = enrichment.raw

    return HttpResponse(dumps(response), content_type="application/json")


def get_best_record(artifact_type, category, model, filters={}):
    if filters:
        collection = model.objects.filter(**filters)
    else:
        collection = model.objects

    q_type = Q(type=artifact_type) | Q(type='')
    q_incident_category = Q(incident_category=category) | Q(incident_category=None)

    result = None
    score = 0

    for record in collection.filter(q_type & q_incident_category):
        if record.type and record.incident_category:
            return record
        elif record.type == '' and record.incident_category:
            if score < 3:
                result = record
                score = 3
        elif record.type and record.incident_category is None:
            if score < 2:
                result = record
                score = 2
        else:
            if score == 0:
                result = record

    return result
