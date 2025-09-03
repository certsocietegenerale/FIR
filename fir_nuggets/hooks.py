import re
from django.db.models import Q, Subquery

from fir_nuggets.api import NuggetSerializer
from fir_nuggets.models import Nugget

hooks = {
    "keyword_filter": {
        "nugget": lambda x: Q(
            id__in=Subquery(
                Nugget.objects.filter(source__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
        | Q(
            id__in=Subquery(
                Nugget.objects.filter(raw_data__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
        | Q(
            id__in=Subquery(
                Nugget.objects.filter(interpretation__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
    },
    "search_filter": [
        lambda x: Q(
            id__in=Subquery(
                Nugget.objects.filter(source__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
        | Q(
            id__in=Subquery(
                Nugget.objects.filter(raw_data__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
        | Q(
            id__in=Subquery(
                Nugget.objects.filter(interpretation__icontains=x)
                .values("incident_id")
                .distinct()
            )
        )
    ],
    "incident_fields": [
        (
            "nugget_set",  #  name of the new field
            None,
            NuggetSerializer(
                many=True, read_only=True
            ),  # Serializer corresponding to the new field
            None,
        ),
    ],
}
