from __future__ import absolute_import, unicode_literals

from pythonwhois.net import get_whois_raw
from pythonwhois.parse import parse_raw_whois
from tldextract import extract

from fir_celery.celeryconf import celery_app

from fir_artifacts.models import Artifact
from fir_abuse.models import ArtifactEnrichment

import re


class Whois:

    @staticmethod
    @celery_app.task
    def analyze(artifact_id):
        """Perform a Whois
        domain name lookup and extract relevant information
        """
        artifact = Artifact.objects.get(pk=artifact_id)
        abuse_email = []
        name = ''
        parts = extract(artifact.value)
        if parts.subdomain == '':
            if artifact.type == 'email':
                artifact.value = ''.join([parts[1], '.', parts[2]])
            try:
                data = get_whois_raw(artifact.value)
                parsed = parse_raw_whois(data, ['Domain', 'contacts'])
            except Exception as e:
                print "Something went wrong"
            else:
                if artifact.type == 'hostname':
                    if 'registrar' in parsed:
                        name = parsed['registrar']
                elif artifact.type == 'email':
                    if 'registrant' in parsed['contacts']:
                        if 'organization' in parsed['contacts']['registrant']:
                            registrant_org = parsed['contacts']['registrant']['organization']
                        if 'email' in parsed['contacts']['registrant']:
                            abuse_email.append(parsed['contacts']['registrant']['email'])

                if len(abuse_email) == 0:
                    for key in parsed['contacts']:
                        if parsed['contacts'][key] and 'email' in parsed['contacts'][key]:
                            match = re.search(r'abuse', parsed['contacts'][key]['email'])
                            if match and match.group() == "abuse":
                                abuse_email.append(parsed['contacts'][key]['email'])

                if len(abuse_email) == 0 and 'emails' in parsed:
                    for email in parsed['emails']:
                        match = re.search(r'abuse', email)
                        if match.group() == "abuse":
                            abuse_email.append(email)
                if len(abuse_email) >= 1:
                    enrichment = ArtifactEnrichment.objects.create(
                            artifact=artifact,
                            name=name,
                            email=abuse_email[0],
                            raw=parsed['raw']
                            )
                else:
                    enrichment = ArtifactEnrichment.objects.create(
                            artifact=artifact,
                            email=abuse_email[0],
                            raw=parsed['raw']
                            )
                enrichment.save()
