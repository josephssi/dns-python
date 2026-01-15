import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))  # pr dev import

from dnsmap import resolve_records, parse_txt, crawl_to_tld, scan_srv, reverse_lookup, enumerate_subdomains  # fn pr resolve + txt + crawl + srv + rev + sub

# petit CLI pr test rapide


def main():
    p = argparse.ArgumentParser(description='Résolution DNS basique (A/AAAA)')
    p.add_argument('domain', help='domaine à analyser')
    p.add_argument('--txt', action='store_true', help='parser les enregistrements TXT')
    p.add_argument('--crawl', action='store_true', help='remonter aux domaines parents (TLD)')
    p.add_argument('--srv', action='store_true', help='scanner les enregistrements SRV')
    p.add_argument('--rev', action='store_true', help='reverse DNS (PTR) des IPs résolues')
    p.add_argument('--sub', action='store_true', help='brute-force sous-domaines courants')
    p.add_argument('--wordlist', help='chemin vers wordlist (un mot par ligne)')
    args = p.parse_args()  # parse args
    res = resolve_records(args.domain)  # call fn
    for rtype, vals in res.items():
        print(f"{rtype}:")
        if not vals:
            print('  (aucune)')  # pas d'enrs
        for v in vals:
            print(f"  {v}")  # affiche chaque val

    if getattr(args, 'txt', False):
        print('\nRésultats TXT:')
        txt = parse_txt(args.domain)
        print(' brut:')
        for r in txt['raw']:
            print('  ', r)
        print(' domaines:')
        for d in txt['domains']:
            print('  ', d)
        print(' IPs:')
        for ip in txt['ips']:
            print('  ', ip)

    if getattr(args, 'crawl', False):
        print('\nParents jusqu au TLD:')
        parents = crawl_to_tld(args.domain)
        for pdom in parents:
            print('  ', pdom)

    if getattr(args, 'srv', False):
        print('\nSRV scan:')
        srv = scan_srv(args.domain)
        for svc, entries in srv.items():
            print(f" {svc}:")
            if not entries:
                print('   (aucun)')
            for e in entries:
                print(f"   - {e['target']}:{e['port']} p={e['priority']} w={e['weight']}")

    if getattr(args, 'rev', False):
        print('\nReverse DNS:')
        # collect IPs résolus
        ips = []
        for vals in res.values():
            for ip in vals:
                if ip not in ips:
                    ips.append(ip)
        if not ips:
            print('  (aucune IP trouvée)')
        for ip in ips:
            ptrs = reverse_lookup(ip)
            if ptrs:
                for p in ptrs:
                    print(f"  {ip} -> {p}")
            else:
                print(f"  {ip} -> (aucun PTR)")

    if getattr(args, 'sub', False):
        print('\nSous-domaines découverts:')
        wl = None
        if getattr(args, 'wordlist', None):
            wl = []
            try:
                from dnsmap.subenum import load_wordlist
                wl = load_wordlist(args.wordlist)
            except Exception:
                wl = None
        subs = enumerate_subdomains(args.domain, wl)
        if not subs:
            print('  (aucun)')
        for s in subs:
            print(f"  {s['sub']}")
            if s['A']:
                for a in s['A']:
                    print('    A:', a)
            if s['AAAA']:
                for a in s['AAAA']:
                    print('    AAAA:', a)
            if s['CNAME']:
                for c in s['CNAME']:
                    print('    CNAME:', c)


if __name__ == '__main__':
    # lance la CLI
    main()
