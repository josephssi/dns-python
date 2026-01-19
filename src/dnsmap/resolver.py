import dns.resolver


# petit script: resolve A/AAAA
def resolve_records(
    domain: str,
    record_types=(
        "A",
        "AAAA",
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
    for rtype in record_types:
        vals = []
        try:
            # req DNS pr le type
            ans = dns.resolver.resolve(domain, rtype)
            for r in ans:
                vals.append(r.to_text())  # ajoute la val
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            # si pb/no ans -> liste vide
            vals = []
        res[rtype] = vals  # save ds dict
    return res  # ret dict


if __name__ == "__main__":
    # run d'exemp
    print(resolve_records("example.com"))
