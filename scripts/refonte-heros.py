#!/usr/bin/env python3
"""
Applique le nouveau gabarit de héros aux pages intérieures.

    python3 scripts/refonte-heros.py [--verifier]

Les pages de prestation, de département, de commune et d'article partagent
toutes la même ouverture : un fil d'Ariane, puis un bloc « section-titre »
contenant le H1, l'accroche et les deux appels à l'action. Ce script les
recompose en une bande de héros — badge, titre, accroche, actions, visuel —
sans toucher au reste de la page.

Ce qui est déplacé, jamais réécrit : le H1, l'accroche et les liens restent
mot pour mot ce qu'ils étaient. Le référencement d'une page tient à ce
texte-là ; une refonte visuelle n'a aucune raison d'y toucher.

Le script est idempotent : une page déjà convertie est laissée telle quelle.
"""

import re
import sys
import textwrap
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "src" / "pages"

# --- Visuel associé à chaque page ------------------------------------------
# Une prestation reçoit le visuel qui la décrit. Les pages de secteur, elles,
# n'ont pas de visuel propre : leur sujet est un territoire, pas un ouvrage.
# On leur attribue une vue de réseau, choisie de façon stable d'après le nom
# du fichier pour que deux communes voisines ne se ressemblent pas.

VISUEL_PRESTATION = {
    "debouchage-wc": "debouchage-wc",
    "debouchage-toilettes": "debouchage-wc",
    "debouchage-evier": "debouchage-evier",
    "debouchage-lavabo": "debouchage-evier",
    "debouchage-douche": "debouchage-douche",
    "debouchage-baignoire": "debouchage-baignoire",
    "debouchage-cuisine": "debouchage-cuisine",
    "debouchage-canalisation": "debouchage-canalisation",
    "debouchage-canalisation-exterieure": "canalisation-exterieure",
    "curage-canalisation": "curage-canalisation",
    "inspection-camera-canalisation": "inspection-camera-canalisation",
    "recherche-bouchon": "inspection-camera-canalisation",
    "pompage": "pompage-canalisation",
    "assainissement": "assainissement",
    "entretien-canalisation": "curage-canalisation",
    "degorgement": "hero-debouchage-canalisation",
    "degorgement-urgence": "urgence-degorgement",
    "degorgement-professionnel": "debouchage-professionnel",
    "degorgement-collectif": "debouchage-canalisation",
    "services": "materiel-degorgement",
    "tarifs": "materiel-degorgement",
    "zone-intervention": "hero-debouchage-canalisation",
    "a-propos": "materiel-degorgement",
    "faq": "inspection-camera-canalisation",
    "contact": "hero-debouchage-canalisation",
    "devis": "materiel-degorgement",
}

# Rotation pour les pages de secteur : uniquement des vues de réseau, jamais
# un sanitaire — une page « Dégorgement à Vannes » parle de canalisations.
VISUEL_SECTEUR = [
    "hero-debouchage-canalisation",
    "debouchage-canalisation",
    "canalisation-exterieure",
    "inspection-camera-canalisation",
    "curage-canalisation",
    "assainissement",
    "pompage-canalisation",
]

# Dimensions réelles des fichiers, pour écrire width/height sans les deviner.
DIMENSIONS = {
    "hero-debouchage-canalisation": (1120, 840),
    "materiel-degorgement": (960, 720),
    "debouchage-wc": (960, 720),
    "debouchage-evier": (960, 720),
    "debouchage-douche": (960, 720),
    "debouchage-baignoire": (960, 720),
    "debouchage-cuisine": (960, 720),
    "debouchage-canalisation": (1120, 700),
    "inspection-camera-canalisation": (1120, 700),
    "curage-canalisation": (1120, 700),
    "pompage-canalisation": (960, 720),
    "assainissement": (1120, 700),
    "debouchage-professionnel": (960, 720),
    "canalisation-exterieure": (960, 720),
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
    "debouchage-professionnel":
        "Coupe d'une installation de cuisine professionnelle raccordée à un bac à graisses enterré",
    "canalisation-exterieure":
        "Coupe d'une canalisation extérieure enterrée traversée par des racines d'arbre, avec "
        "son regard de visite",
    "urgence-degorgement":
        "Vue intérieure d'une canalisation en refoulement : conduite pleine et bouchon "
        "bloquant l'écoulement",
}

# Pages qui n'ont pas à recevoir de héros : mentions, pages de service, 404…
IGNOREES = {
    "404.html", "merci.html", "mentions-legales.html",
    "politique-confidentialite.html", "conditions-generales.html",
    "index.html", "blog/index.html",
}

BLOC_FIL = re.compile(
    r'<div class="wrap fil">\s*\n(?P<nav>.*?)\n</div>\n', re.S)
BLOC_TITRE = re.compile(
    r'<section>\n  <div class="wrap">\n    <div class="section-titre">\n'
    r'(?P<interieur>.*?)\n    </div>\n', re.S)

H1 = re.compile(r'<h1>(?P<t>.*?)</h1>', re.S)
ACTIONS = re.compile(r'<p class="hero-actions">(?P<a>.*?)</p>', re.S)


def reindenter(bloc: str, colonnes: int) -> str:
    """Ré-indente un bloc à la colonne voulue en conservant sa hiérarchie."""
    return textwrap.indent(textwrap.dedent(bloc.strip("\n")), " " * colonnes)


def meta_valeur(texte: str, cle: str) -> str:
    m = re.search(rf'^{cle}:\s*(.+)$', texte, re.M)
    return m.group(1).strip() if m else ""


def choisir_visuel(rel: str) -> str:
    base = rel[:-5] if rel.endswith(".html") else rel
    nom = base.split("/")[-1]
    if base.startswith("departements/") or nom.startswith("degorgement-") and nom not in VISUEL_PRESTATION:
        # Choix stable : la même page reçoit toujours le même visuel.
        return VISUEL_SECTEUR[sum(ord(c) for c in nom) % len(VISUEL_SECTEUR)]
    return VISUEL_PRESTATION.get(nom, "hero-debouchage-canalisation")


def badge_pour(rel: str, texte: str) -> str:
    """Pastille d'en-tête, adaptée à la nature de la page."""
    if rel.startswith("departements/"):
        return ('<span class="pastille" aria-hidden="true"></span> '
                'Intervention {{DISPONIBILITE}} dans tout le département')
    zone = meta_valeur(texte, "zone_nom")
    parent = meta_valeur(texte, "zone_parent")
    if zone and parent:
        return ('<span class="pastille" aria-hidden="true"></span> '
                f'Intervention à {zone} · {parent}')
    if zone:
        return ('<span class="pastille" aria-hidden="true"></span> '
                f'Intervention à {zone}')
    return ('<span class="pastille" aria-hidden="true"></span> '
            'Intervention {{DISPONIBILITE}} · 6 départements')


def convertir(chemin: Path) -> bool:
    rel = chemin.relative_to(PAGES).as_posix()
    if rel in IGNOREES:
        return False

    texte = chemin.read_text(encoding="utf-8")
    if 'class="hero hero-interieur"' in texte:
        return False                      # déjà converti

    m_fil = BLOC_FIL.search(texte)
    m_titre = BLOC_TITRE.search(texte)
    if not m_fil or not m_titre:
        return False

    interieur = m_titre.group("interieur")
    m_h1 = H1.search(interieur)
    if not m_h1:
        return False

    m_actions = ACTIONS.search(interieur)
    actions = m_actions.group("a") if m_actions else ""

    # L'accroche : tout ce qui reste une fois le H1 et les actions retirés.
    accroche = H1.sub("", interieur)
    accroche = ACTIONS.sub("", accroche)
    accroche = "\n".join(l for l in accroche.splitlines() if l.strip())
    accroche = reindenter(accroche, 8)
    accroche = re.sub(r'<p>', '<p class="chapeau">', accroche, count=1)

    visuel = choisir_visuel(rel)
    l, h = DIMENSIONS[visuel]
    nav = reindenter(m_fil.group("nav"), 6)

    bloc_actions = ""
    if actions.strip():
        bloc_actions = ('\n        <div class="hero-actions">\n'
                        + reindenter(actions, 10) + "\n        </div>")

    hero = f'''<section class="hero hero-interieur">
  <div class="wrap">
    <div class="fil">
{nav}
    </div>

    <div class="hero-grid">
      <div>
        <p class="urgence-badge">{badge_pour(rel, texte)}</p>
        <h1>{m_h1.group("t").strip()}</h1>
{accroche}{bloc_actions}
      </div>

      <div class="hero-media">
        <img src="/assets/img/schemas/{visuel}.webp"
             width="{l}" height="{h}" fetchpriority="high" decoding="async"
             alt="{ALT[visuel]}">
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
'''

    # Le fil d'Ariane et le bloc de titre disparaissent de leur emplacement
    # d'origine ; le reste de la première section est conservé intact.
    texte = texte.replace(m_titre.group(0), hero, 1)
    texte = texte.replace(m_fil.group(0), "", 1)
    texte = re.sub(r'\n{3,}', "\n\n", texte)
    chemin.write_text(texte, encoding="utf-8")
    return True


if __name__ == "__main__":
    verifier = "--verifier" in sys.argv
    faits, ignores = [], []
    for f in sorted(PAGES.rglob("*.html")):
        rel = f.relative_to(PAGES).as_posix()
        if verifier:
            t = f.read_text(encoding="utf-8")
            if rel not in IGNOREES and 'class="hero hero-interieur"' not in t:
                ignores.append(rel)
            continue
        (faits if convertir(f) else ignores).append(rel)

    if verifier:
        print(f"{len(ignores)} page(s) sans héros :")
        for r in ignores:
            print("   ", r)
    else:
        print(f"{len(faits)} page(s) converties, {len(ignores)} laissées telles quelles.")
        for r in ignores:
            if r not in IGNOREES:
                print("   ~ non convertie :", r)
