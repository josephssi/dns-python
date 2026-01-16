from graphviz import Digraph
from graphviz.backend.execute import ExecutableNotFound


def _add_node(g: Digraph, name: str, kind: str = 'domain', added: set | None = None) -> str:
    # style: domain = ellipse (lightblue), ip = box (lightgrey)
    # Return a safe node id for use in edges; keep `added` as original names.
    if added is None:
        added = set()
    if name in added:
        # build same safe id
        safe_id = name.replace(':', '_')
        return safe_id
    safe_id = name.replace(':', '_')
    if kind == 'ip':
        g.node(safe_id, label=name, shape='box', style='filled', fillcolor='#f2f2f2')
    else:
        g.node(safe_id, label=name, shape='ellipse', style='filled', fillcolor='#d9edf7')
    added.add(name)
    return safe_id


def build_graph(domain: str, include=None) -> Digraph:
    """Build a Digraph representing DNS relations for `domain`.

    include: set of strategy keys (a, txt, crawl, srv, sub, rev, neighbors)
    """
    if include is None:
        include = {'a', 'txt', 'crawl', 'srv', 'sub', 'rev', 'neighbors'}

    g = Digraph(comment=f'Carto DNS {domain}')
    added: set = set()

    domain_id = _add_node(g, domain, kind='domain', added=added)

    # A / AAAA
    if 'a' in include:
        try:
            from .resolver import resolve_records
            recs = resolve_records(domain)
            for rtype, vals in recs.items():
                for v in vals:
                    v_id = _add_node(g, v, kind='ip', added=added)
                    g.edge(domain_id, v_id, label=rtype)
        except Exception:
            pass

    # TXT
    if 'txt' in include:
        try:
            from .txtparser import parse_txt
            txt = parse_txt(domain)
            for rd in txt.get('domains', []):
                rd_id = _add_node(g, rd, kind='domain', added=added)
                g.edge(domain_id, rd_id, label='TXT')
            for ip in txt.get('ips', []):
                ip_id = _add_node(g, ip, kind='ip', added=added)
                g.edge(domain_id, ip_id, label='TXT')
        except Exception:
            pass

    # crawl
    if 'crawl' in include:
        try:
            from .crawl import crawl_to_tld
            parents = crawl_to_tld(domain)
            for p in parents:
                p_id = _add_node(g, p, kind='domain', added=added)
                g.edge(domain_id, p_id, label='parent')
        except Exception:
            pass

    # srv
    if 'srv' in include:
        try:
            from .srvscan import scan_srv
            srv = scan_srv(domain)
            for svc, entries in srv.items():
                for e in entries:
                    tgt = e.get('target')
                    tgt_id = _add_node(g, tgt, kind='domain', added=added)
                    lab = f"SRV {svc} :{e.get('port')}"
                    g.edge(domain_id, tgt_id, label=lab)
        except Exception:
            pass

    # subdomains
    if 'sub' in include:
        try:
            from .subenum import enumerate_subdomains
            subs = enumerate_subdomains(domain)
            for s in subs:
                subdom = s.get('sub')
                sub_id = _add_node(g, subdom, kind='domain', added=added)
                g.edge(domain_id, sub_id, label='sub')
                for a in s.get('A', []):
                    a_id = _add_node(g, a, kind='ip', added=added)
                    g.edge(sub_id, a_id, label='A')
                for a in s.get('AAAA', []):
                    a_id = _add_node(g, a, kind='ip', added=added)
                    g.edge(sub_id, a_id, label='AAAA')
                for c in s.get('CNAME', []):
                    c_id = _add_node(g, c, kind='domain', added=added)
                    g.edge(sub_id, c_id, label='CNAME')
        except Exception:
            pass

    # reverse
    if 'rev' in include:
        try:
            from .reverse import reverse_lookup
            ips = [n for n in added if n.count('.') == 3 and all(p.isdigit() for p in n.split('.'))]
            for ip in ips:
                ip_id = _add_node(g, ip, kind='ip', added=added)
                ptrs = reverse_lookup(ip)
                for p in ptrs:
                    p_id = _add_node(g, p, kind='domain', added=added)
                    g.edge(ip_id, p_id, label='PTR')
        except Exception:
            pass

    # neighbors
    if 'neighbors' in include:
        try:
            from .ipneighbors import neighbors as ip_neighbors
            ips = [n for n in added if n.count('.') == 3 and all(p.isdigit() for p in n.split('.'))]
            for ip in ips:
                ip_id = _add_node(g, ip, kind='ip', added=added)
                neigh = ip_neighbors(ip, radius=1)
                for n in neigh:
                    nip = n['ip']
                    nip_id = _add_node(g, nip, kind='ip', added=added)
                    g.edge(ip_id, nip_id, label='neighbor')
        except Exception:
            pass

    return g


def render_graph(domain: str, outpath: str = 'dnsmap', fmt: str = 'png') -> str:
    g = build_graph(domain)
    g.format = fmt
    try:
        filename = g.render(filename=outpath, cleanup=True)
        return filename
    except ExecutableNotFound:
        # Graphviz native `dot` not found: export DOT source for manual rendering
        dotpath = outpath if outpath.endswith('.dot') else outpath + '.dot'
        with open(dotpath, 'w', encoding='utf-8') as f:
            f.write(g.source)
        return dotpath
