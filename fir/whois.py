from __future__ import absolute_import, unicode_literals

from pythonwhois.net import get_whois_raw
from pythonwhois.parse import parse_raw_whois
from tldextract import extract

from celery import shared_task
import sys


class Whois:


    @staticmethod
    @shared_task
    def analyze(hostname):
        """Perform a Whois
        domain name lookup and extract relevant information
        """

        parts = extract(hostname)

        if parts.subdomain == '':
            data = get_whois_raw(hostname)

            parsed = parse_raw_whois(data, normalized=True)

            #import ipdb; ipdb.set_trace()
            if 'creation_date' in parsed:
                pass

            if 'registrant' in parsed['contacts']:
                pass

            if 'emails' in parsed:
                print parsed['emails']
        #import ipdb; ipdb.set_trace()
"""
if __name__ == "__main__":
    Whois.analyze(sys.argv[1])"""
