import re

from django.db.models import Q


def keyword_filter(q, query_string):
    nugget = re.search("nugget:(\S+)", query_string)
    if nugget:
        nugget = nugget.group(1)
        q = (
            q & Q(nugget__source__icontains=nugget)
            | Q(nugget__raw_data__icontains=nugget)
            | Q(nugget__interpretation__icontains=nugget)
        )
        query_string = query_string.replace("nugget:" + nugget, "")
    return q, query_string


def search_filter(q, query_string):
    q = q | (
        Q(nugget__source__icontains=query_string)
        | Q(nugget__raw_data__icontains=query_string)
        | Q(nugget__interpretation__icontains=query_string)
    )
    return q, query_string


try:
    from fir_nuggets.api import NuggetSerializer
except ModuleNotFoundError:
    incident_fields = {}
else:
    incident_fields = [
        (
            "nugget_set",  #  name of the new field
            None,
            NuggetSerializer(
                many=True, read_only=True
            ),  # Serializer corresponding to the new field
            None,
        ),
    ]

hooks = {
    "keyword_filter": keyword_filter,
    "search_filter": search_filter,
    "incident_fields": incident_fields,
}
