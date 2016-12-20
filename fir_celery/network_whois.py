from __future__ import absolute_import, unicode_literals

from ipwhois import IPWhois
from operator import itemgetter
import re

from fir_celery.celeryconf import celery_app
from pprint import pprint

"""https://ipwhois.readthedocs.io/en/latest/RDAP.html
"""

class NetworkWhois:

    @staticmethod
    @celery_app.task
    def analyze(artifact):
        abuse_email = {}

        obj = IPWhois(artifact['value'])
        results = obj.lookup_rdap(depth=1)

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

        print "=============== NETWHOIS EMAIL ABUSE PROPOSAL ================="
        abuse_email= sorted(abuse_email.items(), key=itemgetter(1) , reverse=True)
        """for key in abuse_email:
            abuses.append(key)
        pprint(abuses)"""
        pprint(abuse_email[0][0])

"""
if __name__ == "__main__":
    ip_pool = [
            "80.247.227.20", #RIPE
            "35.156.105.176", #APNIC
            "216.58.213.101",
            "183.79.200.194",  #APNIC
            "217.12.15.37",    #RIPE
            "187.111.97.27",   #LACNIC
            "196.12.225.227",  #AFRINIC
            "74.125.225.229"  #ARIN
            ]
    for ip in ip_pool:
        NetworkWhois.analyze(ip)
"""
