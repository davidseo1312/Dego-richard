#!/usr/bin/env python3
"""
Relie les articles de conseils aux pages de prestation qui les concernent.

    python3 scripts/maillage-conseils.py

Pourquoi
--------
Les douze articles du blog n'étaient atteignables que depuis le sommaire du
blog et, pour certains, depuis un autre article. Une page qui ne reçoit qu'un
lien interne est explorée rarement et classée comme secondaire : le travail
d'écriture est fait, mais il ne sert pas.

Chaque page de prestation reçoit donc un bloc « À lire aussi » listant les
articles qui traitent VRAIMENT de son sujet. Pas une liste automatique de
tous les articles : un lien qui ne correspond à rien n'aide ni le visiteur,
ni le référencement.

Le bloc s'insère avant l'appel à l'action final. Idempotent.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "src" / "pages"

TITRES = {
    "canalisation-bouchee-que-faire": "Que faire face à une canalisation bouchée ?",
    "canalisation-bouchee-signes": "Les signes qui annoncent un bouchon",
    "comment-entretenir-canalisations": "Comment entretenir ses canalisations",
    "degorgement-ou-curage": "Dégorgement ou curage : lequel choisir ?",
    "depannage-urgence-vos-droits": "Dépannage en urgence : vos droits, les prix, les pièges",
    "eau-remonte-evier": "L'eau remonte dans l'évier : pourquoi ?",
    "entretenir-assainissement-non-collectif": "Entretenir un assainissement non collectif",
    "eviter-bouchons-canalisation": "Éviter les bouchons de canalisation",
    "pourquoi-canalisation-se-bouche": "Pourquoi une canalisation se bouche",
    "prix-degorgement": "Le prix d'un dégorgement, poste par poste",
    "quand-utiliser-camera-inspection": "Quand l'inspection caméra est utile",
    "residence-secondaire-reouverture": "Rouvrir une résidence secondaire",
    "wc-bouche-que-faire": "WC bouché : ce qu'il faut faire, et ne pas faire",
}

# Quelle prestation renvoie vers quels articles. Le rapprochement est fait
# sujet par sujet : c'est ce qui distingue un maillage utile d'un pied de page
# rempli de liens.
LIENS = {
    "degorgement": ["prix-degorgement", "degorgement-ou-curage", "residence-secondaire-reouverture"],
    "degorgement-urgence": ["canalisation-bouchee-que-faire", "canalisation-bouchee-signes", "depannage-urgence-vos-droits"],
    "debouchage-canalisation": ["canalisation-bouchee-que-faire", "pourquoi-canalisation-se-bouche",
                                "eviter-bouchons-canalisation", "depannage-urgence-vos-droits"],
    "debouchage-canalisation-exterieure": ["pourquoi-canalisation-se-bouche",
                                           "quand-utiliser-camera-inspection"],
    "debouchage-wc": ["wc-bouche-que-faire", "eviter-bouchons-canalisation"],
    "debouchage-toilettes": ["wc-bouche-que-faire"],
    "debouchage-evier": ["eau-remonte-evier", "comment-entretenir-canalisations"],
    "debouchage-lavabo": ["eau-remonte-evier", "eviter-bouchons-canalisation"],
    "debouchage-cuisine": ["comment-entretenir-canalisations", "eau-remonte-evier"],
    "debouchage-douche": ["eviter-bouchons-canalisation"],
    "debouchage-baignoire": ["canalisation-bouchee-signes"],
    "curage-canalisation": ["degorgement-ou-curage", "pourquoi-canalisation-se-bouche"],
    "inspection-camera-canalisation": ["quand-utiliser-camera-inspection"],
    "recherche-bouchon": ["canalisation-bouchee-signes", "quand-utiliser-camera-inspection"],
    "entretien-canalisation": ["comment-entretenir-canalisations", "eviter-bouchons-canalisation",
                               "canalisation-bouchee-signes"],
    "pompage": ["entretenir-assainissement-non-collectif"],
    "assainissement": ["entretenir-assainissement-non-collectif", "residence-secondaire-reouverture"],
    "degorgement-professionnel": ["comment-entretenir-canalisations", "degorgement-ou-curage"],
    "degorgement-collectif": ["eviter-bouchons-canalisation", "pourquoi-canalisation-se-bouche"],
    "tarifs": ["prix-degorgement", "degorgement-ou-curage", "depannage-urgence-vos-droits"],
    "devis": ["prix-degorgement", "depannage-urgence-vos-droits"],
    "faq": ["prix-degorgement", "canalisation-bouchee-que-faire", "wc-bouche-que-faire"],
}

MARQUE = '<!-- maillage-conseils -->'


def bloc(articles) -> str:
    items = "\n".join(
        f'      <li><a href="/blog/{a}">{TITRES[a]}</a></li>' for a in articles)
    return f'''{MARQUE}
<section class="alt">
  <div class="wrap">
    <div class="liens-connexes">
      <h2>À lire aussi</h2>
      <ul>
{items}
        <li><a href="/blog/">Tous nos conseils canalisations</a></li>
      </ul>
    </div>
  </div>
</section>

'''


def traiter(slug: str, articles) -> str | None:
    f = PAGES / f"{slug}.html"
    if not f.is_file():
        return f"{slug} : page introuvable"
    s = f.read_text(encoding="utf-8")

    # Un bloc déjà posé est REMPLACÉ, pas laissé tel quel : sans cela, un
    # article ajouté au blog après coup ne serait jamais relié aux pages déjà
    # traitées, et le script mentirait sur ce qu'il garantit.
    if MARQUE in s:
        debut = s.index(MARQUE)
        fin = s.index("</section>", debut) + len("</section>\n\n")
        avant = s[debut:fin]
        neuf = bloc(articles)
        if avant == neuf:
            return None
        f.write_text(s[:debut] + neuf + s[fin:], encoding="utf-8")
        return f"{slug} → bloc mis à jour, {len(articles)} article(s)"

    i = s.rfind('<section class="cta-final">')
    if i == -1:
        return f"{slug} : pas d'appel à l'action final, bloc non posé"
    f.write_text(s[:i] + bloc(articles) + s[i:], encoding="utf-8")
    return f"{slug} → {len(articles)} article(s)"


if __name__ == "__main__":
    faits = [r for slug, a in LIENS.items() if (r := traiter(slug, a))]
    print(f"{len(faits)} page(s) traitée(s)")
    for r in faits:
        print("   ✓", r)
    sys.exit(0)
