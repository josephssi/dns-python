import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))  # pr dev import

from dnsmap import resolve_records  # fn pr resolve

# petit CLI pr test rapide


def main():
    p = argparse.ArgumentParser(description='Simple DNS A/AAAA resolver')
    p.add_argument('domain', help='domaine à analyser')
    args = p.parse_args()  # parse args
    res = resolve_records(args.domain)  # call fn
    for rtype, vals in res.items():
        print(f"{rtype}:")
        if not vals:
            print('  (aucune)')  # pas d'enrs
        for v in vals:
            print(f"  {v}")  # affiche chaque val


if __name__ == '__main__':
    # lance la CLI
    main()
