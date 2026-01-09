import tldextract


def crawl_to_tld(domain: str) -> list:
    """Return parent domains up to the public suffix (inclusive).

    Example: for `a.b.c.d.e.f.gouv.fr` returns:
      ['b.c.d.e.f.gouv.fr', 'c.d.e.f.gouv.fr', ..., 'f.gouv.fr']
    Stops at the public suffix (so it won't return only 'fr').
    """
    labels = domain.strip().split('.')
    if len(labels) <= 1:
        return []

    ext = tldextract.extract(domain)
    public_suffix = ext.suffix  # e.g. 'social.gouv.fr'

    parents = []
    n = len(labels)
    for i in range(1, n):
        candidate = '.'.join(labels[i:])
        parents.append(candidate)
        if candidate == public_suffix:
            break

    return parents


if __name__ == '__main__':
    print(crawl_to_tld('sirena.integration.dev.atlas.fabrique.social.gouv.fr'))
