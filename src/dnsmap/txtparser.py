import re
import dns.resolver

_IP_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
# split regex string literals to avoid overly long lines
_DOMAIN_RE = re.compile(
    r"\b"
    r"[a-zA-Z0-9.-]+\."
    r"[a-zA-Z]{2,}\b"
)


def parse_txt_from_strings(txt_records: list[str]) -> dict:
    """Parse a list of TXT record strings and extract domains and IPv4 addresses.

    This helper is separated from DNS resolution so it can be unit-tested
    without network.
    """
    out = {"raw": [], "domains": [], "ips": []}
    for txt in txt_records:
        out["raw"].append(txt)
        for ip in _IP_RE.findall(txt):
            if ip not in out["ips"]:
                out["ips"].append(ip)
        for d in _DOMAIN_RE.findall(txt):
            if d not in out["domains"]:
                out["domains"].append(d)
    return out


def parse_txt(domain: str) -> dict:
    """Récupère les enregistrements TXT via DNS et réutilise `parse_txt_from_strings`.

    Keeps previous behavior (network call) but delegating parsing to a testable helper.
    """
    out = {"raw": [], "domains": [], "ips": []}
    try:
        ans = dns.resolver.resolve(domain, "TXT")
        strs = []
        for r in ans:
            txt = r.to_text()
            strs.append(txt)
        out = parse_txt_from_strings(strs)
    except (
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        pass
    return out


if __name__ == "__main__":
    print(parse_txt("example.com"))
