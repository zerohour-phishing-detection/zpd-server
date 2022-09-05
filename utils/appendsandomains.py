import tldextract

# Function to append found (registered) domains from SAN list
# Replaces this:
# for domain1 in domain_list_with_san:
#         domain_list_tld_extract.append(str(tldextract.extract(str(domain1)).registered_domain))

def append_domains_san_to_tld_extract(src):
    dest = []
    if not any(isinstance(x, list) for x in src):
        # process list
        for domain in src:
            # print(domain)
            dest.append(str(tldextract.extract(str(domain)).registered_domain))
            # remove duplicates
            dest = list(dict.fromkeys(dest))
        return dest
    # contains sublists; print or process items one by one
    for x in src:
        if isinstance(x, list):
		    # process sub-list
            dest.extend(append_domains_san_to_tld_extract(x))
        else:
            # print(x)
            dest.append(str(tldextract.extract(str(x)).registered_domain))
    # remove duplicates
    dest = list(dict.fromkeys(dest))
    return dest


# Example source list of SAN domains:
# test_domain_list_with_san = ['www.generalandmedical.com', 'www.generalandmedical.com', 'www.linkedin.com', 'www.government.nl', 'www.cz.nl', 'www.msh-intl.com', 'www.myuhc.com', ['*.generalandmedical.com', 'generalandmedical.com'], ['*.generalandmedical.com', 'generalandmedical.com'], ['www.linkedin.com', 'linkedin.com', 'rum5.perf.linkedin.com', 'exp4.www.linkedin.com', 'exp3.www.linkedin.com', 'exp2.www.linkedin.com', 'exp1.www.linkedin.com', 'rum2.perf.linkedin.com', 'rum4.perf.linkedin.com', 'rum6.perf.linkedin.com', 'rum17.perf.linkedin.com', 'rum8.perf.linkedin.com', 'rum9.perf.linkedin.com', 'afd.perf.linkedin.com', 'rum14.perf.linkedin.com', 'rum18.perf.linkedin.com', 'rum19.perf.linkedin.com', 'exp5.www.linkedin.com', 'realtime.www.linkedin.com', 'px.ads.linkedin.com', 'px4.ads.linkedin.com', 'dc.ads.linkedin.com', 'lnkd.in', 'px.jobs.linkedin.com', 'mid4.linkedin.com'], ['rijksoverheid.nl', 'www.rijksoverheid.nl', 'opendata.rijksoverheid.nl', 'feeds.rijksoverheid.nl', 'static.rijksoverheid.nl', 'government.nl', 'www.government.nl', 'opendata.government.nl', 'feeds.government.nl'], ['www.cz.nl', 'cz.nl', 'mijnczzakelijk.cz.nl'], ['msh-intl.com', 'www.msh-intl.com'], ['www.myuhc.com', 'health4me.com', 'm.myuhc.com', 'myuhc.com', 'myuhcdental.com', 'www.health4me.com', 'www.myuhcdental.com', 'www.yourdentalplan.com', 'yourdentalplan.com']]

#test_domain_list_tld_extract = []
#test_domain_list_tld_extract = append_domains_san_to_tld_extract(test_domain_list_with_san)

#print(len(test_domain_list_tld_extract))
#print(test_domain_list_tld_extract)

## remove duplicates
#test_domain_list_tld_extract = list(dict.fromkeys(test_domain_list_tld_extract))
#print(test_domain_list_tld_extract) 
