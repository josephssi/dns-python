from src.dnsmap.txtparser import parse_txt_from_strings


def test_parse_txt_from_strings_basic():
    txts = [
        "v=spf1 include:_spf.google.com ip4:198.51.100.23 -all",
        "some text mail.example.com another.example.org",
    ]
    out = parse_txt_from_strings(txts)
    assert "198.51.100.23" in out["ips"]
    assert "mail.example.com" in out["domains"]
    assert "another.example.org" in out["domains"]
