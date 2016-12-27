from __future__ import absolute_import, unicode_literals

import pythonwhois
#from pythonwhois.net import get_whois_raw
#from pythonwhois.parse import parse_raw_whois
from tldextract import extract

#from fir_celery.celeryconf import celery_app

#from fir_artifacts.models import Artifact
#from fir_abuse.models import ArtifactEnrichment

from pprint import pprint
import re


class Whois:

    @staticmethod #@celery_app.task
    def analyze(artifact):
        """Perform a Whois
        domain name lookup and extract relevant information
        """
        #artifact = Artifact.objects.get(pk=artifact_id)
        abuse_email = []
        name = ''
        parts = extract(artifact['value'])
        import ipdb; ipdb.set_trace()
        if parts.subdomain == '':
            if artifact['type'] == 'email':
                artifact['value'] = ''.join([parts[1], '.', parts[2]])
            pprint(artifact['value'])
            import ipdb; ipdb.set_trace()
            data = pythonwhois.get_whois(artifact['value'])
            import ipdb; ipdb.set_trace()

            #parsed = parse_raw_whois(data, normalized=True)
            #pprint(parsed)
            
            """
            if artifact['type'] == 'hostname':
                if 'registrar' in parsed:
                    name = parsed['registrar']
                    print "========== registrar ======="
                    pprint(name)
            elif artifact['type'] == 'email':
                if 'registrant' in parsed['contacts']:
                    if 'organization' in parsed['contacts']['registrant']:
                        name = parsed['contacts']['registrant']['organization']
                        print "========== registrant org ======="
                        pprint(name)

            #pprint(parsed['contacts'])
            for key in parsed['contacts']:
                if parsed['contacts'][key] and 'email' in parsed['contacts'][key]:
                    match = re.search(r'abuse', parsed['contacts'][key]['email'])
                    if match and match.group() == "abuse":
                        abuse_email.append(parsed['contacts'][key]['email'])
            pprint(abuse_email)

            if len(abuse_email) == 0:
                for email in parsed['emails']:
                    match = re.search(r'abuse', email)
                    if match.group() == "abuse":
                        abuse_email.append(email)
            pprint(abuse_email)
            """
            #$import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    Whois.analyze({'type': 'hostname', 'value': 'cryto.net'})
    Whois.analyze({'type': 'hostname', 'value': 'amazon.com'})
    Whois.analyze({'type': 'hostname', 'value': 'ovh.com'})
    Whois.analyze({'type': 'email', 'value': 'tupaccu@hotmail.com'})
    Whois.analyze({'type': 'email', 'value': 'yemo.dasilva@gmail.com'})
    #Whois.analyze({'type': 'email', 'value': 'eric.dasilva@epitech.eu'})
