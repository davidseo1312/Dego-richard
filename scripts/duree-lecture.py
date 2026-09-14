#!/usr/bin/env python3
"""
Recalcule la durée de lecture affichée par chaque article du blog.

    python3 scripts/duree-lecture.py

Elle est écrite à deux endroits — l'étiquette de l'article et sa carte dans le
sommaire du blog — et elle était tenue à la main. Une durée maintenue à la
main devient fausse au premier paragraphe ajouté, et elle l'était : des
articles annonçaient six minutes après avoir doublé de longueur.

Le calcul se fait sur le texte RENDU, donc après construction, à 200 mots par
minute — le rythme de lecture courante d'un adulte sur un texte de prose
française. Le site employait auparavant un rythme deux fois plus lent, qui
gonflait chaque durée.

Le script met à jour les deux endroits d'un coup. Idempotent.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "src" / "pages" / "blog"
OUT = RACINE / "public" / "blog"
MOTS_PAR_MINUTE = 200


def duree(slug: str) -> int:
    rendu = OUT / f"{slug}.html"
    corps = rendu.read_text(encoding="utf-8").split('<main id="contenu">')[-1]
    mots = len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corps)).split())
    return max(3, round(mots / MOTS_PAR_MINUTE))


def main() -> int:
    if not OUT.is_dir():
        print("Construisez d'abord le site : bash scripts/build.sh", file=sys.stderr)
        return 1

    index = SRC / "index.html"
    texte_index = index.read_text(encoding="utf-8")
    faits = []

    for f in sorted(SRC.glob("*.html")):
        if f.name == "index.html":
            continue
        slug = f.stem
        m = duree(slug)
        s = f.read_text(encoding="utf-8")
        avant = s

        s = re.sub(r'(<span class="duree">Lecture )\d+( min</span>)',
                   lambda x: f"{x.group(1)}{m}{x.group(2)}", s, count=1)
        s = re.sub(r'(<p class="article-meta">[^<]*?· Lecture )\d+( minutes?</p>)',
                   lambda x: f"{x.group(1)}{m}{x.group(2)}", s, count=1)
        if s != avant:
            f.write_text(s, encoding="utf-8")

        # La carte du sommaire du blog porte la même durée.
        motif = (r'(<a href="/blog/' + re.escape(slug) +
                 r'"[^>]*>.*?<span class="duree">Lecture )\d+( min</span>)')
        texte_index = re.sub(motif, lambda x: f"{x.group(1)}{m}{x.group(2)}",
                             texte_index, count=1, flags=re.S)
        faits.append((slug, m))

    index.write_text(texte_index, encoding="utf-8")
    print(f"{len(faits)} article(s) — durées recalculées à {MOTS_PAR_MINUTE} mots/minute")
    for slug, m in faits:
        print(f"   ✓ {slug} — {m} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
