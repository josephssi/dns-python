import os
import shutil
import subprocess
from graphviz import Digraph
from graphviz.backend.execute import ExecutableNotFound


def _add_node(
    g: Digraph, name: str, kind: str = "domain", added: set | None = None
) -> str:
    # style: domain = ellipse (lightblue), ip = box (lightgrey)
    # Return a safe node id for use in edges; keep `added` as original names.
    if added is None:
        added = set()
    if name in added:
        # build same safe id
        safe_id = name.replace(":", "_")
        return safe_id
    safe_id = name.replace(":", "_")
    if kind == "ip":
        g.node(
            safe_id,
            label=name,
            shape="box",
            style="filled",
            fillcolor="#f2f2f2",
        )
    else:
        g.node(
            safe_id,
            label=name,
            shape="ellipse",
            style="filled",
            fillcolor="#d9edf7",
        )
    added.add(name)
    return safe_id


def build_graph(domain: str, include=None, orchestrator_data=None) -> Digraph:
    """Build a Digraph representing DNS relations for `domain`.

    include: set of strategy keys (a, txt, crawl, srv, sub, rev, neighbors)
    """
    if include is None:
        include = {"a", "txt", "crawl", "srv", "sub", "rev", "neighbors"}

    g = Digraph(comment=f"Carto DNS {domain}")
    added: set = set()

    domain_id = _add_node(g, domain, kind="domain", added=added)

    # If orchestrator_data provided, use it to build a multi-node graph.
    if orchestrator_data is not None:
        try:
            recs_map = orchestrator_data.get("records", {})
            txts_map = orchestrator_data.get("txts", {})
            subs_map = orchestrator_data.get("subs", {})
            edges = orchestrator_data.get("edges", [])
            # add nodes for all discovered domains and records
            for d, recs in recs_map.items():
                d_id = _add_node(g, d, kind="domain", added=added)
                for rtype, vals in (recs or {}).items():
                    for v in vals:
                        if rtype in ("A", "AAAA"):
                            v_id = _add_node(g, v, kind="ip", added=added)
                            g.edge(d_id, v_id, label=rtype)
                        else:
                            v_id = _add_node(g, v, kind="domain", added=added)
                            g.edge(d_id, v_id, label=rtype)

            # TXT relations
            for d, t in txts_map.items():
                d_id = _add_node(g, d, kind="domain", added=added)
                for rd in t.get("domains", []):
                    rd_id = _add_node(g, rd, kind="domain", added=added)
                    g.edge(d_id, rd_id, label="TXT")
                for ip in t.get("ips", []):
                    ip_id = _add_node(g, ip, kind="ip", added=added)
                    g.edge(d_id, ip_id, label="TXT")

            # subdomains
            for d, s_list in subs_map.items():
                d_id = _add_node(g, d, kind="domain", added=added)
                for s in s_list:
                    subdom = s.get("sub")
                    sub_id = _add_node(g, subdom, kind="domain", added=added)
                    g.edge(d_id, sub_id, label="sub")
                    for a in s.get("A", []):
                        a_id = _add_node(g, a, kind="ip", added=added)
                        g.edge(sub_id, a_id, label="A")

            # explicit edges collected by orchestrator
            for a, b, rel in edges:
                a_id = _add_node(g, a, kind=("ip" if ":" in a or a.count(".") == 4 else "domain"), added=added)
                b_id = _add_node(g, b, kind=("ip" if ":" in b or b.count(".") == 4 else "domain"), added=added)
                g.edge(a_id, b_id, label=rel)
        except Exception:
            # fall back to single-domain behavior on any error
            orchestrator_data = None

    # A / AAAA / MX / CNAME / SOA (single-domain fallback)
    if orchestrator_data is None and "a" in include:
        try:
            from .resolver import resolve_records

            recs = resolve_records(domain)
            for rtype, vals in recs.items():
                for v in vals:
                    # treat by record type
                    if rtype in ("A", "AAAA"):
                        v_id = _add_node(g, v, kind="ip", added=added)
                        g.edge(domain_id, v_id, label=rtype)
                    elif rtype == "MX":
                        # MX value typically looks like: "10 mail.example.com."
                        # we take the last token as the mail exchanger host
                        parts = v.split()
                        exch = parts[-1].rstrip(".") if parts else v
                        exch_id = _add_node(g, exch, kind="domain", added=added)
                        priority = parts[0] if parts and parts[0].isdigit() else ""
                        mx_label = f"MX {priority}".strip()
                        g.edge(domain_id, exch_id, label=mx_label)
                    elif rtype == "CNAME":
                        tgt = v.rstrip(".")
                        tgt_id = _add_node(g, tgt, kind="domain", added=added)
                        g.edge(domain_id, tgt_id, label="CNAME")
                    elif rtype == "SOA":
                        # SOA is a long record; create a node with the raw SOA as label
                        soa_label = v
                        soa_id = _add_node(
                            g, f"SOA: {domain}", kind="domain", added=added
                        )
                        # store label separately by setting node's label explicitly
                        # Graphviz nodes use the node name as the default label.
                        # Create a unique node id and set the visible label with the
                        # `label` attribute instead.
                        g.node(
                            soa_id,
                            label=soa_label,
                            shape="note",
                            style="filled",
                            fillcolor="#fff2cc",
                        )
                        g.edge(domain_id, soa_id, label="SOA")
                    else:
                        # generic fallback: treat as domain
                        node_id = _add_node(g, v, kind="domain", added=added)
                        g.edge(domain_id, node_id, label=rtype)
        except Exception:
            pass

    # TXT
    if "txt" in include:
        try:
            from .txtparser import parse_txt

            txt = parse_txt(domain)
            for rd in txt.get("domains", []):
                rd_id = _add_node(g, rd, kind="domain", added=added)
                g.edge(domain_id, rd_id, label="TXT")
            for ip in txt.get("ips", []):
                ip_id = _add_node(g, ip, kind="ip", added=added)
                g.edge(domain_id, ip_id, label="TXT")
        except Exception:
            pass

    # crawl
    if "crawl" in include:
        try:
            from .crawl import crawl_to_tld

            parents = crawl_to_tld(domain)
            for p in parents:
                p_id = _add_node(g, p, kind="domain", added=added)
                g.edge(domain_id, p_id, label="parent")
        except Exception:
            pass

    # srv
    if "srv" in include:
        try:
            from .srvscan import scan_srv

            srv = scan_srv(domain)
            for svc, entries in srv.items():
                for e in entries:
                    tgt = e.get("target")
                    tgt_id = _add_node(g, tgt, kind="domain", added=added)
                    port = e.get('port')
                    lab = f"SRV {svc} :{port}"
                    g.edge(
                        domain_id,
                        tgt_id,
                        label=lab,
                    )
        except Exception:
            pass

    # subdomains
    if "sub" in include:
        try:
            from .subenum import enumerate_subdomains

            subs = enumerate_subdomains(domain)
            for s in subs:
                subdom = s.get("sub")
                sub_id = _add_node(g, subdom, kind="domain", added=added)
                g.edge(domain_id, sub_id, label="sub")
                for a in s.get("A", []):
                    a_id = _add_node(g, a, kind="ip", added=added)
                    g.edge(sub_id, a_id, label="A")
                for a in s.get("AAAA", []):
                    a_id = _add_node(g, a, kind="ip", added=added)
                    g.edge(sub_id, a_id, label="AAAA")
                    print(f"joseph je t'aime")
                for c in s.get("CNAME", []):
                    c_id = _add_node(g, c, kind="domain", added=added)
                    g.edge(sub_id, c_id, label="CNAME")
        except Exception:
            pass

    # reverse
    if "rev" in include:
        try:
            from .reverse import reverse_lookup

            def _is_ipv4_like(name: str) -> bool:
                parts = name.split('.')
                return len(parts) == 4 and all(p.isdigit() for p in parts)

            ips = [n for n in added if _is_ipv4_like(n)]
            for ip in ips:
                ip_id = _add_node(g, ip, kind="ip", added=added)
                ptrs = reverse_lookup(ip)
                for p in ptrs:
                    p_id = _add_node(g, p, kind="domain", added=added)
                    g.edge(ip_id, p_id, label="PTR")
        except Exception:
            pass

    # neighbors
    if "neighbors" in include:
        try:
            from .ipneighbors import neighbors as ip_neighbors

            ips = [n for n in added if _is_ipv4_like(n)]
            for ip in ips:
                ip_id = _add_node(g, ip, kind="ip", added=added)
                neigh = ip_neighbors(ip, radius=1)
                for n in neigh:
                    nip = n["ip"]
                    nip_id = _add_node(g, nip, kind="ip", added=added)
                    g.edge(ip_id, nip_id, label="neighbor")
        except Exception:
            pass

    return g


def render_graph(domain: str, outpath: str = "dnsmap", fmt: str = "png") -> str:
    g = build_graph(domain)
    g.format = fmt
    try:
        # Ensure output directory exists and remove any previous output to
        # guarantee the PNG is regenerated/overwritten on each run.
        outfile = outpath if outpath.endswith(f".{fmt}") else outpath + f".{fmt}"
        outdir = os.path.dirname(outfile)
        if outdir:
            os.makedirs(outdir, exist_ok=True)
        if os.path.exists(outfile):
            try:
                os.remove(outfile)
            except OSError:
                pass

        filename = g.render(filename=outpath, cleanup=True)
        # g.render returns the path to the rendered file; normalize to the
        # expected output path (with extension) for callers.
        return outfile if os.path.exists(outfile) else filename
    except ExecutableNotFound:
        # Graphviz native `dot` not found: export DOT source for manual rendering
        dotpath = outpath if outpath.endswith(".dot") else outpath + ".dot"
        with open(dotpath, "w", encoding="utf-8") as f:
            f.write(g.source)
        # If `dot` is not found by graphviz, try to locate and call it
        # explicitly from common install locations or via shutil.which.
        outfile = outpath if outpath.endswith(f".{fmt}") else outpath + f".{fmt}"
        dot_exec = shutil.which("dot")
        if not dot_exec:
            candidates = [
                r"C:\Program Files\Graphviz\bin\dot.exe",
                r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
            ]
            for c in candidates:
                if os.path.exists(c):
                    dot_exec = c
                    break

        if dot_exec:
            try:
                # ensure output dir exists
                outdir = os.path.dirname(outfile)
                if outdir:
                    os.makedirs(outdir, exist_ok=True)
                if os.path.exists(outfile):
                    try:
                        os.remove(outfile)
                    except OSError:
                        pass
                cmd = [dot_exec, f"-T{fmt}", dotpath, "-o", outfile]
                subprocess.run(cmd, check=True)
                return outfile
            except Exception:
                # fall through to Source fallback
                pass

        # Try to render via graphviz.Source as a fallback (may still require
        # native `dot`). If that fails, return the .dot path for manual
        # rendering.
        try:
            from graphviz import Source

            s = Source(g.source)
            s.format = fmt
            # ensure output dir exists
            outdir = os.path.dirname(outfile)
            if outdir:
                os.makedirs(outdir, exist_ok=True)
            if os.path.exists(outfile):
                try:
                    os.remove(outfile)
                except OSError:
                    pass
            s.render(filename=outpath, cleanup=True)
            return outfile
        except Exception:
            return dotpath
