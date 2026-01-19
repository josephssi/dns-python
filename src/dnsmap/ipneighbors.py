import ipaddress
import dns.reversename
import dns.resolver


def neighbors(ip: str, radius: int = 2) -> list:
    """Retourne les IP voisines et leurs PTRs.

    Se limite aux IPv4. `radius` définit combien d'adjacents de chaque côté.
    Renvoie liste de dicts {'ip': ip_str, 'ptrs': [...]}
    """
    out = []
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return out

    if addr.version != 4:
        return out

    ip_int = int(addr)
    min_ip = 0
    max_ip = 2**32 - 1

    for off in range(-radius, radius + 1):
        if off == 0:
            continue
        n = ip_int + off
        if n < min_ip or n > max_ip:
            continue
        nip = str(ipaddress.IPv4Address(n))
        ptrs = []
        try:
            rev = dns.reversename.from_address(nip)
            ans = dns.resolver.resolve(rev, "PTR")
            for r in ans:
                ptrs.append(r.to_text().rstrip("."))
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            ptrs = []

        out.append({"ip": nip, "ptrs": ptrs})

    return out


if __name__ == "__main__":
    print(neighbors("34.227.236.7", 2))
