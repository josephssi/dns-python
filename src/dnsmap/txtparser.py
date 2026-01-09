import re
import dns.resolver


_IP_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
_DOMAIN_RE = re.compile(r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")


def parse_txt(domain: str) -> dict:
    """Get TXT records and extract domains and IPv4s."""
    out = {"raw": [], "domains": [], "ips": []}
    try:
        ans = dns.resolver.resolve(domain, 'TXT')
        for r in ans:
            txt = r.to_text()
            out["raw"].append(txt)
            # find ips
            for ip in _IP_RE.findall(txt):
                if ip not in out["ips"]:
                    out["ips"].append(ip)
            # find domains
            for d in _DOMAIN_RE.findall(txt):
                if d not in out["domains"]:
                    out["domains"].append(d)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        pass
    return out


if __name__ == '__main__':
    print(parse_txt('example.com'))
