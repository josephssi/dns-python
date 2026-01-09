
import tldextract


# petit module pr remonter aux domaines parents jusqu'au suffixe public
def crawl_to_tld(domain: str) -> list:
    """Renvoie les domaines parents jusqu'au suffixe public."""
    # découpe en étiquettes
    labels = domain.strip().split('.')
    if len(labels) <= 1:
        return []

    # utilise tldextract pour connaître le suffixe public (ex: 'social.gouv.fr')
    ext = tldextract.extract(domain)
    public_suffix = ext.suffix

    parents = []
    n = len(labels)
    # construit les parents en enlevant l'étiquette gauche
    for i in range(1, n):
        candidate = '.'.join(labels[i:])
        parents.append(candidate)
        # si on atteint le suffixe public, on s'arrête
        if candidate == public_suffix:
            break

    return parents



