import re
from django.db.models import Q

from fir_nuggets.api import NuggetSerializer

hooks = {
    "keyword_filter": {
        "nugget": lambda x: Q(nugget__source__icontains=x)
        | Q(nugget__raw_data__icontains=x)
        | Q(nugget__interpretation__icontains=x)
    },
    "search_filter": [
        lambda x: Q(nugget__source__icontains=x)
        | Q(nugget__raw_data__icontains=x)
        | Q(nugget__interpretation__icontains=x)
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
