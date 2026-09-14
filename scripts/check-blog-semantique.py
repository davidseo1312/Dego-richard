#!/usr/bin/env python3
"""
Couverture sémantique de TOUS les articles du blog.

    python3 scripts/check-blog-semantique.py

Chaque article est mesuré sur son propre champ lexical, déclaré dans
src/seo/champs-lexicaux.tsv : le champ commun — la zone d'intervention et le
vocabulaire du métier — plus les notions propres à son sujet.

Ce que le script vérifie, article par article :

  * COUVERTURE ≥ 90 % des termes attendus ;
  * PLACEMENT — part des termes employés dans un titre, un intertitre, une
    question de FAQ ou une mise en évidence, là où ils pèsent ;
  * aucun terme au-delà de 1,5 % des mots, seuil du bourrage — à l'exception
    des termes du H1, qui sont le SUJET de l'article : reprocher à « Dégorgement
    ou curage » de répéter « curage » reviendrait à lui reprocher de traiter sa
    question. Le bourrage, c'est un mot martelé qui n'est pas le sujet ;
  * un appel à l'action final qui invite explicitement à téléphoner.

Le dernier point n'est pas cosmétique : un article de conseils qui ne mène
nulle part est du contenu perdu. Le contrôle exige un bloc .cta-final
contenant un lien tel: vers le numéro de l'entreprise.

Rend 1 si un article échoue, 0 sinon.
"""

import importlib.util
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CHAMPS = RACINE / "src" / "seo" / "champs-lexicaux.tsv"
BLOG = RACINE / "public" / "blog"

sp = importlib.util.spec_from_file_location("cs", RACINE / "scripts" / "check-semantique.py")
cs = importlib.util.module_from_spec(sp)
sp.loader.exec_module(cs)

VERT, ROUGE, JAUNE, GRAS, FIN = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"


def champs() -> dict:
    communs, propres = [], {}
    for ligne in CHAMPS.read_text(encoding="utf-8").splitlines():
        if not ligne.strip() or ligne.lstrip().startswith("#"):
            continue
        slug, _, terme = ligne.partition("\t")
        terme = terme.strip()
        if not terme:
            continue
        if slug == "*":
            communs.append(terme)
        else:
            propres.setdefault(slug, []).append(terme)
    return communs, propres


def appel_final(corps: str) -> bool:
    """Un appel à l'action final, avec un lien vers le téléphone."""
    m = re.search(r'<section class="cta-final">(.*?)</section>', corps, re.S)
    return bool(m and 'href="tel:' in m.group(1))


def main() -> int:
    communs, propres = champs()
    echecs = []

    print(f"\n{GRAS}Couverture sémantique des articles du blog{FIN}")
    print(f"  {len(propres)} articles, champ commun de {len(communs)} termes\n")
    print(f"  {'article':44} {'couv.':>6} {'plac.':>6} {'max/terme':>10}  CTA")
    print("  " + "-" * 76)

    for slug in sorted(propres):
        f = BLOG / f"{slug}.html"
        if not f.is_file():
            echecs.append(f"{slug} : page absente")
            continue
        html = f.read_text(encoding="utf-8")
        corps = cs.corps(html)
        h1 = cs.sans_accent(cs.texte_nu(
            re.search(r"<h1[^>]*>(.*?)</h1>", corps, re.S).group(1)))
        texte = cs.sans_accent(cs.texte_nu(corps)).replace("’", "'")
        fort = cs.sans_accent(cs.zones_fortes(corps)).replace("’", "'")
        nb = len(texte.split())

        termes = communs + propres[slug]
        presents = places = 0
        pire = (0.0, "—")
        manquants = []
        for t in termes:
            formes = cs.variantes(t)
            occ = sum(len(re.findall(r"\b" + re.escape(x) + r"\b", texte)) for x in formes)
            if occ:
                presents += 1
                if any(re.search(r"\b" + re.escape(x) + r"\b", fort) for x in formes):
                    places += 1
                d = 100 * occ / nb
                sujet = any(x in h1 for x in formes)
                if d > pire[0] and not sujet:
                    pire = (d, t)
            else:
                manquants.append(t)

        couv = 100 * presents / len(termes)
        plac = 100 * places / len(termes)
        cta = appel_final(corps)

        souci = couv < 90 or pire[0] > 1.5 or not cta
        marque = f"{ROUGE}x{FIN}" if souci else f"{VERT}v{FIN}"
        print(f"  {marque} {slug:42} {couv:5.1f}% {plac:5.1f}% {pire[0]:9.2f}%  "
              f"{'oui' if cta else ROUGE + 'NON' + FIN}")
        if manquants:
            print(f"      {JAUNE}absents :{FIN} {', '.join(manquants)}")
        if pire[0] > 1.5:
            print(f"      {JAUNE}sur-représenté :{FIN} {pire[1]} ({pire[0]:.2f} %)")
        if souci:
            echecs.append(slug)

    print()
    if echecs:
        print(f"  {ROUGE}{len(echecs)} article(s) sous l'objectif.{FIN}")
        return 1
    print(f"  {VERT}Tous les articles : couverture ≥ 90 %, aucun bourrage, "
          f"appel à l'action téléphonique présent.{FIN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
