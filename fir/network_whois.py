from pprint import pformat
from ipwhois import IPWhois


"""https://ipwhois.readthedocs.io/en/latest/RDAP.html
"""

class NetworkWhois:


    @staticmethod
    def analyze(ip):
        links = set()

        obj = IPWhois(ip)
        results = obj.lookup_rdap(depth=1)
        #IPWhois.lookup_whois()
        print "=============== NETWHOIS ================="
        import ipdb; ipdb.set_trace()
        n = 0
        smallest_subnet = None

        for network in results['network']:
            import ipdb; ipdb.set_trace()
            cidr_bits = int(results['network']['cidr'].split('/')[1].split(',')[0])
            if cidr_bits > n:
                n = cidr_bits
                smallest_subnet = network

        import ipdb; ipdb.set_trace()
        if smallest_subnet:
            # Create the company
            #print smallest_subnet
            #print smallest_subnet['description']
            """company = Company.get_or_create(name=smallest_subnet['description'].split("\n")[0])"""
            """links.update(ip.active_link_to(company, 'hosting', 'Network Whois'))"""

            # Link it to every email address referenced
            print smallest_subnet
            print "\n"
            if smallest_subnet['emails']:pass
            """    for email_address in smallest_subnet['emails'].split("\n"):
                    print email_address"""
            """email = Email.get_or_create(value=email_address)"""
            """links.update(company.link_to(email, None, 'Network Whois'))"""

            # Copy the subnet info into the main dict
            for key in smallest_subnet:
                if smallest_subnet[key]:
                    results["net_{}".format(key)] = smallest_subnet[key]

        """
        # Add the network whois to the context if not already present
        for context in ip.context:
            if context['source'] == 'network_whois':
                break
        else:
            # Remove the nets info (the main one was copied)
            results.pop("nets", None)
            results.pop("raw", None)
            results.pop("raw_referral", None)
            results.pop("referral", None)
            results.pop("query", None)

            results['source'] = 'network_whois'
            ip.add_context(results)
        """
        #import ipdb; ipdb.set_trace()
        return list(links)


if __name__ == "__main__":
    ip_pool = [
            "74.125.225.229"
            "54.239.25.192",
            "54.239.26.128",
            "206.190.36.45",
            "98.138.253.109",
            "69.147.76.173",
            "54.195.239.248",
            "91.212.202.12"
            ]
    for ip in ip_pool:
        NetworkWhois.analyze(ip)
