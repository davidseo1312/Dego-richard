#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Génère les images matricielles que le format vectoriel ne peut pas couvrir :
# la vignette de partage social, les icônes d'application et le favicon .ico.
#
#   python3 scripts/generer-images.py
#
# Ce script est FACULTATIF. Les fichiers qu'il produit sont déjà versionnés
# dans static/assets/img/ : le site se construit et se déploie sans lui.
# Relancez-le après avoir changé le nom commercial, la baseline ou les
# couleurs de la marque.
#
# Dépendance : Pillow (pip install Pillow). Volontairement hors du build, qui
# doit rester exécutable avec bash seul.
#
# Le numéro de téléphone n'est PAS incrusté dans la vignette : une image est
# mise en cache des mois par les réseaux sociaux, et un numéro périmé y ferait
# plus de dégâts que son absence.
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow est absent. Installez-le avec : pip install Pillow")

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "static" / "assets" / "img"

# --- Charte ----------------------------------------------------------------
BLEU_900 = (4, 28, 43)
BLEU_800 = (6, 40, 61)
BLEU_700 = (11, 61, 92)
CYAN = (18, 165, 184)
ORANGE = (255, 122, 26)
BLANC = (255, 255, 255)
BLEU_CLAIR = (180, 214, 230)

POLICES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans{suffixe}.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans{suffixe2}.ttf",
]


def police(taille: int, gras: bool = False):
    for gabarit in POLICES:
        chemin = gabarit.format(
            suffixe="-Bold" if gras else "",
            suffixe2="-Bold" if gras else "-Regular",
        )
        if Path(chemin).exists():
            return ImageFont.truetype(chemin, taille)
    return ImageFont.load_default()


def lire_config(cle: str, defaut: str) -> str:
    """Lit une valeur de src/config.sh, pour que la vignette suive le nom
    commercial sans qu'on ait à l'écrire deux fois."""
    fichier = RACINE / "src" / "config.sh"
    if not fichier.exists():
        return defaut
    motif = re.compile(rf'^{cle}="(.*)"$', re.M)
    trouve = motif.search(fichier.read_text(encoding="utf-8"))
    return trouve.group(1) if trouve else defaut


NOM = lire_config("NOM_COMMERCIAL", "Dégorgement Richard")
BASELINE = lire_config("BASELINE", "Dégorgement et débouchage dans le Grand Ouest")


def contour_goutte(cx: float, cy: float, r: float, pas: int = 160):
    """Points du contour d'une goutte pointant vers le haut.

    Le tracé vient d'une courbe paramétrique : un cercle et un triangle
    juxtaposés laissent toujours une couture visible à l'endroit où ils se
    rejoignent, alors qu'ici la pointe et le ventre sont une seule courbe.
    """
    import math

    largeur = r * 1.02          # demi-largeur du ventre
    hauteur = r * 1.55          # du centre du ventre à la pointe
    n = 1.5                     # plus n est grand, plus la pointe est fine
    v_max = 0.6801              # maximum de sin(t)·sin(t/2)^n, pour normaliser

    points = []
    for i in range(pas + 1):
        t = 2 * math.pi * i / pas
        u = math.cos(t)
        v = math.sin(t) * (math.sin(t / 2) ** n) / v_max
        points.append((cx + v * largeur, cy - u * hauteur))
    return points


def goutte(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, couleur, epaisseur: int):
    """Silhouette de goutte : le repère visuel de la marque."""
    d.line(contour_goutte(cx, cy, r), fill=couleur, width=epaisseur, joint="curve")


def icone(taille: int, marge_ratio: float = 0.0) -> Image.Image:
    img = Image.new("RGB", (taille, taille), BLEU_800)
    d = ImageDraw.Draw(img)
    interieur = int(taille * (1 - 2 * marge_ratio))
    r = int(interieur * 0.235)
    cx = taille // 2
    cy = taille // 2 - int(interieur * 0.06)
    goutte(d, cx, cy, r, CYAN, max(2, taille // 36))
    # Trait de sol : posé SOUS la goutte, jamais au travers.
    base = cy + int(r * 1.55) + max(3, taille // 18)
    d.line([(cx - int(r * 0.8), base), (cx + int(r * 0.8), base)],
           fill=ORANGE, width=max(2, taille // 42))
    return img


def vignette() -> Image.Image:
    L, H = 1200, 630
    img = Image.new("RGB", (L, H), BLEU_800)
    d = ImageDraw.Draw(img)

    # Dégradé vertical discret : deux aplats suffisent à donner du relief
    # sans alourdir le fichier.
    for y in range(H):
        t = y / H
        c = tuple(int(BLEU_900[i] + (BLEU_700[i] - BLEU_900[i]) * t) for i in range(3))
        d.line([(0, y), (L, y)], fill=c)

    goutte(d, 150, 262, 66, CYAN, 11)

    d.text((260, 168), NOM, font=police(70, gras=True), fill=BLANC)
    # La baseline complète déborderait : la vignette porte une accroche courte,
    # le texte long reste dans les métadonnées Open Graph.
    d.text((260, 262), "Débouchage · Curage · Assainissement",
           font=police(36), fill=BLEU_CLAIR)

    d.line([(262, 344), (262 + 120, 344)], fill=ORANGE, width=8)

    zones = "Côtes-d'Armor · Finistère · Ille-et-Vilaine"
    zones2 = "Morbihan · Loire-Atlantique · Maine-et-Loire"
    d.text((260, 384), zones, font=police(29), fill=BLANC)
    d.text((260, 426), zones2, font=police(29), fill=BLANC)

    d.text((260, 502), "Intervention 24h/24 — devis écrit avant travaux",
           font=police(27), fill=BLEU_CLAIR)
    return img


def main() -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)

    icone(192).save(SORTIE / "icone-192.png", optimize=True)
    icone(512).save(SORTIE / "icone-512.png", optimize=True)
    icone(512, marge_ratio=0.20).save(SORTIE / "icone-512-maskable.png", optimize=True)
    icone(180).save(SORTIE / "apple-touch-icon.png", optimize=True)

    base = icone(256)
    base.save(SORTIE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    vignette().save(SORTIE / "og-default.jpg", quality=82, optimize=True, progressive=True)

    for f in ("icone-192.png", "icone-512.png", "icone-512-maskable.png",
              "apple-touch-icon.png", "favicon.ico", "og-default.jpg"):
        chemin = SORTIE / f
        print(f"  ✓ {f} — {chemin.stat().st_size // 1024} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
