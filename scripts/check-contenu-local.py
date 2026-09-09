#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Contrôle de similarité des pages locales.
#
#   python3 scripts/check-contenu-local.py
#
# Pourquoi ce script existe
# -------------------------
# La tentation, sur un site de dépannage, est d'écrire une page type et d'y
# substituer le nom de la commune. Google appelle cela du « contenu peu
# informatif à grande échelle » : les pages ne se positionnent pas, et le
# domaine entier finit par en souffrir. Ce contrôle mesure objectivement à
# quel point deux pages locales se ressemblent, avant publication.
#
# Méthode : similarité de Jaccard sur les 5-grammes de mots du contenu
# éditorial (ce qui est entre <main> et </main>, en-tête et pied de page
# exclus puisqu'ils sont identiques partout, par construction).
#
#   >= SEUIL_BLOQUANT   : les deux pages sont des quasi-doublons -> échec.
#   >= SEUIL_AVERT      : ressemblance forte -> avertissement à traiter.
#
# Sortie 1 si au moins un couple dépasse le seuil bloquant.
# ---------------------------------------------------------------------------

import re
import sys
from itertools import combinations
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"

SEUIL_BLOQUANT = 0.60
SEUIL_AVERT = 0.42
TAILLE_NGRAMME = 5

# Longueur minimale attendue d'une page locale. En dessous, la page n'apporte
# rien qu'une section de la page départementale ne dirait mieux.
MOTS_MINIMUM = 380


def est_page_locale(chemin: Path) -> bool:
    rel = chemin.relative_to(PUBLIC).as_posix()
    if rel.startswith("departements/"):
        return True
    # Les pages communales s'appellent toutes degorgement-<commune>.html.
    # Trois pages de service partagent ce préfixe sans être locales.
    return rel.startswith("degorgement-") and rel not in {
        "degorgement-urgence.html",
        "degorgement-professionnel.html",
        "degorgement-collectif.html",
    }


def texte_editorial(chemin: Path) -> str:
    html = chemin.read_text(encoding="utf-8")

    # Seul le contenu propre à la page est comparé : l'en-tête et le pied de
    # page sont les mêmes partout et gonfleraient artificiellement le score.
    entre_main = re.search(r'<main id="contenu">(.*)</main>', html, re.S)
    if entre_main:
        html = entre_main.group(1)

    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", html)
    return re.sub(r"\s+", " ", html).strip().lower()


def ngrammes(texte: str) -> set:
    mots = re.findall(r"[a-zàâäçéèêëîïôöùûüÿœ0-9]+", texte)
    if len(mots) < TAILLE_NGRAMME:
        return set()
    return {
        " ".join(mots[i:i + TAILLE_NGRAMME])
        for i in range(len(mots) - TAILLE_NGRAMME + 1)
    }


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main() -> int:
    if not PUBLIC.is_dir():
        sys.exit("public/ absent — lancez d'abord : bash scripts/build.sh")

    pages = sorted(p for p in PUBLIC.rglob("*.html") if est_page_locale(p))
    if not pages:
        print("Aucune page locale trouvée.")
        return 0

    profils = {}
    courtes = []
    for page in pages:
        texte = texte_editorial(page)
        nb_mots = len(re.findall(r"[a-zàâäçéèêëîïôöùûüÿœ0-9]+", texte))
        if nb_mots < MOTS_MINIMUM:
            courtes.append((page.relative_to(PUBLIC).as_posix(), nb_mots))
        profils[page] = ngrammes(texte)

    bloquants, avertissements = [], []
    for a, b in combinations(pages, 2):
        score = jaccard(profils[a], profils[b])
        couple = (
            a.relative_to(PUBLIC).as_posix(),
            b.relative_to(PUBLIC).as_posix(),
            score,
        )
        if score >= SEUIL_BLOQUANT:
            bloquants.append(couple)
        elif score >= SEUIL_AVERT:
            avertissements.append(couple)

    print(f"Contenu local : {len(pages)} pages comparées "
          f"({len(pages) * (len(pages) - 1) // 2} couples).")

    if courtes:
        print(f"\n{len(courtes)} page(s) sous {MOTS_MINIMUM} mots de contenu propre :")
        for nom, n in sorted(courtes, key=lambda c: c[1]):
            print(f"  ! {nom} — {n} mots")
        print("    -> une page locale trop courte ne justifie pas son existence :")
        print("       enrichissez-la, ou traitez la commune dans la page du département.")

    if avertissements:
        print(f"\n{len(avertissements)} couple(s) au-dessus de {SEUIL_AVERT:.0%} de similarité :")
        for a, b, s in sorted(avertissements, key=lambda c: -c[2]):
            print(f"  ! {s:.0%}  {a}  <->  {b}")
        print("    -> différenciez le contexte local, les problématiques traitées")
        print("       et la FAQ. Une reformulation ne suffit pas.")

    if bloquants:
        print(f"\n{len(bloquants)} couple(s) au-dessus de {SEUIL_BLOQUANT:.0%} — quasi-doublons :")
        for a, b, s in sorted(bloquants, key=lambda c: -c[2]):
            print(f"  x {s:.0%}  {a}  <->  {b}")
        print("\nCONTENU LOCAL : ECHEC — ces pages ne doivent pas etre publiees en l'etat.")
        return 1

    if not avertissements and not courtes:
        print("\nCONTENU LOCAL : OK — aucune page locale n'en duplique une autre.")
    else:
        print("\nCONTENU LOCAL : aucun quasi-doublon bloquant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
