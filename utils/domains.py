from urllib.parse import urlparse
import ssl
import socket
import tldextract

def get_hostname(url):
    return urlparse(url).netloc

def get_san_names(domain):
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=2) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            san = {}
            for type_, san in cert['subjectAltName']:
                if type_ in san:
                    san[type_] = []
                san[type_].append(san)
            
            return san['DNS']

def get_registered_domain(hostname):
    """
    Gets the registered domain name of a given hostname, e.g. 'forums.bbc.co.uk' becomes 'bbc.co.uk'.
    """
    return tldextract.extract(hostname).registered_domain

def get_unique_registered_domains(hostnames):
    """
    Extract registered domain names from a list of hostnames.
    """
    return list(set([get_registered_domain(hostname) for hostname in hostnames]))


# Example source list of SAN domains:
# test_domain_list_with_san = ['www.generalandmedical.com', 'www.generalandmedical.com', 'www.linkedin.com', 'www.government.nl', 'www.cz.nl', 'www.msh-intl.com', 'www.myuhc.com', ['*.generalandmedical.com', 'generalandmedical.com'], ['*.generalandmedical.com', 'generalandmedical.com'], ['www.linkedin.com', 'linkedin.com', 'rum5.perf.linkedin.com', 'exp4.www.linkedin.com', 'exp3.www.linkedin.com', 'exp2.www.linkedin.com', 'exp1.www.linkedin.com', 'rum2.perf.linkedin.com', 'rum4.perf.linkedin.com', 'rum6.perf.linkedin.com', 'rum17.perf.linkedin.com', 'rum8.perf.linkedin.com', 'rum9.perf.linkedin.com', 'afd.perf.linkedin.com', 'rum14.perf.linkedin.com', 'rum18.perf.linkedin.com', 'rum19.perf.linkedin.com', 'exp5.www.linkedin.com', 'realtime.www.linkedin.com', 'px.ads.linkedin.com', 'px4.ads.linkedin.com', 'dc.ads.linkedin.com', 'lnkd.in', 'px.jobs.linkedin.com', 'mid4.linkedin.com'], ['rijksoverheid.nl', 'www.rijksoverheid.nl', 'opendata.rijksoverheid.nl', 'feeds.rijksoverheid.nl', 'static.rijksoverheid.nl', 'government.nl', 'www.government.nl', 'opendata.government.nl', 'feeds.government.nl'], ['www.cz.nl', 'cz.nl', 'mijnczzakelijk.cz.nl'], ['msh-intl.com', 'www.msh-intl.com'], ['www.myuhc.com', 'health4me.com', 'm.myuhc.com', 'myuhc.com', 'myuhcdental.com', 'www.health4me.com', 'www.myuhcdental.com', 'www.yourdentalplan.com', 'yourdentalplan.com']]

#test_domain_list_tld_extract = []
#test_domain_list_tld_extract = append_domains_san_to_tld_extract(test_domain_list_with_san)

#print(len(test_domain_list_tld_extract))
#print(test_domain_list_tld_extract)

## remove duplicates
#test_domain_list_tld_extract = list(dict.fromkeys(test_domain_list_tld_extract))
#print(test_domain_list_tld_extract) 
