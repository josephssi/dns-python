import dns.reversename
import dns.resolver


def reverse_lookup(ip: str) -> list:
    """Retourne les noms PTR pour une IP (liste vide si aucun)."""
    try:
        rev = dns.reversename.from_address(ip)
        ans = dns.resolver.resolve(rev, "PTR")
        return [r.to_text().rstrip(".") for r in ans]
    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        return []


if __name__ == "__main__":
    print(reverse_lookup("34.227.236.7"))
