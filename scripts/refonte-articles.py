#!/usr/bin/env python3
"""
Applique le nouveau gabarit aux articles du blog.

    python3 scripts/refonte-articles.py

Un article passe d'un simple H1 posé en haut de colonne à :
    bande de héros (fil d'Ariane, catégorie, durée de lecture, H1, date)
  + grande image d'introduction
  + sommaire construit à partir des H2 réellement présents

Le sommaire est généré depuis le document, jamais saisi à la main : il ne
peut donc pas mentir sur le contenu, et suivre un lien ancre toujours sur
une section qui existe. Les identifiants d'ancre sont ajoutés aux H2 au
passage.

Aucun texte d'article n'est modifié. Idempotent.
"""

import re
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BLOG = RACINE / "src" / "pages" / "blog"

VISUEL = {
    "canalisation-bouchee-que-faire": "debouchage-canalisation",
    "canalisation-bouchee-signes": "inspection-camera-canalisation",
    "comment-entretenir-canalisations": "curage-canalisation",
    "degorgement-ou-curage": "curage-canalisation",
    "eau-remonte-evier": "debouchage-evier",
    "entretenir-assainissement-non-collectif": "assainissement",
    "eviter-bouchons-canalisation": "debouchage-cuisine",
    "pourquoi-canalisation-se-bouche": "canalisation-exterieure",
    "prix-degorgement": "materiel-degorgement",
    "quand-utiliser-camera-inspection": "inspection-camera-canalisation",
    "residence-secondaire-reouverture": "pompage-canalisation",
    "wc-bouche-que-faire": "debouchage-wc",
}

CATEGORIE = {
    "canalisation-bouchee-que-faire": "Urgence",
    "canalisation-bouchee-signes": "Diagnostic",
    "comment-entretenir-canalisations": "Entretien",
    "degorgement-ou-curage": "Comprendre",
    "eau-remonte-evier": "Diagnostic",
    "entretenir-assainissement-non-collectif": "Assainissement",
    "eviter-bouchons-canalisation": "Entretien",
    "pourquoi-canalisation-se-bouche": "Comprendre",
    "prix-degorgement": "Tarifs",
    "quand-utiliser-camera-inspection": "Diagnostic",
    "residence-secondaire-reouverture": "Entretien",
    "wc-bouche-que-faire": "Urgence",
}

DIMENSIONS = {
    "hero-debouchage-canalisation": (1120, 840), "materiel-degorgement": (960, 720),
    "debouchage-wc": (960, 720), "debouchage-evier": (960, 720),
    "debouchage-douche": (960, 720), "debouchage-baignoire": (960, 720),
    "debouchage-cuisine": (960, 720), "debouchage-canalisation": (1120, 700),
    "inspection-camera-canalisation": (1120, 700), "curage-canalisation": (1120, 700),
    "pompage-canalisation": (960, 720), "assainissement": (1120, 700),
    "debouchage-professionnel": (960, 720), "canalisation-exterieure": (960, 720),
    "urgence-degorgement": (1120, 700),
}

ALT = {
    "hero-debouchage-canalisation":
        "Coupe d'un réseau d'assainissement domestique : canalisation enterrée reliant la "
        "maison au regard de visite, buse d'hydrocurage en action sur un bouchon",
    "materiel-degorgement":
        "Matériel professionnel de dégorgement : enrouleur haute pression, flexible et "
        "caméra d'inspection de canalisation",
    "debouchage-wc":
        "Coupe d'un WC montrant la garde d'eau du siphon et l'emplacement d'un bouchon",
    "debouchage-evier":
        "Coupe d'un évier et de son siphon en S obstrué par des graisses figées",
    "debouchage-douche":
        "Coupe d'un receveur de douche dont la bonde siphoïde est obstruée par des cheveux",
    "debouchage-baignoire":
        "Coupe d'une baignoire remplie d'eau stagnante et de son siphon de vidage",
    "debouchage-cuisine":
        "Coupe d'une installation de cuisine : évier, siphon et bac à graisses raccordés au réseau",
    "debouchage-canalisation":
        "Coupe d'une canalisation enterrée obstruée, buse rotative haute pression progressant "
        "vers le bouchon",
    "inspection-camera-canalisation":
        "Vue depuis l'intérieur d'une canalisation inspectée par caméra motorisée, paroi "
        "éclairée et lame d'eau au radier",
    "curage-canalisation":
        "Vue depuis l'intérieur d'une canalisation en cours de curage haute pression, dépôt "
        "décollé de la paroi",
    "pompage-canalisation":
        "Coupe d'un regard de visite rempli, flexible d'aspiration plongé jusqu'au fond pour "
        "le pompage",
    "assainissement":
        "Coupe d'une installation d'assainissement individuel : maison, fosse toutes eaux à "
        "deux compartiments, ventilation et départ vers l'épandage",
    "canalisation-exterieure":
        "Coupe d'une canalisation extérieure enterrée traversée par des racines d'arbre, avec "
        "son regard de visite",
}


def ancre(titre: str) -> str:
    """Identifiant d'ancre lisible, dérivé du titre affiché."""
    t = re.sub(r"<[^>]+>", "", titre)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:60] or "section"


def convertir(chemin: Path) -> bool:
    nom = chemin.stem
    texte = chemin.read_text(encoding="utf-8")
    if 'class="hero hero-article"' in texte:
        return False

    m_fil = re.search(r'<div class="wrap fil">\s*\n(?P<nav>.*?)\n</div>\n', texte, re.S)
    m_ouv = re.search(
        r'<section>\n  <div class="wrap article">\n'
        r'    <h1>(?P<h1>.*?)</h1>\n'
        r'    <p class="article-meta">(?P<meta>.*?)</p>\n', texte, re.S)
    if not m_fil or not m_ouv:
        return False

    visuel = VISUEL.get(nom, "hero-debouchage-canalisation")
    l, h = DIMENSIONS[visuel]
    meta = m_ouv.group("meta").strip()

    # La durée de lecture est déjà écrite dans la ligne de méta : on la reprend
    # telle quelle plutôt que d'en recalculer une qui la contredirait.
    m_duree = re.search(r'Lecture\s+(\d+)\s*minutes?', meta)
    duree = f'<span class="duree">Lecture {m_duree.group(1)} min</span>' if m_duree else ""

    nav = re.sub(r'^\s{2}', '      ', m_fil.group("nav"), flags=re.M)

    hero = f'''<section class="hero hero-interieur hero-article">
  <div class="wrap">
    <div class="fil">
{nav}
    </div>

    <div class="article-entete">
      <p class="carte-etiquettes">
        <span>{CATEGORIE.get(nom, "Conseils")}</span>{duree}
      </p>
      <h1>{m_ouv.group("h1").strip()}</h1>
      <p class="article-meta">{meta}</p>
    </div>

    <figure class="article-visuel">
      <img src="/assets/img/photos/{visuel}.webp"
           width="{l}" height="{h}" fetchpriority="high" decoding="async"
           alt="{ALT[visuel]}">
    </figure>
  </div>
</section>

<section>
  <div class="wrap article">
'''

    texte = texte.replace(m_ouv.group(0), hero, 1)
    texte = texte.replace(m_fil.group(0), "", 1)

    # Ancres sur les H2 de l'article — et uniquement ceux-là. Les H2 des
    # sections qui suivent (appel à l'action de fin de page) portent la même
    # indentation ; les inclure ferait pointer le sommaire hors de l'article.
    debut = texte.index('<div class="wrap article">')
    fin = texte.index('</section>', debut)
    corps, reste = texte[debut:fin], texte[fin:]

    titres = []
    def poser_ancre(m):
        t = m.group(1)
        if t.strip() in ("À lire ensuite", "Dans cet article"):
            return m.group(0)
        a = ancre(t)
        titres.append((a, t))
        return f'    <h2 id="{a}">{t}</h2>'

    corps = re.sub(r'^    <h2>(.*?)</h2>$', poser_ancre, corps, flags=re.M)
    texte = texte[:debut] + corps + reste

    if len(titres) >= 4:
        liens = "\n".join(f'        <li><a href="#{a}">{t}</a></li>' for a, t in titres)
        sommaire = ('    <nav class="sommaire" aria-label="Sommaire de l\'article">\n'
                    '      <h2>Dans cet article</h2>\n'
                    '      <ol>\n' + liens + '\n      </ol>\n'
                    '    </nav>\n\n')
        texte = texte.replace('<section>\n  <div class="wrap article">\n',
                              '<section>\n  <div class="wrap article">\n' + sommaire, 1)

    texte = re.sub(r'\n{3,}', "\n\n", texte)
    chemin.write_text(texte, encoding="utf-8")
    return True


if __name__ == "__main__":
    faits = [f.name for f in sorted(BLOG.glob("*.html"))
             if f.name != "index.html" and convertir(f)]
    print(f"{len(faits)} article(s) converti(s)")
    for f in faits:
        print("   ✓", f)
