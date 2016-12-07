import re

from django.db.models import Q

def keyword_filter(q, query_string):
    nugget = re.search("nugget:(\S+)", query_string)
    if nugget:
        nugget = nugget.group(1)
        q = q & Q(nugget__source__icontains=nugget) | Q(nugget__raw_data__icontains=nugget) | Q(nugget__interpretation__icontains=nugget)
        query_string = query_string.replace('nugget:' + nugget, '')
    return q, query_string


def search_filter(q, query_string):
    q = q | (Q(nugget__source__icontains=query_string) | Q(nugget__raw_data__icontains=query_string) | Q(nugget__interpretation__icontains=query_string))
    return q, query_string


hooks = {
    "keyword_filter": keyword_filter,
    "search_filter": search_filter
}
