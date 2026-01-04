from smtplib import SMTPException
from django.http import Http404
from django.template import Template, Context
from rest_framework import serializers, viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from fir_api.permissions import CanViewIncident, CanWriteIncident
from fir_artifacts.models import Artifact
from fir_artifacts_enrichment.models import ArtifactEnrichment
from incidents.models import Incident
from fir_abuse.models import AbuseContact, AbuseTemplate
from fir_abuse.helpers import get_best_record, http_to_hxxp
from fir_email.helpers import send


class AbuseSerializer(serializers.Serializer):
    """
    Serializer for /api/abuse
    """

    to = serializers.CharField()
    cc = serializers.CharField()
    bcc = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField(style={"base_template": "textarea.html"})
    trust = serializers.IntegerField(read_only=True)
    artifact = serializers.CharField(read_only=True)


class AbuseViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    Get Abuse templates and send abuse emails.
    """

    permission_classes = [IsAuthenticated, CanViewIncident | CanWriteIncident]
    serializer_class = AbuseSerializer

    def list(self, request, *args, **kwargs):
        return Response(
            {
                "details": "Browse GET /api/abuse/<IncidentID>?artifact=<Artifact> To get an abuse template, and PUT /api/abuse/<IncidentID> to send an abuse email"
            }
        )

    def get_queryset(self):
        return Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )

    def retrieve(self, request, *args, **kwargs):
        inc = self.get_object()

        artifact = request.query_params.get("artifact", None)
        try:
            artifact = Artifact.objects.get(value=artifact)
        except Artifact.DoesNotExist:
            raise Http404()

        if inc not in artifact.relations.all():
            raise PermissionDenied()

        try:
            enrichment = ArtifactEnrichment.objects.get(artifact=artifact)
            default_email = enrichment.email
            abuse_template = get_best_record(artifact.type, inc.category, AbuseTemplate)

            for name in enrichment.name.split("\n"):
                abuse_contact = get_best_record(
                    artifact.type, inc.category, AbuseContact, {"name": name}
                )

                if abuse_contact:
                    break
        except ArtifactEnrichment.DoesNotExist:
            default_email = ""
            enrichment = None
            abuse_contact = None
            abuse_template = None

        artifacts = {}
        for a in inc.artifacts.all():
            if a.type not in artifacts:
                artifacts[a.type] = []
            artifacts[a.type].append(http_to_hxxp(a.value))

        c = Context(
            {
                "subject": http_to_hxxp(inc.subject),
                "artifacts": artifacts,
                "incident_id": inc.id,
                "bls": inc.get_business_lines_names(),
                "incident_category": inc.category.name,
                "artifact": http_to_hxxp(artifact.value),
                "enrichment": enrichment.raw if enrichment else "",
            }
        )

        response = {
            "to": abuse_contact.to if abuse_contact else default_email,
            "cc": abuse_contact.cc if abuse_contact else "",
            "bcc": abuse_contact.bcc if abuse_contact else "",
            "subject": (
                Template(abuse_template.subject).render(c) if abuse_template else ""
            ),
            "body": Template(abuse_template.body).render(c) if abuse_template else "",
            "trust": 1 if abuse_contact else 0,
            "artifact": http_to_hxxp(artifact.value),
        }

        if enrichment:
            response["enrichment_names"] = enrichment.name.split("\n")
            response["enrichment_emails"] = enrichment.email
            response["enrichment_raw"] = enrichment.raw

        return Response(response)

    def update(self, request, *args, **kwargs):
        try:
            send(
                request,
                to=request.POST["to"],
                subject=request.POST["subject"],
                body=request.POST["body"],
                cc=request.POST["cc"],
                bcc=request.POST["bcc"],
            )
            return Response({"status": "ok"})
        except (SMTPException, ValueError, OSError) as e:
            return Response(
                {"status": "ko", "detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY
            )
