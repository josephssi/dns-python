import dns.resolver


# liste services courants à tester
DEFAULT_SRVS = [
    '_sip._tcp', '_sip._udp', '_sip._tls',
    '_xmpp-server._tcp', '_xmpp-client._tcp',
    '_ldap._tcp', '_kerberos._udp',
    '_http._tcp', '_smtp._tcp', '_imap._tcp', '_pop3._tcp'
]


def scan_srv(domain: str, services: list | None = None) -> dict:
    """Teste des enregistrements SRV pour `domain`.

    Renvoie un dict {service: [ {priority, weight, port, target}, ... ] }
    """
    if services is None:
        services = DEFAULT_SRVS

    out = {}
    for svc in services:
        qname = f"{svc}.{domain}"
        entries = []
        try:
            ans = dns.resolver.resolve(qname, 'SRV')
            for r in ans:
                entries.append({
                    'priority': int(r.priority),
                    'weight': int(r.weight),
                    'port': int(r.port),
                    'target': r.target.to_text().rstrip('.')
                })
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            # pas d'enr pour ce service
            entries = []
        out[svc] = entries

    return out


if __name__ == '__main__':
    print(scan_srv('se.com'))
