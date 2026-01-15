import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))  # pr dev import

from dnsmap import resolve_records, parse_txt, crawl_to_tld, scan_srv  # fn pr resolve + txt + crawl + srv

# petit CLI pr test rapide


def main():
    p = argparse.ArgumentParser(description='Résolution DNS basique (A/AAAA)')
    p.add_argument('domain', help='domaine à analyser')
    p.add_argument('--txt', action='store_true', help='parser les enregistrements TXT')
    p.add_argument('--crawl', action='store_true', help='remonter aux domaines parents (TLD)')
    p.add_argument('--srv', action='store_true', help='scanner les enregistrements SRV')
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


if __name__ == '__main__':
    # lance la CLI
    main()
