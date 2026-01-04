from smtplib import SMTPException
from django.template import Template, Context
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework import serializers, viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from fir_api.permissions import CanViewIncident, CanWriteIncident
from incidents.models import Incident, BusinessLine
from fir_alerting.helpers import get_rec_template, http_to_hxxp
from fir_alerting.models import CategoryTemplate
from fir_email.helpers import send


class AlertingSerializer(serializers.Serializer):
    """
    Serializer for /api/alerting
    """

    behalf = serializers.CharField()
    to = serializers.CharField()
    cc = serializers.CharField()
    bcc = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField(style={"base_template": "textarea.html"})
    bl = serializers.CharField(read_only=True)


class AlertingViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    Get alerting templates and send emails.
    """

    permission_classes = [IsAuthenticated, CanViewIncident | CanWriteIncident]
    serializer_class = AlertingSerializer

    def list(self, request, *args, **kwargs):
        return Response(
            {
                "details": "Browse GET /api/alerting/<IncidentID>?type=<type>&bl=<bl> To get an alerting template, and PUT /api/alerting/<IncidentID> to send an email"
            }
        )

    def get_queryset(self):
        return Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )

    def retrieve(self, request, *args, **kwargs):
        inc = self.get_object()

        template_type = request.query_params.get("type", "").lower()
        try:
            cat_template = CategoryTemplate.objects.get(
                incident_category=inc.category, type=template_type
            )
        except CategoryTemplate.DoesNotExist:
            cat_template = None

        bl = request.query_params.get("bl", "").lower()

        if bl:
            bl = get_object_or_404(BusinessLine, name=bl)
            if bl not in inc.concerned_business_lines.all():
                raise PermissionDenied()

            q_bl = Q(business_line=bl)
            bl_name = bl.name
            parents = [bl]
        else:
            q_bl = Q(business_line__in=inc.concerned_business_lines.all())
            bl_name = inc.get_business_lines_names()
            parents = list(set(inc.concerned_business_lines.all()))

        # Find the most appropriate template
        rec_template = get_rec_template(q_bl & Q(type=template_type))
        while not rec_template and len(parents):
            parents = list(set([b.get_parent() for b in parents if not b.is_root()]))
            q_parents = Q(business_line__in=parents)

            rec_template = get_rec_template(q_parents & Q(type=template_type))

        if rec_template is None:
            rec_template = get_rec_template(
                Q(business_line=None) & Q(type=template_type)
            )

        artifacts = {}
        main_artifact = None
        for a in inc.artifacts.all():
            if inc.subject.lower() == a.value:
                main_artifact = a
            if a.type not in artifacts:
                artifacts[a.type] = []
            artifacts[a.type].append(http_to_hxxp(a.value))

        enrich = None
        if main_artifact and main_artifact.artifactenrichment_set.all().count() > 0:
            enrich = main_artifact.artifactenrichment_set.all()[0].raw

        c = Context(
            {
                "subject": http_to_hxxp(inc.subject),
                "bl": bl_name,
                "artifacts": artifacts,
                "incident_id": inc.id,
                "incident_category": inc.category.name,
                "severity": inc.severity.name if inc.severity else "",
                "phishing_url": http_to_hxxp(
                    inc.subject
                ),  # Legacy. Keeping this for backward compatibility
                "enrich": enrich,  # Legacy. Keeping this for backward compatibility
            }
        )

        response = {
            "behalf": rec_template.behalf if rec_template else "",
            "to": rec_template.recipient_to if rec_template else "",
            "cc": rec_template.recipient_cc if rec_template else "",
            "bcc": rec_template.recipient_bcc if rec_template else "",
            "subject": Template(cat_template.subject).render(c) if cat_template else "",
            "body": Template(cat_template.body).render(c) if cat_template else "",
            "bl": bl_name,
        }

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
