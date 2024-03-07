import socket
import ssl
from urllib.parse import urlparse

import tldextract


def get_hostname(url):
    return urlparse(url).netloc


def get_san_names(domain):
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=2) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            sans = {}
            for type_, san in cert['subjectAltName']:
                if type_ not in sans:
                    sans[type_] = []
                sans[type_].append(san)
            
            return sans['DNS']

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