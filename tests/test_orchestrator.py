import dnsmap.orchestrator as orchestrator


def test_orchestrator_depth(monkeypatch):
    # fake network functions to exercise depth logic deterministically

    def fake_resolve_records(name):
        return {"A": []}

    def fake_parse_txt(name):
        # only root provides a TXT-discovered child
        if name == "root.test":
            return {"raw": ["v"], "domains": ["txt1.root.test"], "ips": []}
        if name == "txt1.root.test":
            return {"raw": ["v"], "domains": ["txt2.root.test"], "ips": []}
        return {"raw": [], "domains": [], "ips": []}

    def fake_enumerate_subdomains(name, wl=None):
        if name == "root.test":
            return [{"sub": "sub1.root.test", "A": [], "AAAA": [], "CNAME": []}]
        return []

    def fake_crawl(name):
        return []

    def fake_scan_srv(name):
        return {}

    def fake_reverse_lookup(ip):
        return []

    def fake_neighbors(ip, radius=2):
        return []

    # patch orchestrator module functions
    monkeypatch.setattr(orchestrator, "resolve_records", fake_resolve_records)
    monkeypatch.setattr(orchestrator, "parse_txt", fake_parse_txt)
    monkeypatch.setattr(orchestrator, "enumerate_subdomains", fake_enumerate_subdomains)
    monkeypatch.setattr(orchestrator, "crawl_to_tld", fake_crawl)
    monkeypatch.setattr(orchestrator, "scan_srv", fake_scan_srv)
    monkeypatch.setattr(orchestrator, "reverse_lookup", fake_reverse_lookup)
    monkeypatch.setattr(orchestrator, "ip_neighbors", fake_neighbors)

    # depth 0 -> only root
    out0 = orchestrator.orchestrate("root.test", depth=0)
    assert "root.test" in out0["domains"]
    assert len(out0["domains"]) == 1

    # depth 1 -> root + txt1 + sub1
    out1 = orchestrator.orchestrate("root.test", depth=1)
    domains1 = set(out1["domains"])
    assert "root.test" in domains1
    assert "txt1.root.test" in domains1
    assert "sub1.root.test" in domains1

    # depth 2 -> includes txt2 (child discovered from txt1)
    out2 = orchestrator.orchestrate("root.test", depth=2)
    domains2 = set(out2["domains"])
    assert "txt2.root.test" in domains2
