import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))  # pr dev import

from dnsmap import resolve_records, parse_txt  # fn pr resolve + txt

# petit CLI pr test rapide


def main():
    p = argparse.ArgumentParser(description='Simple DNS A/AAAA resolver')
    p.add_argument('domain', help='domaine à analyser')
    p.add_argument('--txt', action='store_true', help='parse TXT records')
    args = p.parse_args()  # parse args
    res = resolve_records(args.domain)  # call fn
    for rtype, vals in res.items():
        print(f"{rtype}:")
        if not vals:
            print('  (aucune)')  # pas d'enrs
        for v in vals:
            print(f"  {v}")  # affiche chaque val

    if getattr(args, 'txt', False):
        print('\nTXT parse:')
        txt = parse_txt(args.domain)
        print(' raw:')
        for r in txt['raw']:
            print('  ', r)
        print(' domains:')
        for d in txt['domains']:
            print('  ', d)
        print(' ips:')
        for ip in txt['ips']:
            print('  ', ip)


if __name__ == '__main__':
    # lance la CLI
    main()
