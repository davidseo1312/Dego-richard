#!/usr/bin/env python3
"""
Contrôle de l'indexabilité réelle des pages.

    python3 scripts/check-indexation.py

Une page « indexable » n'est pas seulement une page qui répond 200. Elle doit
aussi être trouvable, se désigner elle-même, et ne pas être contredite par une
autre. Le script vérifie donc, sur le dossier construit :

  1. REDIRECTIONS — aucune règle 301 ne doit boucler sur elle-même, en
     chaîner une autre, viser une page inexistante, ni recouvrir une page
     réelle. Une boucle rend la page définitivement inaccessible : c'est
     arrivé sur /services, et rien ne le voyait parce que l'aperçu local
     n'applique pas le .htaccess.
  2. ORPHELINES — une page qu'aucune autre ne relie n'existe que par le
     sitemap. Google la découvre, la classe comme secondaire, et souvent ne
     l'indexe pas.
  3. PROFONDEUR — nombre de clics depuis l'accueil. Au-delà de trois, une page
     est explorée rarement.
  4. CANONIQUE — chaque page doit se désigner elle-même, et deux pages ne
     doivent jamais revendiquer la même adresse.
  5. SITEMAP — toute page indexable y figure, et rien d'autre.
  6. NOINDEX — cohérent avec le sitemap et avec les liens internes.

Rend 1 si un défaut bloquant est constaté, 0 sinon.
"""

import re
import sys
from collections import deque
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
OUT = RACINE / "public"
HTACCESS = RACINE / "static" / ".htaccess"

# Pages volontairement hors index : elles n'ont rien à faire dans les
# résultats de recherche, et leur absence du sitemap est voulue.
HORS_INDEX = {"/404", "/merci"}

VERT, ROUGE, JAUNE, GRAS, FIN = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"
defauts = avertissements = 0


def titre(t):
    print(f"\n{GRAS}{t}{FIN}")


def ok(m):
    print(f"  {VERT}v{FIN} {m}")


def erreur(m):
    global defauts
    defauts += 1
    print(f"  {ROUGE}x{FIN} {m}")


def avert(m):
    global avertissements
    avertissements += 1
    print(f"  {JAUNE}!{FIN} {m}")


def url_de(fichier: Path) -> str:
    rel = fichier.relative_to(OUT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel[: -len(".html")]


PAGES = {url_de(f): f for f in sorted(OUT.rglob("*.html"))}
TEXTES = {u: f.read_text(encoding="utf-8") for u, f in PAGES.items()}
BASE = ""
m = re.search(r'<link rel="canonical" href="(https?://[^/]+)', TEXTES.get("/", ""))
if m:
    BASE = m.group(1)


def existe(chemin: str) -> bool:
    return chemin in PAGES or chemin.rstrip("/") in PAGES


# --- 1. Redirections --------------------------------------------------------
titre("1. Redirections 301")
regles = {}
if HTACCESS.is_file():
    for motif, cible in re.findall(
            r'^RewriteRule\s+\^([a-z0-9/-]+)/\?\$\s+(/\S*)\s+\[R=301', HTACCESS.read_text(), re.M):
        regles["/" + motif] = cible

for src, cible in regles.items():
    if src == cible:
        erreur(f"{src} redirige vers lui-même — boucle infinie, page inaccessible")
    elif cible in regles:
        erreur(f"chaîne de redirections : {src} → {cible} → {regles[cible]}")
    elif not existe(cible):
        erreur(f"{src} redirige vers {cible}, qui n'existe pas")
    if existe(src):
        erreur(f"{src} est à la fois une page et une redirection")
if not defauts:
    ok(f"{len(regles)} redirections : aucune boucle, aucune chaîne, toutes vers une page réelle")

# --- 2 et 3. Maillage interne : pages orphelines et profondeur --------------
titre("2. Maillage interne")
liens = {}
for u, t in TEXTES.items():
    corps = t.split('<main id="contenu">')[-1]
    cibles = set()
    for href in re.findall(r'href="(/[^"#?]*)"', corps):
        href = href if href == "/" else href.rstrip("/")
        if href in PAGES:
            cibles.add(href)
        elif href + "/" in PAGES:
            cibles.add(href + "/")
    liens[u] = cibles

entrants = {u: 0 for u in PAGES}
for u, cibles in liens.items():
    for c in cibles:
        if c != u:
            entrants[c] += 1

orphelines = [u for u, n in entrants.items() if n == 0 and u not in HORS_INDEX and u != "/"]
if orphelines:
    for u in orphelines:
        erreur(f"page orpheline, aucun lien interne n'y mène : {u}")
else:
    ok(f"Les {len(PAGES)} pages reçoivent au moins un lien interne")

profondeur = {"/": 0}
file = deque(["/"])
while file:
    u = file.popleft()
    for c in liens.get(u, ()):
        if c not in profondeur:
            profondeur[c] = profondeur[u] + 1
            file.append(c)

inatteignables = [u for u in PAGES if u not in profondeur and u not in HORS_INDEX]
for u in inatteignables:
    erreur(f"page inatteignable depuis l'accueil : {u}")
profondes = [(u, p) for u, p in profondeur.items() if p > 3]
if profondes:
    for u, p in sorted(profondes, key=lambda x: -x[1])[:8]:
        avert(f"{u} est à {p} clics de l'accueil")
else:
    maxi = max(profondeur.values())
    ok(f"Toutes les pages sont à {maxi} clics ou moins de l'accueil")

faibles = sorted((n, u) for u, n in entrants.items() if n < 3 and u != "/" and u not in HORS_INDEX)
if faibles:
    avert(f"{len(faibles)} page(s) reçoivent moins de 3 liens internes "
          f"(la plus isolée : {faibles[0][1]}, {faibles[0][0]})")
else:
    ok("Chaque page reçoit au moins 3 liens internes")

# --- 4. Canoniques ----------------------------------------------------------
titre("3. Adresses canoniques")
canoniques = {}
pb = False
for u, t in TEXTES.items():
    m = re.search(r'<link rel="canonical" href="([^"]+)"', t)
    if not m:
        erreur(f"aucune adresse canonique : {u}")
        pb = True
        continue
    attendue = BASE + u
    if m.group(1) != attendue:
        erreur(f"{u} se déclare canonique sur {m.group(1)}")
        pb = True
    canoniques.setdefault(m.group(1), []).append(u)
for c, us in canoniques.items():
    if len(us) > 1:
        erreur(f"{len(us)} pages revendiquent la même adresse canonique {c} : {', '.join(us)}")
        pb = True
if not pb:
    ok(f"Les {len(TEXTES)} pages se désignent elles-mêmes, sans doublon")

# --- 5. Sitemap -------------------------------------------------------------
titre("4. Sitemap et directives robots")
sitemap = set(re.findall(r"<loc>(.*?)</loc>", (OUT / "sitemap.xml").read_text()))
chemins_sitemap = {u[len(BASE):] for u in sitemap if u.startswith(BASE)}
noindex = {u for u, t in TEXTES.items() if re.search(r'name="robots" content="noindex', t)}

manquantes = sorted(set(PAGES) - chemins_sitemap - noindex - HORS_INDEX)
for u in manquantes:
    erreur(f"page indexable absente du sitemap : {u}")
en_trop = sorted(chemins_sitemap - set(PAGES))
for u in en_trop:
    erreur(f"URL au sitemap sans page correspondante : {u}")
contradictoires = sorted(chemins_sitemap & noindex)
for u in contradictoires:
    erreur(f"page en noindex déclarée au sitemap : {u}")
if not (manquantes or en_trop or contradictoires):
    ok(f"{len(chemins_sitemap)} URLs au sitemap, {len(noindex)} page(s) en noindex assumées "
       f"({', '.join(sorted(noindex))})")

# --- 6. Domaine -------------------------------------------------------------
titre("5. Domaine déclaré")
print(f"      Les adresses canoniques et le sitemap désignent {GRAS}{BASE}{FIN}.")
print("      Une page servie depuis un AUTRE domaine — un sous-domaine de")
print("      prévisualisation, par exemple — désigne donc une adresse qui n'est")
print("      pas la sienne, et aucun moteur ne l'indexera. C'est voulu tant que")
print("      le site est en préparation ; à l'ouverture, DOMAINE doit être celui")
print("      sur lequel le site répond vraiment (src/config.sh).")

print(f"\n{GRAS}Bilan{FIN}")
print(f"  {len(PAGES)} pages analysées")
if defauts:
    print(f"  {ROUGE}{defauts} défaut(s) d'indexation{FIN}")
else:
    print(f"  {VERT}Aucun défaut d'indexation.{FIN}")
if avertissements:
    print(f"  {JAUNE}{avertissements} avertissement(s){FIN}")
sys.exit(1 if defauts else 0)
