import dns.resolver
from pathlib import Path

# liste de sous-domaines courants
DEFAULT_WORDS = [
    "www",
    "mail",
    "api",
    "dev",
    "staging",
    "test",
    "vpn",
    "admin",
    "intranet",
    "shop",
    "blog",
    "m",
    "webmail",
    "smtp",
    "imap",
    "pop",
    "ftp",
    "ns1",
    "ns2",
]


def load_wordlist(path: str) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return [
        line.strip()
        for line in p.read_text(encoding="utf8").splitlines()
        if line.strip()
    ]


def enumerate_subdomains(domain: str, wordlist: list | None = None) -> list:
    """Brute-force des sous-domaines basiques via une liste de mots.

    Renvoie une liste d'objets {sub: str, A: [], AAAA: [], CNAME: []}.
    """
    if wordlist is None:
        words = DEFAULT_WORDS
    else:
        words = wordlist

    found = []
    for w in words:
        sub = f"{w}.{domain}"
        entry = {"sub": sub, "A": [], "AAAA": [], "CNAME": []}
        # A
        try:
            ans = dns.resolver.resolve(sub, "A")
            for r in ans:
                entry["A"].append(r.to_text())
        except Exception:
            pass
        # AAAA
        try:
            ans = dns.resolver.resolve(sub, "AAAA")
            for r in ans:
                entry["AAAA"].append(r.to_text())
        except Exception:
            pass
        # CNAME
        try:
            ans = dns.resolver.resolve(sub, "CNAME")
            for r in ans:
                entry["CNAME"].append(r.to_text().rstrip("."))
        except Exception:
            pass

        if entry["A"] or entry["AAAA"] or entry["CNAME"]:
            found.append(entry)

    return found


if __name__ == "__main__":
    print(enumerate_subdomains("example.com"))
