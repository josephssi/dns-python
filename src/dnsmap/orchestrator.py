from collections import deque
from typing import Dict, List, Tuple, Set, Any, Optional

from .resolver import resolve_records
from .txtparser import parse_txt
from .subenum import enumerate_subdomains
from .crawl import crawl_to_tld
from .srvscan import scan_srv
from .reverse import reverse_lookup
from .ipneighbors import neighbors as ip_neighbors


def orchestrate(
    root: str,
    depth: int = 1,
    strategies: Optional[Dict[str, bool]] = None,
    wordlist: Optional[List[str]] = None,
    radius: int = 2,
) -> Dict[str, Any]:
    """Crawl DNS starting from `root` up to `depth` levels.

    strategies: dict with keys 'txt','sub','crawl','srv','rev','neighbors'
    Returns aggregated results for discovered domains and simple edges for graphing.
    """
    if strategies is None:
        strategies = {k: True for k in ["txt", "sub", "crawl", "srv", "rev", "neighbors"]}

    q = deque()
    q.append((root, 0))
    visited: Set[str] = set()
    records: Dict[str, Dict[str, List[str]]] = {}
    txts: Dict[str, Dict[str, List[str]]] = {}
    subs: Dict[str, List[Dict[str, Any]]] = {}
    srvs: Dict[str, Dict[str, Any]] = {}
    neighs: Dict[str, List[Dict[str, Any]]] = {}
    reverse_map: Dict[str, List[str]] = {}
    edges: List[Tuple[str, str, str]] = []

    while q:
        dom, level = q.popleft()
        if dom in visited:
            continue
        visited.add(dom)

        try:
            rec = resolve_records(dom)
        except Exception:
            rec = {}
        records[dom] = rec

        # TXT
        if strategies.get("txt", False):
            try:
                t = parse_txt(dom)
            except Exception:
                t = {"raw": [], "domains": [], "ips": []}
            txts[dom] = t
            # discovered domains from TXT are expansion candidates
            if level < depth:
                for d in t.get("domains", []):
                    if d not in visited:
                        q.append((d, level + 1))
                        edges.append((dom, d, "txt"))

        # subdomains
        if strategies.get("sub", False) and level < depth:
            try:
                s = enumerate_subdomains(dom, wordlist)
            except Exception:
                s = []
            subs[dom] = s
            for ent in s:
                subname = ent.get("sub")
                if subname and subname not in visited:
                    q.append((subname, level + 1))
                    edges.append((dom, subname, "sub"))

        # crawl to parents
        if strategies.get("crawl", False) and level < depth:
            try:
                parents = crawl_to_tld(dom)
            except Exception:
                parents = []
            for p in parents:
                if p not in visited:
                    q.append((p, level + 1))
                    edges.append((dom, p, "parent"))

        # SRV
        if strategies.get("srv", False):
            try:
                ssv = scan_srv(dom)
            except Exception:
                ssv = {}
            srvs[dom] = ssv

        # neighbors (based on A records)
        if strategies.get("neighbors", False):
            ips = rec.get("A", []) + rec.get("AAAA", [])
            for ip in ips:
                try:
                    n = ip_neighbors(ip, radius)
                except Exception:
                    n = []
                if n:
                    neighs[ip] = n
                    # add PTR targets as discovered domains
                    if level < depth:
                        for ent in n:
                            for p in ent.get("ptrs", []) or []:
                                if p not in visited:
                                    q.append((p, level + 1))
                                    edges.append((ip, p, "ptr"))

        # reverse (PTR) for resolved IPs
        if strategies.get("rev", False):
            ips = rec.get("A", []) + rec.get("AAAA", [])
            for ip in ips:
                try:
                    ptrs = reverse_lookup(ip)
                except Exception:
                    ptrs = []
                if ptrs:
                    reverse_map[ip] = ptrs
                    if level < depth:
                        for p in ptrs:
                            if p not in visited:
                                q.append((p, level + 1))
                                edges.append((ip, p, "ptr"))

    return {
        "root": root,
        "domains": list(visited),
        "records": records,
        "txts": txts,
        "subs": subs,
        "srvs": srvs,
        "neighbors": neighs,
        "reverse": reverse_map,
        "edges": edges,
    }
