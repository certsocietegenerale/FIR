from __future__ import absolute_import, unicode_literals

from pythonwhois.net import get_whois_raw
from pythonwhois.parse import parse_raw_whois
from tldextract import extract

from celery import shared_task
import sys

"""
def link_from_contact_info(hostname, contact, field, klass, description):
    if contact is not None and field in contact:
        node = klass.get_or_create(value=contact[field])

        return hostname.active_link_to(node, description, 'Whois')
    else:
        return ()
"""

class Whois:


    @staticmethod
    @shared_task
    def analyze(hostname):
        """Perform a Whois
        domain name lookup and extract relevant information
        """
        links = set()

        parts = extract(hostname)

        if parts.subdomain == '':
            should_add_context = False
            """
            for context in hostname.context:
                if context['source'] == 'whois':
                    break
            else:
                should_add_context = True
                context = {'source': 'whois'}
            """
            data = get_whois_raw(hostname)

            """results.update(raw=data[0])"""
            parsed = parse_raw_whois(data, normalized=True)
            """context['raw'] = data[0]"""
            print parsed

            if 'creation_date' in parsed:
                print parsed['creation_date'][0]

                """context['creation_date'] = parsed['creation_date'][0]"""

            if 'registrant' in parsed['contacts']:
                print parsed['contacts']['registrant']

            """
                fields_to_extract = [
                    ('email', Email, 'Registrant Email'),
                    ('name', Text, 'Registrant Name'),
                    ('organization', Text, 'Registrant Organization'),
                    ('phone', Text, 'Registrant Phone Number'),
                ]
            """
            """
                for field, klass, description in fields_to_extract:
                    links.update(link_from_contact_info(hostname, parsed['contacts']['registrant'], field, klass, description))
                """
            """
            if should_add_context:
                hostname.add_context(context)
            else:
                hostname.save()
            """
        #import ipdb; ipdb.set_trace()
        return list(links)


if __name__ == "__main__":
    #tool = Whois()
    Whois.analyze(sys.argv[1])
