# Import du module dnspython pour effectuer des résolutions DNS
import dns.resolver

# Default DNS query timeouts (seconds)
DEFAULT_RESOLVER_TIMEOUT = 2
DEFAULT_RESOLVER_LIFETIME = 4


# petit script: resolve A/AAAA
def resolve_records(
    domain: str,
    record_types=(
        "A",
        "AAAA",
        "NS",
        "MX",
        "CNAME",
        "SOA",
    ),
) -> dict:
    """Resolve common DNS record types for `domain`.

    By default resolves A, AAAA, MX, CNAME and SOA. TXT is handled by the
    TXT parser.
    Results are returned as a mapping `rtype -> list` of textual values
    (as returned by dnspython).
    """
    res = {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = DEFAULT_RESOLVER_TIMEOUT
    resolver.lifetime = DEFAULT_RESOLVER_LIFETIME

    for rtype in record_types:
        vals = []
        try:
            # perform query with controlled lifetime to avoid long blocks
            ans = resolver.resolve(domain, rtype, lifetime=DEFAULT_RESOLVER_LIFETIME)
            for r in ans:
                vals.append(r.to_text())
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            OSError,
        ):
            vals = []
        res[rtype] = vals
    return res  # ret dict


if __name__ == "__main__":
    # run d'exemp
    print(resolve_records("example.com"))
