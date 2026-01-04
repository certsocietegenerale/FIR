import re
from fir_alerting.models import RecipientTemplate


def get_rec_template(query):
    template = list(RecipientTemplate.objects.filter(query))

    if len(template) > 0:
        return template[0]
    else:
        return None


def http_to_hxxp(text):
    pattern = re.compile(r"\bhttps?://", re.IGNORECASE)

    return pattern.sub(
        lambda m: "".join(
            "X" if c.lower() == "t" and c.isupper() else "x" if c.lower() == "t" else c
            for c in m.group(0)
        ),
        text,
    )
