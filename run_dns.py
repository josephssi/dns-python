import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))  # pr dev import

from colorama import init as colorama_init, Fore, Style

colorama_init()

from dnsmap import (
    resolve_records,
    parse_txt,
    crawl_to_tld,
    scan_srv,
    reverse_lookup,
    enumerate_subdomains,
    ip_neighbors,
)  # fn pr resolve + txt + crawl + srv + rev + sub + neigh
from dnsmap.graphout import render_graph

# petit CLI pr test rapide + sortie colorée


def main():
    p = argparse.ArgumentParser(description="Résolution DNS basique (A/AAAA)")
    p.add_argument("domain", help="domaine à analyser")
    p.add_argument("--txt", action="store_true", help="parser les enregistrements TXT")
    p.add_argument(
        "--crawl", action="store_true", help="remonter aux domaines parents (TLD)"
    )
    p.add_argument("--srv", action="store_true", help="scanner les enregistrements SRV")
    p.add_argument(
        "--rev", action="store_true", help="reverse DNS (PTR) des IPs résolues"
    )
    p.add_argument(
        "--sub", action="store_true", help="brute-force sous-domaines courants"
    )
    p.add_argument("--wordlist", help="chemin vers wordlist (un mot par ligne)")
    p.add_argument(
        "--neighbors", action="store_true", help="rechercher IP voisines (IPv4)"
    )
    p.add_argument(
        "--radius", type=int, default=2, help="rayon pour IP voisines (défaut: 2)"
    )
    p.add_argument(
        "--graph", help="générer un graphe (chemin sans extension), ex: out/dnsmap"
    )
    p.add_argument(
        "--graph-format", default="png", help="format du graphe (png, pdf, svg)"
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="exporter un rapport Markdown simple sous out/report.md",
    )
    args = p.parse_args()  # parse args
    # si aucun flag de stratégie fourni, on active tout par défaut
    strategy_flags = ["txt", "crawl", "srv", "rev", "sub", "neighbors"]
    if not any(getattr(args, f) for f in strategy_flags):
        for f in strategy_flags:
            setattr(args, f, True)

    res = resolve_records(args.domain)  # call fn

    # couleurs
    HDR = Fore.CYAN + Style.BRIGHT
    TYP = Fore.YELLOW + Style.BRIGHT
    VAL = Fore.GREEN
    RST = Style.RESET_ALL

    # affiche records A/AAAA
    for rtype, vals in res.items():
        print(f"{HDR}{rtype}:{RST}")
        if not vals:
            print("  (aucune)")
        for v in vals:
            print(f"  {TYP}{v}{RST}")

    if getattr(args, "txt", False):
        print(f"\n{HDR}Résultats TXT:{RST}")
        txt = parse_txt(args.domain)
        print(f"{TYP} brut:{RST}")
        for r in txt["raw"]:
            print("  ", r)
        print(f"{TYP} domaines:{RST}")
        for d in txt["domains"]:
            print("  ", d)
        print(f"{TYP} IPs:{RST}")
        for ip in txt["ips"]:
            print("  ", ip)

    if getattr(args, "crawl", False):
        print(f"\n{HDR}Parents jusqu au TLD:{RST}")
        parents = crawl_to_tld(args.domain)
        for pdom in parents:
            print("  ", pdom)

    if getattr(args, "srv", False):
        print(f"\n{HDR}SRV scan:{RST}")
        srv = scan_srv(args.domain)
        for svc, entries in srv.items():
            print(f" {TYP}{svc}:{RST}")
            if not entries:
                print("   (aucun)")
            for e in entries:
                print(
                    f"   - {VAL}{e['target']}:{e['port']}{RST} p={e['priority']} w={e['weight']}"
                )

    if getattr(args, "rev", False):
        print(f"\n{HDR}Reverse DNS:{RST}")
        # collect only A/AAAA IPs
        ips = []
        for ip in res.get("A", []) + res.get("AAAA", []):
            if ip not in ips:
                ips.append(ip)
        if not ips:
            print("  (aucune IP trouvée)")
        for ip in ips:
            ptrs = reverse_lookup(ip)
            if ptrs:
                for p in ptrs:
                    print(f"  {VAL}{ip}{RST} -> {p}")
            else:
                print(f"  {VAL}{ip}{RST} -> (aucun PTR)")

    if getattr(args, "sub", False):
        print(f"\n{HDR}Sous-domaines découverts:{RST}")
        wl = None
        if getattr(args, "wordlist", None):
            wl = []
            try:
                from dnsmap.subenum import load_wordlist

                wl = load_wordlist(args.wordlist)
            except Exception:
                wl = None
        subs = enumerate_subdomains(args.domain, wl)
        if not subs:
            print("  (aucun)")
        for s in subs:
            print(f"  {TYP}{s['sub']}{RST}")
            if s["A"]:
                for a in s["A"]:
                    print(f"    A: {VAL}{a}{RST}")
            if s["AAAA"]:
                for a in s["AAAA"]:
                    print(f"    AAAA: {VAL}{a}{RST}")
            if s["CNAME"]:
                for c in s["CNAME"]:
                    print(f"    CNAME: {c}")

    if getattr(args, "neighbors", False):
        print(f"\n{HDR}IP voisines:{RST}")
        # on récupère les IPs résolues (A seulement)
        ips = []
        for vals in res.get("A", []), res.get("AAAA", []):
            for ip in vals:
                if ip not in ips:
                    ips.append(ip)
        if not ips:
            print("  (aucune IP trouvée)")
        for ip in ips:
            neigh = ip_neighbors(ip, args.radius)
            print(f"  pour {VAL}{ip}{RST}:")
            for n in neigh:
                if n["ptrs"]:
                    print(f"    {n['ip']} -> {', '.join(n['ptrs'])}")
                else:
                    print(f"    {n['ip']} -> (aucun PTR)")

    if getattr(args, "report", False):
        # minimal Markdown report
        outdir = Path("out")
        outdir.mkdir(exist_ok=True)
        rpt = outdir / "report.md"
        with open(rpt, "w", encoding="utf-8") as f:
            f.write(f"# Rapport DNS pour {args.domain}\n\n")
            f.write("## A/AAAA/MX/CNAME/SOA\n\n")
            for rtype, vals in res.items():
                f.write(f"### {rtype}\n")
                if not vals:
                    f.write("- (aucune)\n")
                for v in vals:
                    f.write(f"- {v}\n")
                f.write("\n")
            f.write("## TXT (domains / ips)\n")
            txt = parse_txt(args.domain)
            for d in txt["domains"]:
                f.write(f"- domain: {d}\n")
            for ip in txt["ips"]:
                f.write(f"- ip: {ip}\n")
        print(f"{HDR}Rapport généré:{RST} {rpt}")

    # graph si demandé
    if getattr(args, "graph", None):
        out = render_graph(args.domain, outpath=args.graph, fmt=args.graph_format)
        print(f"{HDR}Graphe généré:{RST} {out}")


if __name__ == "__main__":
    # lance la CLI
    main()
