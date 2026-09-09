#!/usr/bin/env python3
"""
Place les photographies d'intervention dans les pages.

    python3 scripts/placer-photos.py

Répartition des rôles
---------------------
Le site dispose de deux familles de visuels, et les confondre les affaiblit
toutes les deux :

  * la PHOTOGRAPHIE montre qui intervient et à quoi ressemble une
    intervention. Sa place est en ouverture de page, là où le visiteur décide
    s'il a affaire à un professionnel ;
  * le SCHÉMA explique où se forme un bouchon et comment on le traite. Sa
    place est dans le corps du texte, en appui d'une explication.

Ce script applique cette règle : il remplace le visuel d'ouverture par une
photographie, et redescend le schéma dans la page, doté d'une légende.

Aucun texte de page n'est modifié. Idempotent.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "src" / "pages"

# --- Quelle photographie pour quelle page ----------------------------------
PHOTO_PRESTATION = {
    "debouchage-wc": "WC",
    "debouchage-toilettes": "WC",
    "recherche-bouchon": "WC",
    "debouchage-evier": "EVIER",
    "debouchage-lavabo": "EVIER",
    "debouchage-cuisine": "EVIER",
    "degorgement": "EVIER",
    "debouchage-douche": "BAIGNOIRE",
    "debouchage-baignoire": "BAIGNOIRE",
    "inspection-camera-canalisation": "BAIGNOIRE",
    "debouchage-canalisation": "COLLECTIF",
    "debouchage-canalisation-exterieure": "COLLECTIF",
    "curage-canalisation": "COLLECTIF",
    "entretien-canalisation": "COLLECTIF",
    "pompage": "COLLECTIF",
    "assainissement": "COLLECTIF",
    "degorgement-professionnel": "COLLECTIF",
    "degorgement-collectif": "COLLECTIF",
    "degorgement-urgence": "URGENCE",
    # Pages transverses
    "services": "EVIER",
    "tarifs": "EVIER",
    "devis": "WC",
    "contact": "EVIER",
    "a-propos": "COLLECTIF",
    "faq": "BAIGNOIRE",
    "zone-intervention": "COLLECTIF",
}

# Rotation des pages de secteur : le choix est stable, donc reproductible,
# mais deux communes voisines ne reçoivent pas la même image.
ROTATION = ["EVIER", "WC", "BAIGNOIRE", "COLLECTIF", "URGENCE"]

# Articles : photographie quand le sujet est une situation vécue, schéma
# quand il porte sur un mécanisme.
PHOTO_ARTICLE = {
    "canalisation-bouchee-que-faire": "URGENCE",
    "canalisation-bouchee-signes": "BAIGNOIRE",
    "eau-remonte-evier": "EVIER",
    "wc-bouche-que-faire": "WC",
    "prix-degorgement": "COLLECTIF",
    "quand-utiliser-camera-inspection": "WC",
    "residence-secondaire-reouverture": "COLLECTIF",
    "comment-entretenir-canalisations": "EVIER",
    # Les quatre autres gardent leur schéma : leur sujet EST un mécanisme.
}

# Légende du schéma une fois redescendu dans la page.
LEGENDE_SCHEMA = {
    "hero-debouchage-canalisation":
        "Le réseau d'un logement en coupe : de l'appareil au regard de visite, puis au collecteur.",
    "materiel-degorgement":
        "Le matériel embarqué : enrouleur haute pression, flexible et caméra d'inspection.",
    "debouchage-wc": "Où se forme le bouchon dans un WC : la garde d'eau du siphon intégré.",
    "debouchage-evier": "Le siphon en S d'un évier, et l'endroit où les graisses se figent.",
    "debouchage-douche": "La bonde siphoïde d'un receveur de douche, obstruée par les cheveux.",
    "debouchage-baignoire": "Le vidage d'une baignoire et son siphon, en coupe.",
    "debouchage-cuisine": "D'un évier de cuisine au bac à graisses : le trajet complet des eaux grasses.",
    "debouchage-canalisation": "Une canalisation enterrée obstruée, et la buse qui progresse vers le bouchon.",
    "inspection-camera-canalisation": "Ce que voit la caméra à l'intérieur d'une conduite.",
    "curage-canalisation": "Le curage haute pression décolle le dépôt sur toute la paroi.",
    "pompage-canalisation": "Le pompage d'un regard plein, flexible plongé jusqu'au radier.",
    "assainissement": "Une fosse toutes eaux en coupe : compartiments, ventilation, départ vers l'épandage.",
    "debouchage-professionnel": "Une cuisine professionnelle raccordée à son bac à graisses enterré.",
    "canalisation-exterieure": "Des racines traversant la paroi d'une canalisation enterrée.",
    "urgence-degorgement": "Une conduite en refoulement : l'écoulement s'inverse.",
}

# Texte alternatif des schémas, repris de scripts/refonte-heros.py pour qu'il
# n'existe qu'une seule description par visuel.
def _alts():
    import importlib.util
    sp = importlib.util.spec_from_file_location("h", RACINE / "scripts" / "refonte-heros.py")
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m.ALT

ALT_SCHEMA = _alts()

IGNOREES = {"404.html", "merci.html", "mentions-legales.html",
            "politique-confidentialite.html", "conditions-generales.html",
            "blog/index.html", "index.html"}

# Le visuel d'ouverture, tel que l'a posé scripts/refonte-heros.py.
MEDIA = re.compile(
    r'      <div class="hero-media">\n'
    r'        <img src="/assets/img/schemas/(?P<schema>[a-z0-9-]+)\.webp"\n'
    r'[^\n]*\n'
    r'[^\n]*\n'
    r'      </div>\n', re.M)

# Le visuel d'introduction des articles.
VISUEL_ARTICLE = re.compile(
    r'    <figure class="article-visuel">\n'
    r'      <img src="/assets/img/schemas/(?P<schema>[a-z0-9-]+)\.webp"\n'
    r'[^\n]*\n'
    r'[^\n]*\n'
    r'    </figure>\n', re.M)


def cle_photo(rel: str) -> str | None:
    nom = rel[:-5].split("/")[-1]
    if rel.startswith("blog/"):
        return PHOTO_ARTICLE.get(nom)
    if nom in PHOTO_PRESTATION:
        return PHOTO_PRESTATION[nom]
    if rel.startswith("departements/") or nom.startswith("degorgement-"):
        return ROTATION[sum(ord(c) for c in nom) % len(ROTATION)]
    return None


def figure_schema(schema: str) -> str:
    """Le schéma, redescendu dans la page, avec la légende qui l'explique."""
    from PIL import Image
    legende = LEGENDE_SCHEMA.get(schema, "")
    # Dimensions lues sur le fichier : écrites au jugé, elles produiraient le
    # décalage de mise en page que ces attributs servent à supprimer.
    l, h = Image.open(RACINE / "static/assets/img/schemas" / f"{schema}.webp").size
    return (
        '    <figure class="schema">\n'
        f'      <img src="/assets/img/schemas/{schema}.webp" width="{l}" height="{h}"\n'
        '           loading="lazy" decoding="async"\n'
        f'           alt="{ALT_SCHEMA.get(schema, legende)}">\n'
        f'      <figcaption>{legende}</figcaption>\n'
        '    </figure>\n\n'
    )


def convertir(chemin: Path) -> str | None:
    rel = chemin.relative_to(PAGES).as_posix()
    if rel in IGNOREES:
        return None
    texte = chemin.read_text(encoding="utf-8")
    if "{{PHOTO_" in texte:
        return None                                  # déjà traité

    cle = cle_photo(rel)
    if cle is None:
        return None

    if rel.startswith("blog/"):
        m = VISUEL_ARTICLE.search(texte)
        if not m:
            return None
        remplacement = ('    <figure class="article-visuel">\n'
                        f'      {{{{PHOTO_{cle}_LARGE}}}}\n'
                        '    </figure>\n')
        texte = texte.replace(m.group(0), remplacement, 1)
        chemin.write_text(texte, encoding="utf-8")
        return f"{rel} → photo {cle}"

    m = MEDIA.search(texte)
    if not m:
        return None
    schema = m.group("schema")

    texte = texte.replace(
        m.group(0),
        '      <div class="hero-media">\n'
        f'        {{{{PHOTO_{cle}_MEDIA}}}}\n'
        '      </div>\n', 1)

    # Le schéma redescend juste après le bloc « Réponse rapide », là où il
    # appuie une explication. Les pages de secteur n'en reçoivent pas : leur
    # sujet est un territoire, pas un ouvrage.
    detail = ""
    interieur = not (rel.startswith("departements/")
                     or (rel[:-5].split("/")[-1].startswith("degorgement-")
                         and rel[:-5].split("/")[-1] not in PHOTO_PRESTATION))
    if interieur and schema in LEGENDE_SCHEMA:
        fin = texte.find("</div>\n", texte.find('<div class="reponse-rapide">'))
        if fin != -1:
            insertion = texte.index("\n", fin) + 1
            texte = texte[:insertion] + "\n" + figure_schema(schema) + texte[insertion:]
            detail = f", schéma {schema} redescendu"

    chemin.write_text(texte, encoding="utf-8")
    return f"{rel} → photo {cle}{detail}"


if __name__ == "__main__":
    faits = [r for f in sorted(PAGES.rglob("*.html")) if (r := convertir(f))]
    print(f"{len(faits)} page(s) traitée(s)")
    for r in faits[:12]:
        print("   ✓", r)
    if len(faits) > 12:
        print(f"   … et {len(faits) - 12} autres")
