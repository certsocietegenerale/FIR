from __future__ import absolute_import, unicode_literals

from pythonwhois.net import get_whois_raw
from pythonwhois.parse import parse_raw_whois
from tldextract import extract

from fir_celery.celeryconf import celery_app
#import sys
import re


class Whois:

    @staticmethod
    @celery_app.task
    def analyze(artifact):
        """Perform a Whois
        domain name lookup and extract relevant information
        """
        abuse_email = []
        parts = extract(artifact['value'])

        if parts.subdomain == '':
            if artifact['type'] == 'email':
                artifact['value'] = ''.join([parts[1], '.', parts[2]])

            data = get_whois_raw(artifact['value'])

            parsed = parse_raw_whois(data, normalized=True)

            if artifact['type'] == 'hostname':
                if 'registrar' in parsed:
                    registrar = parsed['registrar']

            if artifact['type'] == 'email':
                if 'registrant' in parsed['contacts']:
                    if 'organization' in parsed['contacts']['registrant']:
                        organization = parsed['contacts']['registrant']['organization']

            for key in parsed['contacts']:
                if parsed['contacts'][key] and 'email' in parsed['contacts'][key]:
                    match = re.search(r'abuse', parsed['contacts'][key]['email'])
                    if match and match.group() == "abuse":
                        abuse_email.append(parsed['contacts'][key]['email'])

            if len(abuse_email) == 0:
                for email in parsed['emails']:
                    match = re.search(r'abuse', email)
                    if match.group() == "abuse":
                        abuse_email.append(email)


            """import ipdb; ipdb.set_trace()"""

"""
if __name__ == "__main__":
    Whois.analyze({'type': 'email', 'value': 'eric.dasilva@epitech.eu'})
    Whois.analyze({'type': 'hostname', 'value': 'amazon.com'})
    Whois.analyze({'type': 'hostname', 'value': 'ovh.com'})
    Whois.analyze({'type': 'email', 'value': 'tupaccu@hotmail.com'})
    Whois.analyze({'type': 'email', 'value': 'yemo.dasilva@gmail.com'})
"""
