from __future__ import absolute_import, unicode_literals

from ipwhois import IPWhois
from operator import itemgetter
import re

from fir_artifacts.models import Artifact
from fir_abuse.models import ArtifactEnrichment
from fir_celery.celeryconf import celery_app

"""https://ipwhois.readthedocs.io/en/latest/RDAP.html
"""


class NetworkWhois:

    @staticmethod
    @celery_app.task
    def analyze(artifact_id):
        artifact = Artifact.objects.get(pk=artifact_id)
        abuse_email = {}

        obj = IPWhois(artifact.value)
        results = obj.lookup_rdap(depth=1, inc_raw=True)

        s = {'abuse': 4, 'registrant': 3, 'registrar': 2, 'inmail': 1, 'none': 0}

        for k in results['objects']:
            r = -1
            if results['objects'][k]['roles']:
                for role in results['objects'][k]['roles']:
                    if re.search('abuse', role):
                        r = s['abuse']
                        break
            if r < 0:
                r = s['none']

            if results['objects'][k]['contact']['email']:
                email = results['objects'][k]['contact']['email'][0]['value']
                if r == 0 and re.search('abuse', email):
                    r = s['inmail']
                abuse_email[email] = r

        abuse_email= sorted(abuse_email.items(), key=itemgetter(1) , reverse=True)

        if 'name' in results['network'] and 'raw' in results and len(abuse_email) >= 1:
            if results['network']['name']:
                name = results['network']['name']
            else:
                name = "NOT PROVIDED"
            enrichment = ArtifactEnrichment.objects.create(
                    artifact=artifact,
                    name=name,
                    email=abuse_email[0][0],
                    raw=results['raw']
                    )
            enrichment.save()
