import re
from django.db.models import Q


def get_best_record(artifact_type, category, model, filters={}):
    if filters:
        collection = model.objects.filter(**filters)
    else:
        collection = model.objects

    q_type = Q(type=artifact_type) | Q(type="")
    q_incident_category = Q(incident_category=category) | Q(incident_category=None)

    result = None
    score = 0

    for record in collection.filter(q_type & q_incident_category):
        if record.type and record.incident_category:
            return record
        elif record.type == "" and record.incident_category:
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


def http_to_hxxp(text):
    pattern = re.compile(r"\bhttps?://", re.IGNORECASE)

    return pattern.sub(
        lambda m: "".join(
            "X" if c.lower() == "t" and c.isupper() else "x" if c.lower() == "t" else c
            for c in m.group(0)
        ),
        text,
    )
