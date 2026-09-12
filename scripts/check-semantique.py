#!/usr/bin/env python3
"""
Couverture sémantique d'une page, et garde-fou contre le bourrage.

    python3 scripts/check-semantique.py public/blog/ma-page.html mots-cles.txt

Ce que le script mesure, et pourquoi
------------------------------------
Les outils d'optimisation sémantique — 1.fr et ses équivalents — notent une
page sur deux choses : COMBIEN de termes du champ lexical attendu elle
emploie, et OÙ elle les emploie. Un terme cité une fois au fond d'une liste ne
vaut pas un terme qui structure un paragraphe.

Le script rend donc trois chiffres :

  1. COUVERTURE — part des termes attendus réellement présents dans le texte
     rendu, accents et pluriels compris. C'est la note qui compte.
  2. PLACEMENT — part des termes présents dans un titre, un intertitre, un
     résumé ou une question de FAQ, c'est-à-dire là où ils pèsent.
  3. DENSITÉ DU CHAMP — part des mots du texte qui appartiennent au champ
     visé. Elle se calcule sur les EMPLACEMENTS distincts, pas sur la somme
     des occurrences par terme : « assurance multirisque habitation » contient
     « assurance multirisque » et « assurance habitation », et les compter
     trois fois ferait passer pour du bourrage une seule tournure correcte.

     Cette valeur est INFORMATIVE. Un article qui traite réellement d'un sujet
     emploie le vocabulaire de ce sujet : 5 à 8 % sur un champ de trente
     termes est le signe qu'il parle bien de ce dont il prétend parler, pas
     qu'il triche.

  4. DENSITÉ PAR TERME — c'est ELLE qui trahit le bourrage. Un même mot
     répété au-delà de 1,5 % des mots de la page ne sert plus le lecteur.
     Le seuil porte sur chaque terme pris isolément, jamais sur leur somme :
     confondre les deux revient à reprocher à un texte d'être sur son sujet.

Un terme n'est compté que dans le CORPS de la page : en-tête et pied de page
sont communs aux 112 pages et gonfleraient la note sans rien apporter.
"""

import re
import sys
import unicodedata
from pathlib import Path


def sans_accent(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")


def variantes(terme: str) -> list:
    """Les formes sous lesquelles un terme peut réellement apparaître.

    « fuite d'eau » se rencontre aussi en « fuites d'eau » ; « plombier » en
    « plombiers ». Les apostrophes droites et typographiques sont ramenées à
    la même forme, faute de quoi « contrat d'assurance » ne serait jamais
    trouvé dans un texte correctement composé.
    """
    base = sans_accent(terme).replace("’", "'")
    formes = {base}
    mots = base.split()
    # Pluriel ou singulier du premier mot, qui porte le nombre en français.
    if mots:
        tete = mots[0]
        formes.add(" ".join([tete + "s"] + mots[1:]))
        if tete.endswith("s"):
            formes.add(" ".join([tete[:-1]] + mots[1:]))
        if tete.endswith("x"):
            formes.add(" ".join([tete[:-1]] + mots[1:]))
    # « d'eau » ou « de l'eau », « d'assurance » ou « de l'assurance ».
    formes |= {f.replace(" d'", " de l'") for f in list(formes)}
    return sorted(formes)


def corps(html: str) -> str:
    """Le contenu propre à la page, sans l'en-tête ni le pied commun."""
    t = html.split('<main id="contenu">')[-1].split("</main>")[0]
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    return t


def texte_nu(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def zones_fortes(html: str) -> str:
    """Titres, intertitres, résumé, questions de FAQ, texte mis en évidence."""
    morceaux = re.findall(
        r"<(h1|h2|h3|summary|strong)[^>]*>(.*?)</\1>", html, re.S | re.I)
    return texte_nu(" ".join(m[1] for m in morceaux))


def main(chemin: str, fichier_mots: str) -> int:
    html = Path(chemin).read_text(encoding="utf-8")
    c = corps(html)
    texte = sans_accent(texte_nu(c)).replace("’", "'")
    fort = sans_accent(zones_fortes(c)).replace("’", "'")
    nb_mots = len(texte.split())

    termes = [l.strip() for l in Path(fichier_mots).read_text(encoding="utf-8").splitlines()
              if l.strip()]

    presents, absents, places = [], [], []
    spans = []          # emplacements couverts, pour une densité non gonflée
    for terme in termes:
        formes = variantes(terme)
        occ = 0
        for f in formes:
            for m in re.finditer(r"\b" + re.escape(f) + r"\b", texte):
                occ += 1
                spans.append(m.span())
        if occ:
            presents.append((terme, occ))
            if any(re.search(r"\b" + re.escape(f) + r"\b", fort) for f in formes):
                places.append(terme)
        else:
            absents.append(terme)

    # Fusion des emplacements qui se recouvrent.
    fusion, mots_couverts = [], 0
    for d, f in sorted(spans):
        if fusion and d <= fusion[-1][1]:
            fusion[-1] = (fusion[-1][0], max(fusion[-1][1], f))
        else:
            fusion.append((d, f))
    for d, f in fusion:
        mots_couverts += len(texte[d:f].split())

    couverture = 100 * len(presents) / len(termes)
    placement = 100 * len(places) / len(termes)
    densite = 100 * mots_couverts / nb_mots if nb_mots else 0

    print(f"\n\033[1m{chemin}\033[0m — {nb_mots} mots dans le corps\n")
    print(f"  COUVERTURE  {couverture:5.1f} %   ({len(presents)}/{len(termes)} termes présents)")
    print(f"  PLACEMENT   {placement:5.1f} %   ({len(places)} en titre, intertitre ou mise en évidence)")
    print(f"  DENSITÉ     {densite:5.2f} %   ({mots_couverts} mots du champ sur {nb_mots}, "
          f"{len(fusion)} emplacements)")

    if absents:
        print(f"\n  \033[33mAbsents ({len(absents)})\033[0m")
        for t in absents:
            print(f"      {t}")

    pire = max(((100 * o / nb_mots, t) for t, o in presents), default=(0, "—"))
    print(f"  PAR TERME   {pire[0]:5.2f} %   (le plus répété : {pire[1]})")

    trop = [(t, o) for t, o in presents if 100 * o / nb_mots > 1.5]
    if trop:
        print(f"\n  \033[33mBourrage — termes au-delà de 1,5 % des mots\033[0m")
        for t, o in sorted(trop, key=lambda x: -x[1]):
            print(f"      {t} : {o} occurrences ({100 * o / nb_mots:.2f} %)")

    defaut = couverture < 90 or bool(trop)
    print()
    if defaut:
        print("  \033[31mObjectif non atteint : couverture ≥ 90 %, aucun terme au-delà de 1,5 %.\033[0m")
    else:
        print("  \033[32mCouverture ≥ 90 %, aucun terme sur-représenté.\033[0m")
    return 1 if defaut else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
