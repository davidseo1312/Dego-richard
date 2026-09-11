#!/usr/bin/env python3
"""
Prépare les photographies d'intervention pour le web.

    photos-source/*.webp  ->  static/assets/img/interventions/*.avif|webp
                          ->  src/photos.sh   (markup <picture> prêt à poser)

Ce que fait le script
---------------------
1. Il produit chaque photographie en cinq largeurs (480 → 1536) et deux
   formats : AVIF, plus léger, et WebP en repli. Un navigateur ne télécharge
   donc jamais une image plus grande que la place qu'elle occupe.
2. Il écrit `src/photos.sh`, où chaque variante d'affichage devient une
   variable shell contenant le bloc <picture> complet — dimensions, srcset,
   sizes, alt, chargement. Le build l'importe, et une page n'a plus qu'à
   écrire {{PHOTO_EVIER_HERO}}.

Pourquoi générer le markup plutôt que l'écrire à la main : les attributs
`width`, `height` et `srcset` doivent décrire les fichiers RÉELLEMENT
présents. Écrits à la main, ils divergent au premier recadrage, et une
dimension fausse produit exactement le décalage de mise en page que ces
attributs sont censés éviter.

Dépendances : Pillow (avec support AVIF).
"""

import shlex
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "photos-source"
IMAGES = RACINE / "static" / "assets" / "img"
MANIFESTE = RACINE / "src" / "photos.sh"
PARTAGE = RACINE / "static" / "assets" / "img" / "partage"

LARGEURS = [480, 768, 1024, 1366, 1536]

# --- Les photographies, et ce qu'elles montrent -----------------------------
# Le texte alternatif décrit la scène, sans énumérer de mots-clés : il est lu
# à voix haute par une synthèse vocale, et une liste de villes n'y a rien à
# faire.
# `famille` décide du dossier de destination — /assets/img/<famille>/ — et
# rend l'ajout d'une photographie mécanique : on la dépose dans photos-source,
# on déclare ici ce qu'elle montre et à quelle famille elle appartient, et le
# script produit les dérivés, le markup et la vignette de partage. Les dossiers
# ne sont créés que lorsqu'une photographie les remplit : pas de dossier vide.
PHOTOS = {
    "debouchage-wc-inspection-camera": {
        "famille": "interventions",
        "alt": "Technicien introduisant une caméra d'inspection dans la cuvette "
               "d'un WC, enrouleur de furet posé au sol",
        "legende": "Inspection caméra d'un WC bouché",
    },
    "debouchage-evier-cuisine": {
        "famille": "interventions",
        "alt": "Technicien éclairant le siphon sous un évier de cuisine avant "
               "de le démonter",
        "legende": "Débouchage d'un évier de cuisine",
    },
    "debouchage-baignoire-inspection": {
        "famille": "interventions",
        "alt": "Technicien inspectant l'évacuation d'une baignoire à l'aide "
               "d'une caméra endoscopique",
        "legende": "Contrôle de l'évacuation d'une baignoire",
    },
    "reseau-collectif-sous-sol": {
        "famille": "interventions",
        "alt": "Technicien intervenant sur la tuyauterie d'un local technique "
               "d'immeuble",
        "legende": "Intervention sur un réseau collectif",
    },
    "urgence-degorgement-douche": {
        "famille": "interventions",
        "alt": "Technicien aspirant l'eau répandue au sol devant une douche "
               "après un refoulement",
        "legende": "Aspiration après un refoulement",
    },

    # --- Second envoi -------------------------------------------------------
    # Chaque description ne dit que ce que la photographie montre : ni lieu,
    # ni date, ni résultat. Rien de ce qui n'est pas visible n'y figure.
    "installation-broyeur-sanitaire-wc": {
        "famille": "plomberie",
        "alt": "Technicien raccordant un broyeur sanitaire derrière une cuvette "
               "de WC, coudes PVC et boîte à outils au sol",
        "legende": "Raccordement d'un broyeur sanitaire",
    },
    "demontage-siphon-lavabo": {
        "famille": "debouchage",
        "alt": "Technicien démontant à la pince le siphon chromé sous un lavabo "
               "de salle de bains",
        "legende": "Démontage du siphon d'un lavabo",
    },
    "aspiration-eau-receveur-douche": {
        "famille": "degorgement",
        "alt": "Technicien aspirant l'eau stagnante d'un receveur de douche à "
               "l'aide d'un aspirateur eau et poussière",
        "legende": "Évacuation de l'eau stagnante d'une douche",
    },
    "controle-ecoulement-evier-cuisine": {
        "famille": "interventions",
        "alt": "Technicien contrôlant l'écoulement d'un évier de cuisine, "
               "robinet ouvert et clé à molette en main",
        "legende": "Contrôle de l'écoulement d'un évier",
    },
    "inspection-camera-regard-voirie": {
        "famille": "camera",
        "alt": "Technicien descendant une caméra d'inspection dans un regard de "
               "voirie ouvert, fourgon d'intervention à l'arrière-plan",
        "legende": "Inspection caméra d'un regard de voirie",
    },
}

# --- Variantes d'affichage --------------------------------------------------
# `sizes` décrit la largeur que l'image occupera vraiment, mise en page
# comprise. C'est cette valeur, et non srcset seule, qui détermine le fichier
# choisi par le navigateur : la renseigner au jugé fait télécharger du 1536 px
# pour une vignette.
VARIANTES = {
    # Grand visuel d'ouverture de l'accueil : colonne droite du héros.
    "HERO": {
        "sizes": "(min-width: 1240px) 560px, (min-width: 980px) 46vw, calc(100vw - 2.4rem)",
        "chargement": 'fetchpriority="high" decoding="async"',
        "classe": "",
        "ratio": (3, 2),
    },
    # Ouverture des pages intérieures.
    "MEDIA": {
        "sizes": "(min-width: 1240px) 500px, (min-width: 980px) 42vw, calc(100vw - 2.4rem)",
        "chargement": 'fetchpriority="high" decoding="async"',
        "classe": "",
        "ratio": (3, 2),
    },
    # Vignette de grille : cartes de service, galerie.
    "CARTE": {
        "sizes": "(min-width: 1240px) 380px, (min-width: 900px) 33vw, (min-width: 600px) 50vw, calc(100vw - 2.4rem)",
        "chargement": 'loading="lazy" decoding="async"',
        "classe": "",
        "ratio": (3, 2),
    },
    # Vignette mise en avant de la galerie : deux colonnes sur trois.
    "LARGE": {
        "sizes": "(min-width: 1240px) 780px, (min-width: 900px) 66vw, calc(100vw - 2.4rem)",
        "chargement": 'loading="lazy" decoding="async"',
        "classe": "",
        "ratio": (3, 2),
    },
}


def variable(slug: str, variante: str) -> str:
    """PHOTO_EVIER_HERO à partir de debouchage-evier-cuisine + HERO."""
    court = {
        "debouchage-wc-inspection-camera": "WC",
        "debouchage-evier-cuisine": "EVIER",
        "debouchage-baignoire-inspection": "BAIGNOIRE",
        "reseau-collectif-sous-sol": "COLLECTIF",
        "urgence-degorgement-douche": "URGENCE",
        "installation-broyeur-sanitaire-wc": "BROYEUR",
        "demontage-siphon-lavabo": "SIPHON",
        "aspiration-eau-receveur-douche": "DOUCHE",
        "controle-ecoulement-evier-cuisine": "CUISINE",
        "inspection-camera-regard-voirie": "REGARD",
    }[slug]
    return f"PHOTO_{court}_{variante}"


def dossier(slug: str) -> Path:
    return IMAGES / PHOTOS[slug]["famille"]


def produire(slug: str) -> list:
    """Écrit les dérivés d'une photographie et rend la liste (largeur, hauteur)."""
    src = SOURCE / f"{slug}.webp"
    sortie = dossier(slug)
    sortie.mkdir(parents=True, exist_ok=True)
    origine = Image.open(src).convert("RGB")
    tailles = []
    for l in LARGEURS:
        if l > origine.width:
            continue
        h = round(origine.height * l / origine.width)
        vignette = origine.resize((l, h), Image.LANCZOS)
        # AVIF d'abord : à qualité perçue égale il pèse environ un tiers de
        # moins que WebP. WebP reste servi en repli — Safari 15 et les
        # navigateurs d'avant 2023 ne lisent pas l'AVIF.
        vignette.save(sortie / f"{slug}-{l}.avif", "AVIF", quality=58, speed=4)
        vignette.save(sortie / f"{slug}-{l}.webp", "WEBP", quality=80, method=6)
        tailles.append((l, h))
    return tailles


def markup(slug: str, variante: str, tailles: list, infos: dict) -> str:
    v = VARIANTES[variante]
    base = f"/assets/img/{PHOTOS[slug]['famille']}/{slug}"
    srcset = lambda ext: ", ".join(f"{base}-{l}.{ext} {l}w" for l, _ in tailles)
    l_ref, h_ref = tailles[-1]
    classe = f' class="{v["classe"]}"' if v["classe"] else ""
    return (
        f'<picture{classe}>'
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{v["sizes"]}">'
        f'<img src="{base}-{l_ref}.webp" srcset="{srcset("webp")}" sizes="{v["sizes"]}" '
        f'width="{l_ref}" height="{h_ref}" {v["chargement"]} '
        f'alt="{infos["alt"]}">'
        f'</picture>'
    )


def police(taille: int, gras: bool = False):
    for chemin in ("/usr/share/fonts/truetype/dejavu/DejaVuSans{s}.ttf",
                   "/usr/share/fonts/truetype/liberation/LiberationSans-{l}.ttf"):
        try:
            return ImageFont.truetype(
                chemin.format(s="-Bold" if gras else "", l="Bold" if gras else "Regular"), taille)
        except OSError:
            continue
    return ImageFont.load_default()


def image_partage(slug: str, sortie: Path) -> None:
    """
    Vignette de partage 1200×630 tirée de la photographie.

    Une photographie réelle vaut mieux qu'un schéma sur un fil d'actualité :
    c'est la seule chose que verront la plupart des gens avant de cliquer. Le
    cadrage est centré en hauteur, là où se trouve le sujet sur ces cinq
    prises de vue.
    """
    L, H = 1200, 630
    origine = Image.open(SOURCE / f"{slug}.webp").convert("RGB")
    echelle = max(L / origine.width, H / origine.height)
    redim = origine.resize((round(origine.width * echelle), round(origine.height * echelle)),
                           Image.LANCZOS)
    gauche = (redim.width - L) // 2
    haut = max(0, (redim.height - H) // 2)
    vignette = redim.crop((gauche, haut, gauche + L, haut + H))

    # Voile sombre en bas, pour que le cartouche reste lisible quelle que soit
    # la photographie.
    voile = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y - H * 0.55) / (H * 0.45))
        voile.putpixel((0, y), int(215 * (t ** 1.5)))
    voile = voile.resize((L, H))
    vignette = Image.composite(Image.new("RGB", (L, H), (10, 16, 30)), vignette, voile)

    d = ImageDraw.Draw(vignette)
    # Cartouche de marque : angles vifs, comme tout le reste du site.
    d.rectangle((44, H - 138, 44 + 74, H - 138 + 74), fill=(2, 132, 199))
    # La goutte de la marque, tracée au trait blanc dans le carré.
    import math
    cx, cy, r = 44 + 37, H - 138 + 40, 21
    points = []
    for i in range(121):
        t = 2 * math.pi * i / 120
        u, v = math.cos(t), math.sin(t) * (math.sin(t / 2) ** 1.5) / 0.6801
        points.append((cx + v * r * 1.02, cy - u * r * 1.4))
    d.line(points + [points[0]], fill=(255, 255, 255), width=5, joint="curve")
    d.text((150, H - 132), "Dégorgement Richard", font=police(44, True), fill=(255, 255, 255))
    d.text((152, H - 74), "Débouchage · Curage · Assainissement",
           font=police(25), fill=(186, 230, 253))
    vignette.save(sortie, "JPEG", quality=84, optimize=True, progressive=True)


def main() -> int:
    if not SOURCE.is_dir():
        print(f"Dossier introuvable : {SOURCE}", file=sys.stderr)
        return 1
    IMAGES.mkdir(parents=True, exist_ok=True)

    lignes = [
        "# Généré par scripts/preparer-photos.py — NE PAS MODIFIER À LA MAIN.",
        "#",
        "# Chaque variable contient un bloc <picture> complet : sources AVIF et",
        "# WebP, srcset, sizes, dimensions et texte alternatif. Une page écrit",
        "# simplement {{PHOTO_EVIER_HERO}} ; le build fait le reste.",
        "",
    ]
    PARTAGE.mkdir(parents=True, exist_ok=True)
    total = 0
    for slug, infos in PHOTOS.items():
        tailles = produire(slug)
        image_partage(slug, PARTAGE / f"og-{slug}.jpg")
        # Vignette de repli du site : celle qu'utilisent les pages sans clé
        # « image ». Une photographie y vaut mieux qu'un schéma.
        if slug == "debouchage-evier-cuisine":
            image_partage(slug, PARTAGE / "og-default.jpg")
        poids = sum((dossier(slug) / f"{slug}-{l}.{e}").stat().st_size
                    for l, _ in tailles for e in ("avif", "webp"))
        total += poids
        print(f"  ✓ {PHOTOS[slug]['famille']}/{slug} — {len(tailles)} largeurs "
              f"× 2 formats, {poids/1024:.0f} Ko")
        # Le markup et les textes contiennent des apostrophes ; shlex.quote
        # produit la seule forme que bash relit sans surprise.
        for variante in VARIANTES:
            valeur = shlex.quote(markup(slug, variante, tailles, infos))
            lignes.append(f"{variable(slug, variante)}={valeur}")
        lignes.append(f"{variable(slug, 'ALT')}={shlex.quote(infos['alt'])}")
        lignes.append(f"{variable(slug, 'LEGENDE')}={shlex.quote(infos['legende'])}")
        lignes.append("")

    MANIFESTE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"\n{len(PHOTOS)} photographies · {total/1024:.0f} Ko de dérivés")
    print(f"Markup écrit dans {MANIFESTE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
