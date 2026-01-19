# DNS Map

Outil pour analyser rapidement les enregistrements DNS d'un domaine
et produire une cartographie simple.

Principales fonctionnalités
- Résolution des enregistrements A, AAAA, MX, CNAME, SOA
- Extraction et parsing basique des enregistrements TXT
- Scan SRV pour services courants
- Reverse (PTR) pour les IP trouvées
- Énumération simple de sous-domaines (wordlist)
- Recherche d'adresses IP voisines (IPv4)
- Export du graphe en `.dot` (Graphviz) et rendu en image si `dot` est installé

Prérequis
- Python 3.8+
- Installer les dépendances listées dans `requirements.txt`
- (optionnel) Graphviz natif (`dot`) pour générer des images à partir du `.dot`

Installation rapide

```powershell
git clone <repo-url>
cd projet
python -m venv .venv
& .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Exemples d'utilisation

```powershell
# Analyse complète et export du graphe (PNG si dot sur PATH)
python run_dns.py example.com --graph out/dnsmap --graph-format png

# Même chose sans dot : génère out/dnsmap.dot
python run_dns.py example.com --graph out/dnsmap

# Générer un rapport Markdown minimal
python run_dns.py example.com --report
```

Sorties
- Sortie texte colorée dans la console (A/AAAA, TXT, MX, SRV, etc.)
- Fichier `out/dnsmap.dot` si `--graph` demandé; rendu image si `dot` disponible
- Rapport Markdown `out/report.md` si `--report` demandé

Conversion manuelle du DOT (si nécessaire)

```powershell
& "C:\Program Files\Graphviz\bin\dot.exe" -Tpng out/dnsmap.dot -o out/dnsmap.png
ii out\dnsmap.png
```

Dépannage rapide
- Si `dot` n'est pas trouvé, vérifie que Graphviz est installé et que son dossier `bin` est dans `PATH`.
- Les requêtes DNS nécessitent un accès réseau.



