#!/usr/bin/env python3
"""
Génère la bibliothèque de visuels du site.

    scripts/generer-visuels.py  ->  static/assets/img/photos/*.webp

Pourquoi des illustrations et non des photographies
---------------------------------------------------
L'environnement de construction n'a pas accès aux banques d'images (Unsplash,
Pexels, Pixabay, Wikimedia : toutes refusées par la politique réseau). Plutôt
que de laisser des zones vides ou de publier une image dont la licence ne peut
pas être vérifiée, chaque visuel est DESSINÉ ICI. Conséquences :

  * la licence est celle du dépôt — aucun tiers, aucun filigrane, aucun logo ;
  * le style est homogène sur l'ensemble de la bibliothèque, ce qu'un
    assemblage de photos de banques ne garantit jamais ;
  * remplacer un visuel par une vraie photographie ne demande qu'à déposer un
    fichier du même nom dans static/assets/img/photos/ : le HTML ne bouge pas.

Parti pris graphique
--------------------
Deux familles, et rien d'autre :

  1. LA COUPE TECHNIQUE — le réseau vu en section, comme sur un plan
     d'exécution : terrain, ouvrage, canalisation, pente, annotations. C'est
     le langage du métier, et il se calcule exactement.
  2. L'INTÉRIEUR DE CANALISATION — la vue qu'un opérateur a réellement dans
     son moniteur : un tunnel qui fuit vers un point de fuite, une lame d'eau
     au fond, l'outil en action.

Aucun personnage, aucun véhicule : dessinés en code, ils versent
immédiatement dans la caricature. La géométrie, elle, est calculée — les
ellipses d'un tunnel décroissent selon une raison géométrique, les
canalisations ont une épaisseur de paroi constante, les cotes tombent juste.

Dépendances : playwright (chromium déjà présent) et Pillow.
"""

import asyncio
import io
import math
import shutil
import sys
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "static" / "assets" / "img" / "schemas"
CHROMIUM = "/opt/pw-browsers/chromium"

# --- Palette (identique aux jetons de la feuille de style) ------------------
BLEU_100, BLEU_200, BLEU_300 = "#e0f2fe", "#bae6fd", "#7dd3fc"
BLEU_400, BLEU_500, BLEU_600 = "#38bdf8", "#0ea5e9", "#0284c7"
BLEU_700, BLEU_800, BLEU_900 = "#0369a1", "#075985", "#0c4a6e"
NUIT, NUIT_800, NUIT_700 = "#0f172a", "#1e293b", "#334155"
ORANGE, ORANGE_F = "#f97316", "#c2410c"
ARDOISE, GRIS_C, BLANC = "#64748b", "#e2e8f0", "#ffffff"
TERRE, TERRE_F = "#c9b28c", "#a8906a"

POLICE = "Inter, 'Segoe UI', system-ui, sans-serif"


# ---------------------------------------------------------------------------
# Outils de calcul
# ---------------------------------------------------------------------------

def melange(a: str, b: str, t: float) -> str:
    """Interpolation linéaire entre deux couleurs hexadécimales."""
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


def pt_ellipse(cx, cy, rx, ry, deg):
    """Point d'une ellipse à l'angle donné (0° = droite, 90° = bas)."""
    a = math.radians(deg)
    return cx + rx * math.cos(a), cy + ry * math.sin(a)


# ---------------------------------------------------------------------------
# Briques communes
# ---------------------------------------------------------------------------

def defs() -> str:
    return f"""
    <defs>
      <linearGradient id="ciel" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{BLEU_100}"/>
        <stop offset=".62" stop-color="#f4fbff"/>
        <stop offset="1" stop-color="{BLANC}"/>
      </linearGradient>
      <linearGradient id="paroi" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#f1f5f9"/>
        <stop offset=".28" stop-color="#cbd5e1"/>
        <stop offset="1"   stop-color="#94a3b8"/>
      </linearGradient>
      <linearGradient id="paroiV" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0"   stop-color="#f1f5f9"/>
        <stop offset=".28" stop-color="#cbd5e1"/>
        <stop offset="1"   stop-color="#94a3b8"/>
      </linearGradient>
      <linearGradient id="eau" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{BLEU_300}"/>
        <stop offset="1" stop-color="{BLEU_700}"/>
      </linearGradient>
      <linearGradient id="eauSombre" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{BLEU_500}" stop-opacity=".85"/>
        <stop offset="1" stop-color="{BLEU_900}"/>
      </linearGradient>
      <linearGradient id="inox" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#f8fafc"/>
        <stop offset=".4" stop-color="#cbd5e1"/>
        <stop offset=".55" stop-color="#e2e8f0"/>
        <stop offset="1" stop-color="#7c8ba1"/>
      </linearGradient>
      <linearGradient id="orange" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#fb923c"/>
        <stop offset="1" stop-color="{ORANGE_F}"/>
      </linearGradient>
      <linearGradient id="ceramique" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{BLANC}"/>
        <stop offset=".55" stop-color="#f1f5f9"/>
        <stop offset="1" stop-color="#dbe3ec"/>
      </linearGradient>
      <radialGradient id="halo" cx=".5" cy=".5" r=".5">
        <stop offset="0" stop-color="{BLEU_400}" stop-opacity=".35"/>
        <stop offset="1" stop-color="{BLEU_400}" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="haloOrange" cx=".5" cy=".5" r=".5">
        <stop offset="0" stop-color="{ORANGE}" stop-opacity=".55"/>
        <stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="lampe" cx=".5" cy=".5" r=".5">
        <stop offset="0" stop-color="#fffbeb" stop-opacity=".92"/>
        <stop offset=".45" stop-color="#fde68a" stop-opacity=".35"/>
        <stop offset="1" stop-color="#fde68a" stop-opacity="0"/>
      </radialGradient>
      <filter id="ombre" x="-40%" y="-40%" width="180%" height="200%">
        <feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#0f172a" flood-opacity=".18"/>
      </filter>
      <filter id="ombreDouce" x="-40%" y="-40%" width="180%" height="200%">
        <feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#0f172a" flood-opacity=".16"/>
      </filter>
      <filter id="flou12"><feGaussianBlur stdDeviation="12"/></filter>
      <filter id="flou4"><feGaussianBlur stdDeviation="4"/></filter>

      <pattern id="terre" width="26" height="26" patternUnits="userSpaceOnUse"
               patternTransform="rotate(45)">
        <rect width="26" height="26" fill="{TERRE}"/>
        <path d="M0 0 V26" stroke="{TERRE_F}" stroke-width="2.2" opacity=".55"/>
      </pattern>
      <pattern id="gravier" width="34" height="34" patternUnits="userSpaceOnUse">
        <rect width="34" height="34" fill="#d6d3d1"/>
        <circle cx="8"  cy="9"  r="3.4" fill="#a8a29e"/>
        <circle cx="24" cy="6"  r="2.6" fill="#b6b1ac"/>
        <circle cx="17" cy="21" r="3.8" fill="#a8a29e"/>
        <circle cx="30" cy="26" r="2.4" fill="#b6b1ac"/>
        <circle cx="4"  cy="27" r="2.8" fill="#b6b1ac"/>
      </pattern>
      <pattern id="carrelage" width="52" height="52" patternUnits="userSpaceOnUse">
        <rect width="52" height="52" fill="#e8eef4"/>
        <rect x="1.6" y="1.6" width="48.8" height="48.8" rx="3" fill="#f6f9fc"/>
      </pattern>
      <pattern id="beton" width="40" height="40" patternUnits="userSpaceOnUse">
        <rect width="40" height="40" fill="#cbd5e1"/>
        <circle cx="11" cy="14" r="1.9" fill="#b3bfcd"/>
        <circle cx="29" cy="27" r="2.3" fill="#b3bfcd"/>
        <circle cx="33" cy="8"  r="1.6" fill="#b3bfcd"/>
      </pattern>
    </defs>"""


def fond_clair(w, h) -> str:
    """Lavis de fond des coupes techniques."""
    return f"""
    <rect width="{w}" height="{h}" fill="url(#ciel)"/>
    <ellipse cx="{w*0.76:.0f}" cy="{h*0.16:.0f}" rx="{w*0.46:.0f}" ry="{h*0.44:.0f}" fill="url(#halo)"/>"""


def fond_sombre(w, h, chaud=False) -> str:
    halo = "haloOrange" if chaud else "halo"
    return f"""
    <rect width="{w}" height="{h}" fill="#080e1a"/>
    <ellipse cx="{w*0.5:.0f}" cy="{h*0.5:.0f}" rx="{w*0.5:.0f}" ry="{h*0.5:.0f}" fill="url(#{halo})"/>"""


def texte(x, y, contenu, taille=20, poids=650, couleur=NUIT, ancre="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{ancre}" font-family="{POLICE}" '
            f'font-size="{taille}" font-weight="{poids}" fill="{couleur}">{contenu}</text>')


def etiquette(x, y, contenu, vers=None, couleur=BLEU_700, fond=BLANC):
    """Annotation encadrée, avec ligne de rappel facultative vers un point."""
    largeur = 15 + len(contenu) * 9.6
    rappel = ""
    if vers:
        rappel = (f'<path d="M{x:.0f} {y+16:.0f} L{vers[0]:.0f} {vers[1]:.0f}" '
                  f'stroke="{couleur}" stroke-width="2" stroke-dasharray="6 6" opacity=".85"/>'
                  f'<circle cx="{vers[0]:.0f}" cy="{vers[1]:.0f}" r="5" fill="{couleur}"/>')
    return (rappel +
            f'<g transform="translate({x-largeur/2:.0f},{y-16:.0f})" filter="url(#ombreDouce)">'
            f'<rect width="{largeur:.0f}" height="34" rx="17" fill="{fond}" '
            f'stroke="{melange(couleur, BLANC, .72)}" stroke-width="2"/>'
            f'{texte(largeur/2, 23, contenu, 16, 700, couleur, "middle")}</g>')


def cote(x1, y1, x2, y2, libelle):
    """Ligne de cote avec flèches — le détail qui fait lire « plan », pas « dessin »."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    return (f'<g stroke="{ARDOISE}" stroke-width="1.8" fill="none">'
            f'<path d="M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f}"/>'
            f'<path d="M{x1:.0f} {y1-7:.0f} v14"/><path d="M{x2:.0f} {y2-7:.0f} v14"/></g>'
            f'<rect x="{mx-34:.0f}" y="{my-13:.0f}" width="68" height="26" rx="6" fill="{BLANC}" opacity=".92"/>'
            f'{texte(mx, my+6, libelle, 15, 650, ARDOISE, "middle")}')


# ---------------------------------------------------------------------------
# Famille 1 — intérieur de canalisation
# ---------------------------------------------------------------------------

def tunnel(cx, cy, rx, ry, anneaux=26, raison=0.855, fuite=(0, 0),
           teinte_proche="#3f4a5c", teinte_loin="#050a14", eau=0.0):
    """
    Intérieur d'une canalisation vu depuis l'entrée.

    Les anneaux décroissent selon une raison géométrique constante et leur
    centre glisse linéairement vers le point de fuite : c'est exactement ce
    que produit une projection en perspective, et c'est ce qui manque à un
    empilement d'ellipses posées à la main.

    `eau` (0 à 1) est la hauteur de la lame d'eau, en fraction du diamètre.
    """
    morceaux = []
    rayons = []
    for i in range(anneaux):
        f = i / max(1, anneaux - 1)
        r_x, r_y = rx * (raison ** i), ry * (raison ** i)
        c_x = cx + (fuite[0] - cx) * (1 - raison ** i) / (1 - raison ** (anneaux - 1))
        c_y = cy + (fuite[1] - cy) * (1 - raison ** i) / (1 - raison ** (anneaux - 1))
        couleur = melange(teinte_proche, teinte_loin, f ** 0.72)
        morceaux.append(f'<ellipse cx="{c_x:.1f}" cy="{c_y:.1f}" rx="{r_x:.1f}" '
                        f'ry="{r_y:.1f}" fill="{couleur}"/>')
        rayons.append((c_x, c_y, r_x, r_y))

    # Nervures : une ellipse claire tous les quatre anneaux, très discrète.
    for i in range(2, anneaux - 3, 4):
        c_x, c_y, r_x, r_y = rayons[i]
        morceaux.append(f'<ellipse cx="{c_x:.1f}" cy="{c_y:.1f}" rx="{r_x:.1f}" ry="{r_y:.1f}" '
                        f'fill="none" stroke="#94a3b8" stroke-width="{max(0.6, 2.6*(1-i/anneaux)):.1f}" '
                        f'opacity="{0.30*(1-i/anneaux):.2f}"/>')

    # Lame d'eau. Ce qu'on voit réellement dans une conduite en eau, ce sont
    # deux choses distinctes, et les confondre est ce qui fait « dessin » :
    #   1. la paroi immergée du premier anneau — un segment circulaire sombre ;
    #   2. la SURFACE, un plan qui fuit vers le point de fuite et se réduit à
    #      un coin. Ses bords sont les lignes de rive, là où l'eau touche la
    #      paroi ; elle s'assombrit avec la distance, d'où le dégradé radial
    #      centré sur le point de fuite.
    if eau > 0:
        t = 1 - 2 * eau
        cos_g = -math.sqrt(max(0.0, 1 - t * t))

        def rive(anneau):
            c_x, c_y, r_x, r_y = anneau
            return ((c_x + r_x * cos_g, c_y + r_y * t),
                    (c_x - r_x * cos_g, c_y + r_y * t))

        # 1. paroi immergée, au premier plan. L'arc doit passer par le BAS de
        #    l'ellipse (angle +90°) : on part donc de la rive gauche et on fait
        #    décroître l'angle jusqu'à la rive droite, en repassant sous zéro
        #    si nécessaire — sinon, au-delà d'un demi-diamètre d'eau, l'arc
        #    bascule par le haut et noie toute la conduite.
        c_x, c_y, r_x, r_y = rayons[0]
        a_g = math.atan2(t, cos_g) % (2 * math.pi)
        a_d = math.atan2(t, -cos_g) % (2 * math.pi)
        if a_d > a_g:
            a_d -= 2 * math.pi
        pts = [(c_x + r_x * math.cos(a_g + (a_d - a_g) * k / 28),
                c_y + r_y * math.sin(a_g + (a_d - a_g) * k / 28)) for k in range(29)]
        morceaux.append('<path d="M' + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
                        + ' Z" fill="#07253c"/>')

        # 2. surface, du premier anneau jusqu'au point de fuite
        gauche = [rive(a)[0] for a in rayons[:-2]]
        droite = [rive(a)[1] for a in rayons[:-2]]
        contour = gauche + list(reversed(droite))
        d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in contour) + " Z"
        fx, fy = fuite
        morceaux.append(
            f'<radialGradient id="surfEau" gradientUnits="userSpaceOnUse" '
            f'cx="{fx:.0f}" cy="{fy:.0f}" r="{rx*1.25:.0f}">'
            f'<stop offset="0" stop-color="#06263f"/>'
            f'<stop offset=".55" stop-color="{BLEU_700}"/>'
            f'<stop offset="1" stop-color="{BLEU_400}"/></radialGradient>')
        morceaux.append(f'<path d="{d}" fill="url(#surfEau)"/>')

        # Reflet spéculaire : une bande claire le long de la rive éclairée.
        n = min(len(gauche), 10)
        reflet = ("M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in gauche[:n])
                  + " L" + " L".join(f"{px+ (droite[i][0]-px)*0.34:.1f} {py:.1f}"
                                     for i, (px, py) in reversed(list(enumerate(gauche[:n])))) + " Z")
        morceaux.append(f'<path d="{reflet}" fill="{BLEU_200}" opacity=".16"/>')

        # Ligne de rive au premier plan : c'est elle qui donne le niveau.
        (xg, yg), (xd, yd) = rive(rayons[0])
        morceaux.append(f'<path d="M{xg:.1f} {yg:.1f} L{xd:.1f} {yd:.1f}" '
                        f'stroke="{BLEU_200}" stroke-width="3" opacity=".7"/>')

    return "".join(morceaux), rayons


def anneau_entree(cx, cy, rx, ry, epaisseur=26):
    """Tranche de paroi à l'entrée du tunnel : donne son épaisseur au tuyau."""
    return (f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx+epaisseur:.0f}" ry="{ry+epaisseur:.0f}" '
            f'fill="url(#paroi)"/>'
            f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx+epaisseur:.0f}" ry="{ry+epaisseur:.0f}" '
            f'fill="none" stroke="#8b98a9" stroke-width="2"/>')


def tete_camera(x, y, e=1.0):
    """Tête de caméra d'inspection : corps inox, dôme, couronne de LED, cône."""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <ellipse cx="120" cy="0" rx="150" ry="118" fill="url(#lampe)"/>
      <rect x="-104" y="-30" width="120" height="60" rx="16" fill="url(#inox)"/>
      <rect x="-104" y="-30" width="120" height="12" rx="6" fill="#f8fafc" opacity=".85"/>
      <circle cx="26" cy="0" r="36" fill="#111a2b"/>
      <circle cx="26" cy="0" r="34" fill="none" stroke="url(#inox)" stroke-width="5"/>
      <circle cx="26" cy="0" r="22" fill="#0b2a44"/>
      <circle cx="26" cy="0" r="12" fill="{BLEU_400}"/>
      <circle cx="20" cy="-7" r="5" fill="{BLANC}" opacity=".95"/>
      <g fill="#fef3c7">
        <circle cx="26" cy="-31" r="5.5"/><circle cx="26" cy="31" r="5.5"/>
        <circle cx="52" cy="-18" r="5.5"/><circle cx="52" cy="18" r="5.5"/>
        <circle cx="57" cy="0" r="5.5"/>
      </g>
      <path d="M-104 -18 h-46" stroke="#0b1220" stroke-width="19" stroke-linecap="round"/>
    </g>"""


def buse(x, y, e=1.0, jets=True):
    """Buse rotative d'hydrocurage, jets arrière de propulsion."""
    faisceaux = ""
    if jets:
        for dy, l in ((-1, 132), (0, 156), (1, 132)):
            faisceaux += (f'<path d="M-74 {dy*14} L{-74-l} {dy*54}" stroke="{BLEU_300}" '
                          f'stroke-width="6" stroke-linecap="round" opacity=".85"/>')
            faisceaux += (f'<path d="M-74 {dy*14} L{-74-l*0.7:.0f} {dy*38:.0f}" stroke="{BLANC}" '
                          f'stroke-width="2.5" stroke-linecap="round" opacity=".5"/>')
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      {faisceaux}
      <path d="M-78 -34 h96 l40 34 l-40 34 h-96 z" fill="url(#inox)"/>
      <path d="M-78 -34 h96 l40 34 l-40 34 h-96 z" fill="none" stroke="#7c8ba1" stroke-width="3"/>
      <rect x="-104" y="-22" width="30" height="44" rx="10" fill="url(#orange)"/>
      <circle cx="18" cy="0" r="9" fill="#1e293b"/>
      <path d="M-104 0 h-52" stroke="#0b1220" stroke-width="21" stroke-linecap="round"/>
      <path d="M-104 0 h-52" stroke="{BLEU_500}" stroke-width="6" stroke-linecap="round" opacity=".45"/>
    </g>"""


def amas(x, y, rx=54, ry=42, sombre=False):
    """Amas obstruant, contour irrégulier calculé (jamais deux fois le même)."""
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        r = 1 + 0.20 * math.sin(3.7 * a + 1.1) + 0.12 * math.sin(6.3 * a)
        pts.append((x + rx * r * math.cos(a), y + ry * r * math.sin(a)))
    d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts) + " Z"
    base = "#4a3f31" if sombre else "#8a7355"
    clair = "#5e5140" if sombre else "#a58f6d"
    return (f'<path d="{d}" fill="{base}"/>'
            f'<path d="{d}" fill="{clair}" opacity=".55" transform="translate(-6,-7) scale(.82)" '
            f'transform-origin="{x:.0f} {y:.0f}"/>'
            f'<circle cx="{x+rx*0.35:.0f}" cy="{y-ry*0.3:.0f}" r="{rx*0.13:.0f}" fill="#3f362a" opacity=".8"/>'
            f'<circle cx="{x-rx*0.4:.0f}" cy="{y+ry*0.25:.0f}" r="{rx*0.10:.0f}" fill="#3f362a" opacity=".8"/>')


def hud(x, y, libelle, point="#f87171"):
    """Incrustation type moniteur d'inspection."""
    largeur = 30 + len(libelle) * 9.4
    return (f'<g transform="translate({x:.0f},{y:.0f})">'
            f'<rect width="{largeur:.0f}" height="44" rx="12" fill="rgba(255,255,255,.09)" '
            f'stroke="rgba(255,255,255,.20)" stroke-width="1.6"/>'
            f'<circle cx="22" cy="22" r="6.5" fill="{point}"/>'
            f'{texte(38, 28, libelle, 17, 600, "#e2e8f0")}</g>')


# ---------------------------------------------------------------------------
# Famille 2 — coupes techniques
# ---------------------------------------------------------------------------

def terrain(w, h, y_surface, herbe=True):
    """Terrain naturel en coupe : herbe, terre hachurée, lit de gravier."""
    bande = f'<rect x="0" y="{y_surface-13:.0f}" width="{w}" height="13" fill="#7fb069"/>' if herbe else ""
    return (f'<rect x="0" y="{y_surface:.0f}" width="{w}" height="{h-y_surface:.0f}" fill="url(#terre)"/>'
            + bande +
            f'<path d="M0 {y_surface:.0f} H{w}" stroke="{TERRE_F}" stroke-width="3"/>')


def dalle(w, y, hauteur=26):
    """Dalle béton en coupe."""
    return (f'<rect x="0" y="{y:.0f}" width="{w}" height="{hauteur}" fill="url(#beton)"/>'
            f'<path d="M0 {y:.0f} H{w}" stroke="#94a3b8" stroke-width="2.5"/>')


def canalisation(x1, y1, x2, y2, diametre=64, remplissage=0.35, paroi=9):
    """
    Canalisation en coupe longitudinale, quelconque en pente.

    Épaisseur de paroi constante et lame d'eau parallèle au radier : ce sont
    ces deux détails qui font qu'un tuyau incliné se lit comme un tuyau et
    non comme un rectangle penché.
    """
    dx, dy = x2 - x1, y2 - y1
    lg = math.hypot(dx, dy) or 1
    nx, ny = -dy / lg, dx / lg          # normale unitaire
    r = diametre / 2

    def dec(x, y, k):
        return x + nx * k, y + ny * k

    a1, b1 = dec(x1, y1, -r); a2, b2 = dec(x2, y2, -r)
    a3, b3 = dec(x2, y2, r);  a4, b4 = dec(x1, y1, r)
    ext = f"M{a1:.1f} {b1:.1f} L{a2:.1f} {b2:.1f} L{a3:.1f} {b3:.1f} L{a4:.1f} {b4:.1f} Z"

    i1, j1 = dec(x1, y1, -r + paroi); i2, j2 = dec(x2, y2, -r + paroi)
    i3, j3 = dec(x2, y2, r - paroi);  i4, j4 = dec(x1, y1, r - paroi)
    inte = f"M{i1:.1f} {j1:.1f} L{i2:.1f} {j2:.1f} L{i3:.1f} {j3:.1f} L{i4:.1f} {j4:.1f} Z"

    eau = ""
    if remplissage > 0:
        hs = r - paroi - 2 * (r - paroi) * remplissage
        e1, f1 = dec(x1, y1, hs); e2, f2 = dec(x2, y2, hs)
        eau = (f'<path d="M{e1:.1f} {f1:.1f} L{e2:.1f} {f2:.1f} L{i3:.1f} {j3:.1f} '
               f'L{i4:.1f} {j4:.1f} Z" fill="url(#eau)" opacity=".9"/>')

    return (f'<path d="{ext}" fill="url(#paroi)" stroke="#7c8ba1" stroke-width="2.5"/>'
            f'<path d="{inte}" fill="#16202e"/>{eau}')


def regard(cx, y_sol, largeur=180, profondeur=190, ouvert=True):
    """Regard de visite maçonné, en coupe, tampon relevé sur le côté."""
    l2 = largeur / 2
    tampon = ""
    if ouvert:
        tampon = (f'<g transform="translate({cx+largeur*0.92:.0f},{y_sol-22:.0f}) rotate(-15)">'
                  f'<rect x="-62" y="-11" width="124" height="22" rx="8" fill="url(#inox)" '
                  f'stroke="#7c8ba1" stroke-width="2"/>'
                  f'<circle cx="0" cy="0" r="8" fill="{NUIT_700}"/></g>')
    else:
        tampon = (f'<rect x="{cx-l2-14:.0f}" y="{y_sol-16:.0f}" width="{largeur+28:.0f}" '
                  f'height="18" rx="6" fill="url(#inox)" stroke="#7c8ba1" stroke-width="2"/>')
    return (f'<rect x="{cx-l2-16:.0f}" y="{y_sol:.0f}" width="{largeur+32:.0f}" '
            f'height="{profondeur:.0f}" rx="8" fill="url(#beton)" stroke="#8b98a9" stroke-width="2.5"/>'
            f'<rect x="{cx-l2:.0f}" y="{y_sol:.0f}" width="{largeur:.0f}" '
            f'height="{profondeur-16:.0f}" fill="#16202e"/>'
            f'<rect x="{cx-l2:.0f}" y="{y_sol+profondeur-72:.0f}" width="{largeur:.0f}" '
            f'height="56" fill="url(#eau)" opacity=".92"/>'
            f'<rect x="{cx-l2:.0f}" y="{y_sol+profondeur-72:.0f}" width="{largeur:.0f}" '
            f'height="5" fill="{BLEU_300}" opacity=".7"/>'
            + tampon)


def maison(x, y_sol, l=250, hauteur=210):
    """Pignon de maison en coupe : mur, toiture, ouverture."""
    return (f'<path d="M{x-l/2-26:.0f} {y_sol-hauteur:.0f} L{x:.0f} {y_sol-hauteur-88:.0f} '
            f'L{x+l/2+26:.0f} {y_sol-hauteur:.0f} Z" fill="#94a3b8"/>'
            f'<path d="M{x-l/2-26:.0f} {y_sol-hauteur:.0f} L{x:.0f} {y_sol-hauteur-88:.0f} '
            f'L{x+l/2+26:.0f} {y_sol-hauteur:.0f} Z" fill="none" stroke="#7c8ba1" stroke-width="3"/>'
            f'<rect x="{x-l/2:.0f}" y="{y_sol-hauteur:.0f}" width="{l:.0f}" height="{hauteur:.0f}" '
            f'fill="#eef2f7" stroke="#c3cdd9" stroke-width="3"/>'
            f'<rect x="{x-l/2+30:.0f}" y="{y_sol-hauteur+38:.0f}" width="64" height="76" rx="5" '
            f'fill="{BLEU_200}" stroke="#c3cdd9" stroke-width="3"/>'
            f'<rect x="{x+18:.0f}" y="{y_sol-hauteur+38:.0f}" width="64" height="76" rx="5" '
            f'fill="{BLEU_200}" stroke="#c3cdd9" stroke-width="3"/>')


def cuvette(x, y_sol, e=1.0):
    """Cuvette de WC en coupe : réservoir, siphon en S, garde d'eau."""
    return f"""
    <g transform="translate({x:.0f},{y_sol:.0f}) scale({e:.3f})" filter="url(#ombreDouce)">
      <rect x="-70" y="-286" width="140" height="104" rx="14" fill="url(#ceramique)" stroke="#c3cdd9" stroke-width="3"/>
      <rect x="-52" y="-268" width="104" height="58" rx="6" fill="url(#eau)" opacity=".5"/>
      <rect x="-22" y="-300" width="44" height="16" rx="8" fill="#c3cdd9"/>
      <path d="M-78 -182 h156 q10 0 8 14 l-10 46 q-4 16 -22 16 h-108 q-18 0 -22 -16 l-10 -46 q-2 -14 8 -14 z"
            fill="url(#ceramique)" stroke="#c3cdd9" stroke-width="3"/>
      <ellipse cx="0" cy="-176" rx="76" ry="24" fill="{BLANC}" stroke="#c3cdd9" stroke-width="3"/>
      <ellipse cx="0" cy="-172" rx="58" ry="16" fill="url(#eau)"/>
      <path d="M-46 -106 q6 62 46 68 q40 -6 46 -68 z" fill="url(#ceramique)" stroke="#c3cdd9" stroke-width="3"/>
      <path d="M0 -132 q-46 22 -32 62 q14 40 62 26" fill="none" stroke="#cbd5e1" stroke-width="26"/>
      <path d="M0 -132 q-46 22 -32 62 q14 40 62 26" fill="none" stroke="url(#eau)" stroke-width="14" opacity=".85"/>
      <ellipse cx="0" cy="0" rx="58" ry="12" fill="#cbd5e1"/>
    </g>"""


def siphon_evier(x, y, e=1.0, bouche=False):
    """Plan de travail, cuve d'évier et siphon en S sous l'appareil."""
    obstruction = amas(x - 4 * e, y + 150 * e, 30 * e, 20 * e) if bouche else ""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <rect x="-250" y="-26" width="500" height="28" rx="6" fill="#e8eef4" stroke="#c3cdd9" stroke-width="3"/>
      <path d="M-160 2 h320 v128 q0 16 -16 16 h-288 q-16 0 -16 -16 z" fill="url(#inox)"/>
      <path d="M-146 16 h292 v104 q0 10 -10 10 h-272 q-10 0 -10 -10 z" fill="#b6c2d1"/>
      <path d="M-146 74 h292 v46 q0 10 -10 10 h-272 q-10 0 -10 -10 z" fill="url(#eau)" opacity=".9"/>
      <circle cx="0" cy="130" r="20" fill="#7c8ba1"/>
      <path d="M188 -26 v-96 q0 -26 -28 -26 h-46" fill="none" stroke="url(#inox)" stroke-width="16" stroke-linecap="round"/>
      <path d="M0 146 v56 q0 40 42 40 q42 0 42 -40 v-14 h96"
            fill="none" stroke="#9aa7b8" stroke-width="34" stroke-linecap="round"/>
      <path d="M0 146 v56 q0 40 42 40 q42 0 42 -40 v-14 h96"
            fill="none" stroke="#16202e" stroke-width="20" stroke-linecap="round"/>
      <path d="M6 200 q0 30 36 30 q36 0 36 -30" fill="none" stroke="{BLEU_500}" stroke-width="18" opacity=".8"/>
    </g>{obstruction}"""


def bac_graisses(x, y, e=1.0):
    """Bac à graisses en coupe : trois compartiments, flottant de graisse."""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <rect x="-240" y="-140" width="480" height="180" rx="14" fill="url(#beton)" stroke="#8b98a9" stroke-width="3"/>
      <rect x="-222" y="-124" width="444" height="150" rx="6" fill="#16202e"/>
      <rect x="-222" y="-70" width="444" height="96" fill="url(#eau)" opacity=".88"/>
      <rect x="-222" y="-84" width="444" height="20" fill="#e0cfa4"/>
      <rect x="-222" y="-90" width="444" height="8" fill="#f0e3c2"/>
      <g stroke="#8b98a9" stroke-width="8">
        <path d="M-84 -124 v120"/><path d="M84 -104 v130"/>
      </g>
      <g fill="url(#inox)" stroke="#7c8ba1" stroke-width="2">
        <rect x="-206" y="-156" width="120" height="18" rx="7"/>
        <rect x="86" y="-156" width="120" height="18" rx="7"/>
      </g>
      <path d="M-296 -40 h60" stroke="url(#paroi)" stroke-width="34" stroke-linecap="round"/>
      <path d="M-296 -40 h60" stroke="#16202e" stroke-width="18" stroke-linecap="round"/>
      <path d="M236 -6 h62" stroke="url(#paroi)" stroke-width="30" stroke-linecap="round"/>
      <path d="M236 -6 h62" stroke="#16202e" stroke-width="16" stroke-linecap="round"/>
    </g>"""


def fosse(x, y, e=1.0):
    """Fosse toutes eaux en coupe : deux compartiments, chapeau, ventilation."""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <path d="M-300 -110 h600 q30 0 30 30 v150 q0 34 -34 34 h-592 q-34 0 -34 -34 v-150 q0 -30 30 -30 z"
            fill="url(#beton)" stroke="#8b98a9" stroke-width="4"/>
      <path d="M-286 -94 h572 v168 q0 16 -16 16 h-540 q-16 0 -16 -16 z" fill="#16202e"/>
      <path d="M-286 -22 h572 v152 q0 16 -16 16 h-540 q-16 0 -16 -16 z" fill="url(#eau)" opacity=".9"/>
      <path d="M-286 -38 h572 v18 h-572 z" fill="#c7ae86"/>
      <path d="M-286 108 h572 v34 q0 16 -16 16 h-540 q-16 0 -16 -16 z" fill="#6b5c46" opacity=".85"/>
      <path d="M96 -94 v190" stroke="#8b98a9" stroke-width="10"/>
      <path d="M96 -30 v-30 h70" fill="none" stroke="#8b98a9" stroke-width="8"/>
      <g fill="url(#inox)" stroke="#7c8ba1" stroke-width="2">
        <rect x="-250" y="-128" width="132" height="20" rx="8"/>
        <rect x="130" y="-128" width="132" height="20" rx="8"/>
      </g>
      <path d="M-380 -50 h96" stroke="url(#paroi)" stroke-width="40" stroke-linecap="round"/>
      <path d="M-380 -50 h96" stroke="#16202e" stroke-width="22" stroke-linecap="round"/>
      <path d="M300 4 h90" stroke="url(#paroi)" stroke-width="36" stroke-linecap="round"/>
      <path d="M300 4 h90" stroke="#16202e" stroke-width="20" stroke-linecap="round"/>
    </g>"""


def receveur_douche(x, y, e=1.0):
    """Receveur de douche en coupe, bonde siphoïde et eau stagnante."""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <rect x="-260" y="-330" width="520" height="330" fill="url(#carrelage)"/>
      <rect x="-262" y="-334" width="524" height="334" fill="none" stroke="#d3dce6" stroke-width="4"/>
      <path d="M-270 0 h540 v34 q0 14 -14 14 h-512 q-14 0 -14 -14 z" fill="url(#ceramique)" stroke="#c3cdd9" stroke-width="3"/>
      <path d="M-240 0 h480 l-14 20 h-452 z" fill="#dbe4ee"/>
      <path d="M-236 -18 h472 v18 h-472 z" fill="url(#eau)" opacity=".85"/>
      <circle cx="0" cy="6" r="26" fill="url(#inox)" stroke="#7c8ba1" stroke-width="2"/>
      <circle cx="0" cy="6" r="14" fill="#16202e"/>
      <path d="M0 30 v40 q0 34 38 34 q38 0 38 -34 v-16 h86"
            fill="none" stroke="#9aa7b8" stroke-width="34" stroke-linecap="round"/>
      <path d="M0 30 v40 q0 34 38 34 q38 0 38 -34 v-16 h86"
            fill="none" stroke="#16202e" stroke-width="20" stroke-linecap="round"/>
      <path d="M112 -330 v244" stroke="url(#inox)" stroke-width="14" stroke-linecap="round"/>
      <path d="M112 -330 h-64" stroke="url(#inox)" stroke-width="14" stroke-linecap="round"/>
      <ellipse cx="42" cy="-324" rx="30" ry="10" fill="#b6c2d1"/>
      <g stroke="{BLEU_300}" stroke-width="4.5" stroke-linecap="round" opacity=".75">
        <path d="M22 -308 v54"/><path d="M42 -310 v72"/><path d="M62 -308 v54"/>
      </g>
    </g>"""


def baignoire(x, y, e=1.0):
    """Baignoire en coupe, remplie, avec vidage et siphon."""
    return f"""
    <g transform="translate({x:.0f},{y:.0f}) scale({e:.3f})">
      <rect x="-300" y="-320" width="600" height="240" fill="url(#carrelage)"/>
      <path d="M-260 -120 h520 q16 0 14 18 l-16 128 q-6 40 -46 40 h-424 q-40 0 -46 -40 l-16 -128 q-2 -18 14 -18 z"
            fill="url(#ceramique)" stroke="#c3cdd9" stroke-width="4"/>
      <path d="M-234 -94 h468 l-16 118 q-4 22 -30 22 h-376 q-26 0 -30 -22 z" fill="#e6edf4"/>
      <path d="M-224 -40 h448 l-10 64 q-4 22 -30 22 h-368 q-26 0 -30 -22 z" fill="url(#eau)" opacity=".92"/>
      <path d="M-224 -40 h448 v6 h-448 z" fill="{BLEU_200}" opacity=".8"/>
      <circle cx="-160" cy="60" r="16" fill="url(#inox)"/>
      <path d="M-160 76 v34 q0 30 34 30 q34 0 34 -30 v-14 h110"
            fill="none" stroke="#9aa7b8" stroke-width="30" stroke-linecap="round"/>
      <path d="M-160 76 v34 q0 30 34 30 q34 0 34 -30 v-14 h110"
            fill="none" stroke="#16202e" stroke-width="17" stroke-linecap="round"/>
      <path d="M-260 -120 v-72 q0 -20 22 -20 h40" fill="none" stroke="url(#inox)" stroke-width="14" stroke-linecap="round"/>
    </g>"""


# ---------------------------------------------------------------------------
# Les scènes
# ---------------------------------------------------------------------------

def sc_hero(w, h):
    """
    Coupe du réseau domestique. La ligne de sol est placée haut : le sujet est
    ce qui se passe SOUS terre, et c'est donc au sous-sol que revient les deux
    tiers du cadre.
    """
    y_sol = h * 0.31
    return (fond_clair(w, h)
            + maison(w * 0.19, y_sol, 300, 230)
            + terrain(w, h, y_sol)
            + f'<rect x="0" y="{h*0.86:.0f}" width="{w}" height="{h*0.14:.0f}" '
              f'fill="url(#gravier)" opacity=".5"/>'
            + canalisation(w * 0.19, y_sol + 132, w * 0.585, y_sol + 214, 74, .32)
            + regard(w * 0.665, y_sol, 190, 300)
            + canalisation(w * 0.745, y_sol + 268, w + 20, y_sol + 312, 74, .38)
            + buse(w * 0.42, y_sol + 180, 0.56)
            + amas(w * 0.535, y_sol + 210, 27, 21)
            + etiquette(w * 0.30, y_sol + 62, "Hydrocurage haute pression", (w * 0.42, y_sol + 172))
            + etiquette(w * 0.845, y_sol + 62, "Regard de visite", (w * 0.665, y_sol + 96))
            + cote(w * 0.19, h * 0.945, w * 0.665, h * 0.945, "réseau"))


def sc_materiel(w, h):
    """Le matériel d'intervention, cadré comme un plan produit."""
    return (fond_clair(w, h)
            + f'<ellipse cx="{w*0.5:.0f}" cy="{h*0.90:.0f}" rx="{w*0.38:.0f}" ry="24" '
              f'fill="{ARDOISE}" opacity=".18" filter="url(#flou12)"/>'
            # Enrouleur haute pression.
            + f'<g transform="translate({w*0.28:.0f},{h*0.42:.0f})">'
              f'<circle r="150" fill="none" stroke="{NUIT_800}" stroke-width="34"/>'
              f'<circle r="150" fill="none" stroke="{BLEU_500}" stroke-width="7" opacity=".45"/>'
              f'<circle r="122" fill="none" stroke="{NUIT_700}" stroke-width="10" opacity=".7"/>'
              f'<circle r="56" fill="url(#inox)" stroke="#7c8ba1" stroke-width="3"/>'
              f'<circle r="26" fill="url(#orange)"/><circle r="10" fill="{NUIT}"/>'
              f'<path d="M0 -150 A150 150 0 0 1 130 76" fill="none" stroke="{BLEU_400}" '
              f'stroke-width="11" opacity=".6" stroke-linecap="round"/></g>'
            # Flexible reliant l'enrouleur à la buse.
            + f'<path d="M{w*0.28+130:.0f} {h*0.42+76:.0f} C {w*0.50:.0f} {h*0.86:.0f}, '
              f'{w*0.58:.0f} {h*0.60:.0f}, {w*0.72:.0f} {h*0.70:.0f}" fill="none" '
              f'stroke="#0b1220" stroke-width="24" stroke-linecap="round"/>'
            + f'<path d="M{w*0.28+130:.0f} {h*0.42+76:.0f} C {w*0.50:.0f} {h*0.86:.0f}, '
              f'{w*0.58:.0f} {h*0.60:.0f}, {w*0.72:.0f} {h*0.70:.0f}" fill="none" '
              f'stroke="{BLEU_500}" stroke-width="6" stroke-linecap="round" opacity=".4"/>'
            + buse(w * 0.83, h * 0.70, 0.80, jets=False)
            + tete_camera(w * 0.70, h * 0.20, 0.80)
            + etiquette(w * 0.26, h * 0.78, "Enrouleur haute pression")
            + etiquette(w * 0.74, h * 0.05, "Caméra d'inspection")
            + etiquette(w * 0.86, h * 0.87, "Buse rotative"))


def sc_wc(w, h):
    y_sol = h * 0.84
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{y_sol:.0f}" fill="url(#carrelage)" opacity=".95"/>'
            + f'<rect x="0" y="{y_sol:.0f}" width="{w}" height="{h-y_sol:.0f}" fill="#dbe3ec"/>'
            + f'<path d="M0 {y_sol:.0f} H{w}" stroke="#c3cdd9" stroke-width="3"/>'
            + canalisation(w * 0.46, y_sol + 34, w + 20, y_sol + 52, 56, .34)
            + cuvette(w * 0.46, y_sol, 1.62)
            + amas(w * 0.435, y_sol - 150, 26, 19)
            + etiquette(w * 0.20, h * 0.30, "Garde d'eau", (w * 0.415, h * 0.415))
            + etiquette(w * 0.80, h * 0.60, "Bouchon dans le siphon", (w * 0.435, y_sol - 150)))


def sc_evier(w, h):
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{h*0.30:.0f}" fill="url(#carrelage)" opacity=".95"/>'
            + f'<rect x="0" y="{h*0.30:.0f}" width="{w}" height="{h*0.70:.0f}" fill="#eef3f8"/>'
            + f'<path d="M0 {h*0.30:.0f} H{w}" stroke="#d3dce6" stroke-width="3"/>'
            + canalisation(w * 0.72, h * 0.735, w + 20, h * 0.745, 42, .30)
            + siphon_evier(w * 0.42, h * 0.235, 1.42, bouche=True)
            + etiquette(w * 0.19, h * 0.72, "Siphon démontable")
            + etiquette(w * 0.80, h * 0.30, "Graisses figées", (w * 0.415, h * 0.735)))


def sc_douche(w, h):
    y_sol = h * 0.62
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{y_sol:.0f}" fill="url(#carrelage)" opacity=".95"/>'
            + f'<rect x="0" y="{y_sol:.0f}" width="{w}" height="{h-y_sol:.0f}" fill="#dde5ee"/>'
            + f'<path d="M0 {y_sol:.0f} H{w}" stroke="#c3cdd9" stroke-width="3"/>'
            + canalisation(w * 0.64, y_sol + 108, w + 20, y_sol + 120, 44, .30)
            + receveur_douche(w * 0.42, y_sol, 1.18)
            + amas(w * 0.52, y_sol + 52, 24, 16)
            + etiquette(w * 0.79, h * 0.42, "Cheveux et savon", (w * 0.52, y_sol + 52))
            + etiquette(w * 0.19, h * 0.88, "Bonde siphoïde"))


def sc_baignoire(w, h):
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{h*0.72:.0f}" fill="url(#carrelage)" opacity=".95"/>'
            + baignoire(w * 0.47, h * 0.60, 1.32)
            + f'<rect x="0" y="{h*0.86:.0f}" width="{w}" height="{h*0.14:.0f}" fill="#dbe3ec"/>'
            + f'<path d="M0 {h*0.86:.0f} H{w}" stroke="#c3cdd9" stroke-width="3"/>'
            + etiquette(w * 0.76, h * 0.20, "L'eau ne descend plus")
            + etiquette(w * 0.26, h * 0.93, "Siphon de vidage"))


def sc_cuisine(w, h):
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{h*0.30:.0f}" fill="url(#carrelage)" opacity=".95"/>'
            + siphon_evier(w * 0.28, h * 0.22, 1.02)
            + f'<rect x="0" y="{h*0.62:.0f}" width="{w}" height="{h*0.38:.0f}" fill="url(#gravier)" opacity=".55"/>'
            + f'<path d="M0 {h*0.62:.0f} H{w}" stroke="#a8a29e" stroke-width="3"/>'
            + canalisation(w * 0.335, h * 0.71, w * 0.52, h * 0.745, 46, .30)
            + bac_graisses(w * 0.72, h * 0.80, 0.78)
            + etiquette(w * 0.26, h * 0.545, "Évier de cuisine")
            + etiquette(w * 0.72, h * 0.42, "Bac à graisses", (w * 0.72, h * 0.66)))


def sc_canalisation(w, h):
    y = h * 0.55
    return (fond_clair(w, h)
            + f'<rect x="0" y="{h*0.18:.0f}" width="{w}" height="{h*0.82:.0f}" fill="url(#terre)" opacity=".55"/>'
            + f'<path d="M0 {h*0.18:.0f} H{w}" stroke="{TERRE_F}" stroke-width="3"/>'
            + f'<rect x="0" y="{y+70:.0f}" width="{w}" height="46" fill="url(#gravier)" opacity=".8"/>'
            + canalisation(-20, y - 8, w + 20, y + 26, 116, .30)
            + amas(w * 0.68, y + 18, 44, 30)
            + buse(w * 0.40, y + 8, 0.86)
            + etiquette(w * 0.68, h * 0.13, "Bouchon localisé", (w * 0.68, y + 12))
            + etiquette(w * 0.28, h * 0.87, "Buse rotative haute pression", (w * 0.40, y + 20))
            + cote(0, h * 0.30, w * 0.68, h * 0.30, "18,2 m"))


def sc_camera(w, h):
    cx, cy = w * 0.56, h * 0.50
    corps, rayons = tunnel(cx, cy, w * 0.44, h * 0.44, 28, .862,
                           fuite=(w * 0.72, h * 0.46), eau=0.20)
    return (fond_sombre(w, h)
            + anneau_entree(cx, cy, w * 0.44, h * 0.44, 30)
            + corps
            + f'<ellipse cx="{w*0.30:.0f}" cy="{cy:.0f}" rx="220" ry="180" fill="url(#lampe)"/>'
            + amas(w * 0.695, h * 0.475, 26, 20, sombre=True)
            + tete_camera(w * 0.28, cy + h * 0.02, 0.86)
            + hud(w * 0.045, h * 0.075, "Inspection · 12,4 m")
            + hud(w * 0.045, h * 0.855, "Contre-pente détectée", "#fbbf24"))


def sc_curage(w, h):
    cx, cy = w * 0.55, h * 0.50
    corps, _ = tunnel(cx, cy, w * 0.44, h * 0.44, 28, .862,
                      fuite=(w * 0.74, h * 0.48), eau=0.14,
                      teinte_proche="#4b5563", teinte_loin="#050a14")
    return (fond_sombre(w, h)
            + anneau_entree(cx, cy, w * 0.44, h * 0.44, 30)
            + corps
            # Dépôt encore en place sur la paroi, au-delà de la buse : une
            # couronne entre deux anneaux, pas une tache posée sur l'image.
            + f'<path fill-rule="evenodd" fill="#6b5c46" opacity=".82" d="'
              f'M{w*0.55+w*0.30:.0f} {h*0.49:.0f} '
              f'a{w*0.30:.0f} {h*0.30:.0f} 0 1 0 {-w*0.60:.0f} 0 '
              f'a{w*0.30:.0f} {h*0.30:.0f} 0 1 0 {w*0.60:.0f} 0 Z '
              f'M{w*0.57+w*0.235:.0f} {h*0.487:.0f} '
              f'a{w*0.235:.0f} {h*0.235:.0f} 0 1 0 {-w*0.47:.0f} 0 '
              f'a{w*0.235:.0f} {h*0.235:.0f} 0 1 0 {w*0.47:.0f} 0 Z"/>'
            + buse(w * 0.44, cy, 0.94)
            + hud(w * 0.045, h * 0.075, "Curage en cours")
            + hud(w * 0.045, h * 0.855, "150 bar", "#38bdf8"))


def sc_pompage(w, h):
    y_sol = h * 0.34
    return (fond_clair(w, h)
            + terrain(w, h, y_sol, herbe=False)
            + f'<rect x="0" y="{y_sol-26:.0f}" width="{w}" height="26" fill="url(#beton)"/>'
            + regard(w * 0.42, y_sol, 230, 300)
            + canalisation(-20, y_sol + 210, w * 0.30, y_sol + 224, 66, .34)
            + canalisation(w * 0.545, y_sol + 236, w + 20, y_sol + 250, 66, .28)
            # Flexible d'aspiration plongé jusqu'au fond.
            + f'<path d="M{w*0.42:.0f} {y_sol+250:.0f} V {y_sol-70:.0f} '
              f'C {w*0.42:.0f} {y_sol-150:.0f}, {w*0.72:.0f} {y_sol-160:.0f}, {w*0.84:.0f} {y_sol-96:.0f}" '
              f'fill="none" stroke="#0b1220" stroke-width="30" stroke-linecap="round"/>'
            + f'<path d="M{w*0.42:.0f} {y_sol+250:.0f} V {y_sol-70:.0f} '
              f'C {w*0.42:.0f} {y_sol-150:.0f}, {w*0.72:.0f} {y_sol-160:.0f}, {w*0.84:.0f} {y_sol-96:.0f}" '
              f'fill="none" stroke="{BLEU_500}" stroke-width="9" stroke-linecap="round" opacity=".45"/>'
            + f'<g transform="translate({w*0.42:.0f},{y_sol+250:.0f})">'
              f'<rect x="-26" y="-16" width="52" height="32" rx="10" fill="url(#orange)"/></g>'
            # Flèches de remontée du liquide.
            + "".join(f'<path d="M{w*0.42:.0f} {y_sol+180-i*70:.0f} v-40" stroke="{BLEU_300}" '
                      f'stroke-width="5" opacity=".8" marker-end="url(#fl)"/>' for i in range(3))
            + '<defs><marker id="fl" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" '
              f'markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{BLEU_300}"/></marker></defs>'
            + etiquette(w * 0.80, h * 0.14, "Aspiration", (w * 0.60, y_sol - 128))
            + etiquette(w * 0.18, h * 0.66, "Regard plein", (w * 0.42, y_sol + 210)))


def sc_assainissement(w, h):
    y_sol = h * 0.30
    return (fond_clair(w, h)
            + maison(w * 0.13, y_sol, 210, 190)
            + terrain(w, h, y_sol)
            + canalisation(w * 0.13, y_sol + 70, w * 0.34, y_sol + 92, 56, .30)
            + fosse(w * 0.56, h * 0.62, 0.86)
            + canalisation(w * 0.78, y_sol + 226, w + 20, y_sol + 250, 52, .24)
            + f'<path d="M{w*0.616:.0f} {y_sol+112:.0f} V {y_sol-70:.0f}" stroke="#8b98a9" stroke-width="11"/>'
            + f'<path d="M{w*0.616:.0f} {y_sol-70:.0f} l-16 -22 h32 z" fill="#8b98a9"/>'
            + etiquette(w * 0.615, y_sol - 104, "Ventilation")
            + etiquette(w * 0.30, h * 0.90, "Fosse toutes eaux", (w * 0.50, h * 0.72))
            + etiquette(w * 0.88, h * 0.16, "Épandage"))


def sc_professionnel(w, h):
    return (fond_clair(w, h)
            + f'<rect x="0" y="0" width="{w}" height="{h*0.40:.0f}" fill="url(#carrelage)" opacity=".9"/>'
            + f'<g transform="translate({w*0.20:.0f},{h*0.30:.0f})" filter="url(#ombreDouce)">'
              f'<rect x="-150" y="-120" width="300" height="150" rx="10" fill="url(#inox)" '
              f'stroke="#7c8ba1" stroke-width="3"/>'
              f'<rect x="-134" y="-104" width="128" height="112" rx="6" fill="#4b5563"/>'
              f'<rect x="6" y="-104" width="128" height="112" rx="6" fill="#4b5563"/>'
              f'<circle cx="-70" cy="-48" r="19" fill="{ORANGE}" opacity=".9"/>'
              f'<circle cx="70" cy="-48" r="19" fill="{BLEU_400}" opacity=".8"/>'
              f'<rect x="-150" y="30" width="300" height="14" rx="6" fill="#94a3b8"/></g>'
            + f'<rect x="0" y="{h*0.52:.0f}" width="{w}" height="{h*0.48:.0f}" fill="url(#gravier)" opacity=".6"/>'
            + f'<path d="M0 {h*0.52:.0f} H{w}" stroke="#a8a29e" stroke-width="3"/>'
            + canalisation(w * 0.20, h * 0.44, w * 0.20, h * 0.62, 48, .26)
            + bac_graisses(w * 0.62, h * 0.72, 0.78)
            + canalisation(w * 0.245, h * 0.615, w * 0.395, h * 0.635, 48, .30)
            + etiquette(w * 0.20, h * 0.075, "Cuisine professionnelle")
            + etiquette(w * 0.62, h * 0.28, "Bac à graisses", (w * 0.62, h * 0.60)))


def sc_exterieure(w, h):
    y_sol = h * 0.36
    return (fond_clair(w, h)
            + maison(w * 0.14, y_sol, 230, 200)
            + terrain(w, h, y_sol)
            + canalisation(w * 0.14, y_sol + 84, w * 0.50, y_sol + 122, 62, .30)
            + regard(w * 0.565, y_sol, 170, 190)
            + canalisation(w * 0.63, y_sol + 150, w + 20, y_sol + 182, 62, .34)
            # Racines traversant la paroi : la cause la plus fréquente à l'extérieur.
            + f'<g stroke="#7a5c3b" stroke-width="7" fill="none" stroke-linecap="round" opacity=".95">'
              f'<path d="M{w*0.83:.0f} {y_sol+96:.0f} q-26 42 -14 78"/>'
              f'<path d="M{w*0.83:.0f} {y_sol+118:.0f} q-46 22 -60 52"/>'
              f'<path d="M{w*0.845:.0f} {y_sol+130:.0f} q10 34 -8 46"/></g>'
            + amas(w * 0.815, y_sol + 178, 30, 20)
            + f'<g transform="translate({w*0.86:.0f},{y_sol-56:.0f})">'
              f'<path d="M0 0 v-38" stroke="#7a5c3b" stroke-width="12"/>'
              f'<circle cx="0" cy="-58" r="40" fill="#7fb069" opacity=".9"/>'
              f'<circle cx="-26" cy="-40" r="26" fill="#8fbf78" opacity=".9"/>'
              f'<circle cx="26" cy="-42" r="24" fill="#6fa05c" opacity=".9"/></g>'
            + etiquette(w * 0.30, h * 0.90, "Canalisation enterrée")
            + etiquette(w * 0.60, y_sol - 48, "Regard", (w * 0.565, y_sol + 24))
            + etiquette(w * 0.80, h * 0.93, "Racines", (w * 0.815, y_sol + 172)))


def sc_urgence(w, h):
    cx, cy = w * 0.54, h * 0.50
    corps, _ = tunnel(cx, cy, w * 0.44, h * 0.44, 26, .868,
                      fuite=(w * 0.70, h * 0.47), eau=0.62,
                      teinte_proche="#4a3f31", teinte_loin="#0a0703")
    return (fond_sombre(w, h, chaud=True)
            + anneau_entree(cx, cy, w * 0.44, h * 0.44, 30)
            + corps
            + amas(w * 0.60, h * 0.42, 60, 40, sombre=True)
            # Flèche de refoulement : le sens de l'eau s'inverse.
            + f'<g transform="translate({w*0.30:.0f},{h*0.50:.0f})">'
              f'<path d="M120 0 H-40" stroke="{ORANGE}" stroke-width="13" stroke-linecap="round"/>'
              f'<path d="M-72 0 l44 -30 v60 z" fill="{ORANGE}"/></g>'
            + hud(w * 0.045, h * 0.075, "Refoulement", "#f97316")
            + f'<g transform="translate({w*0.80:.0f},{h*0.20:.0f})">'
              f'<path d="M0 -54 L50 38 H-50 Z" fill="url(#orange)" stroke="#fdba74" '
              f'stroke-width="4" stroke-linejoin="round"/>'
              f'<rect x="-5.5" y="-26" width="11" height="36" rx="5.5" fill="{NUIT}"/>'
              f'<circle cx="0" cy="22" r="6" fill="{NUIT}"/></g>')


# ---------------------------------------------------------------------------
# Registre
# ---------------------------------------------------------------------------

VISUELS = [
    ("hero-debouchage-canalisation", 1120, 840, sc_hero,
     "Coupe d'un réseau d'assainissement domestique : canalisation enterrée reliant "
     "la maison au regard de visite, buse d'hydrocurage en action sur un bouchon"),
    ("materiel-degorgement", 960, 720, sc_materiel,
     "Matériel professionnel de dégorgement : enrouleur haute pression, flexible et "
     "caméra d'inspection de canalisation"),
    ("debouchage-wc", 960, 720, sc_wc,
     "Coupe d'un WC montrant la garde d'eau du siphon et l'emplacement d'un bouchon"),
    ("debouchage-evier", 960, 720, sc_evier,
     "Coupe d'un évier et de son siphon en S obstrué par des graisses figées"),
    ("debouchage-douche", 960, 720, sc_douche,
     "Coupe d'un receveur de douche dont la bonde siphoïde est obstruée par des cheveux"),
    ("debouchage-baignoire", 960, 720, sc_baignoire,
     "Coupe d'une baignoire remplie d'eau stagnante et de son siphon de vidage"),
    ("debouchage-cuisine", 960, 720, sc_cuisine,
     "Coupe d'une installation de cuisine : évier, siphon et bac à graisses raccordés au réseau"),
    ("debouchage-canalisation", 1120, 700, sc_canalisation,
     "Coupe d'une canalisation enterrée obstruée, buse rotative haute pression progressant "
     "vers le bouchon"),
    ("inspection-camera-canalisation", 1120, 700, sc_camera,
     "Vue depuis l'intérieur d'une canalisation inspectée par caméra motorisée, "
     "paroi éclairée et lame d'eau au radier"),
    ("curage-canalisation", 1120, 700, sc_curage,
     "Vue depuis l'intérieur d'une canalisation en cours de curage haute pression, "
     "dépôt décollé de la paroi"),
    ("pompage-canalisation", 960, 720, sc_pompage,
     "Coupe d'un regard de visite rempli, flexible d'aspiration plongé jusqu'au fond pour le pompage"),
    ("assainissement", 1120, 700, sc_assainissement,
     "Coupe d'une installation d'assainissement individuel : maison, fosse toutes eaux "
     "à deux compartiments, ventilation et départ vers l'épandage"),
    ("debouchage-professionnel", 960, 720, sc_professionnel,
     "Coupe d'une installation de cuisine professionnelle raccordée à un bac à graisses enterré"),
    ("canalisation-exterieure", 960, 720, sc_exterieure,
     "Coupe d'une canalisation extérieure enterrée traversée par des racines d'arbre, "
     "avec son regard de visite"),
    ("urgence-degorgement", 1120, 700, sc_urgence,
     "Vue intérieure d'une canalisation en refoulement : conduite pleine et bouchon "
     "bloquant l'écoulement"),
]

# Images de partage (Open Graph). Un SVG n'est pas affiché par les réseaux
# sociaux et WebP reste inégalement pris en charge : ces images-là sont donc
# des JPEG 1200×630, la seule combinaison acceptée partout.
# og-default.jpg n'est PAS produit ici : c'est une photographie, écrite par
# scripts/preparer-photos.py. Deux scripts pour un même fichier, et c'est le
# dernier exécuté qui gagne — donc le résultat dépend de l'ordre.
OG = [
    ("og-degorgement", sc_hero),
    ("og-debouchage-canalisation", sc_canalisation),
    ("og-canalisation-exterieure", sc_exterieure),
    ("og-curage-canalisation", sc_curage),
    ("og-inspection-camera", sc_camera),
    ("og-pompage", sc_pompage),
    ("og-assainissement", sc_assainissement),
    ("og-debouchage-wc", sc_wc),
    ("og-debouchage-evier", sc_evier),
    ("og-debouchage-douche", sc_douche),
    ("og-urgence", sc_urgence),
    ("og-professionnel", sc_professionnel),
    ("og-materiel", sc_materiel),
]
OG_L, OG_H = 1200, 630


def cartouche_og(w, h, sombre=False):
    """Bandeau de marque des images de partage."""
    fond = "rgba(15,23,42,.88)" if not sombre else "rgba(15,23,42,.82)"
    return (f'<g transform="translate({w*0.045:.0f},{h-142:.0f})">'
            f'<rect width="560" height="104" rx="22" fill="{fond}"/>'
            f'<g transform="translate(30,22)">'
            f'<rect width="60" height="60" rx="17" fill="{BLEU_600}"/>'
            f'<path d="M30 12c9.6 13.3 14 19.7 14 25.8a14 14 0 0 1-28 0c0-6.1 4.4-12.5 14-25.8z" '
            f'fill="none" stroke="#fff" stroke-width="4.4" stroke-linejoin="round"/></g>'
            f'{texte(108, 58, "Dégorgement Richard", 33, 800, "#ffffff")}'
            f'{texte(108, 86, "Débouchage · Curage · Assainissement", 19, 550, "#bae6fd")}'
            f'</g>')


FACTEUR = 2   # rendu au double, réduit ensuite : bords nets sur écran Retina


def svg_scene(fn, w, h) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{defs()}{fn(w, h)}</svg>')


async def rendre():
    SORTIE.mkdir(parents=True, exist_ok=True)
    resultats = []

    async with async_playwright() as p:
        navigateur = await p.chromium.launch(executable_path=CHROMIUM)
        for nom, w, h, fn, alt in VISUELS:
            page = await navigateur.new_page(
                viewport={"width": w * FACTEUR, "height": h * FACTEUR},
                device_scale_factor=1,
            )
            # Le viewBox reste inchangé : doubler width/height suffit à rendre
            # la scène au double, sans recalculer un seul tracé.
            svg = svg_scene(fn, w, h)
            svg = svg.replace('width="%d" height="%d"' % (w, h),
                              'width="%d" height="%d"' % (w * FACTEUR, h * FACTEUR), 1)
            await page.set_content('<body style="margin:0;background:#fff">' + svg + '</body>')
            png = await page.screenshot(type="png")
            await page.close()

            image = Image.open(io.BytesIO(png)).convert("RGB")
            image = image.resize((w, h), Image.LANCZOS)
            chemin = SORTIE / f"{nom}.webp"
            image.save(chemin, "WEBP", quality=84, method=6)
            resultats.append((nom, w, h, chemin.stat().st_size, alt))
            print(f"  ✓ {nom}.webp  {w}×{h}  {chemin.stat().st_size/1024:.0f} Ko")

        # Images de partage : mêmes scènes, format imposé par les réseaux.
        for nom, fn in OG:
            page = await navigateur.new_page(
                viewport={"width": OG_L, "height": OG_H}, device_scale_factor=1)
            corps = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{OG_L}" '
                     f'height="{OG_H}" viewBox="0 0 {OG_L} {OG_H}">{defs()}'
                     f'{fn(OG_L, OG_H)}{cartouche_og(OG_L, OG_H)}</svg>')
            await page.set_content('<body style="margin:0">' + corps + '</body>')
            png = await page.screenshot(type="png")
            await page.close()
            image = Image.open(io.BytesIO(png)).convert("RGB")
            chemin = SORTIE.parent / "partage" / f"{nom}.jpg"
            image.save(chemin, "JPEG", quality=82, optimize=True, progressive=True)
            print(f"  ✓ {nom}.jpg  {OG_L}×{OG_H}  {chemin.stat().st_size/1024:.0f} Ko")

        await navigateur.close()

    return resultats


def ecrire_manifeste(resultats):
    lignes = [
        "# Bibliothèque de visuels",
        "",
        "Fichiers produits par `scripts/generer-visuels.py`. **Ne pas les retoucher",
        "à la main** : le script est la source, une retouche serait perdue au",
        "prochain rendu.",
        "",
        "## Origine et licence",
        "",
        "Ces images sont des **illustrations originales**, décrites en SVG dans le",
        "script puis rendues en WebP par Chromium. Elles ne proviennent d'aucune",
        "banque d'images : aucun filigrane, aucun logo tiers, aucune licence à",
        "respecter au-delà de celle du dépôt.",
        "",
        "Deux familles seulement, pour que l'ensemble se tienne :",
        "",
        "1. **la coupe technique** — le réseau vu en section, comme sur un plan",
        "   d'exécution (terrain, ouvrage, canalisation, pente, annotations) ;",
        "2. **l'intérieur de canalisation** — la vue du moniteur d'inspection,",
        "   avec point de fuite calculé et lame d'eau suivant la perspective.",
        "",
        "## Remplacer une illustration par une photographie",
        "",
        "Déposer un fichier WebP de **mêmes nom et dimensions** dans ce dossier",
        "suffit : le HTML référence les fichiers par leur nom et porte déjà",
        "`width`, `height`, `loading`, `decoding` et `alt`. Vérifier seulement que",
        "la photographie retenue est libre de droits pour un usage commercial et",
        "que le texte alternatif la décrit toujours correctement.",
        "",
        "## Contenu",
        "",
        "| Fichier | Dimensions | Poids | Texte alternatif |",
        "|---|---|---|---|",
    ]
    for nom, w, h, taille, alt in resultats:
        lignes.append(f"| `{nom}.webp` | {w}×{h} | {taille/1024:.0f} Ko | {alt} |")
    lignes.append("")
    (SORTIE / "README.md").write_text("\n".join(lignes), encoding="utf-8")


if __name__ == "__main__":
    if not Path(CHROMIUM).exists() and not shutil.which("chromium"):
        sys.exit("Chromium introuvable : impossible de rendre les visuels.")
    print("Rendu de la bibliothèque de visuels…")
    res = asyncio.run(rendre())
    ecrire_manifeste(res)
    total = sum(r[3] for r in res)
    print(f"\n{len(res)} visuels · {total/1024:.0f} Ko au total · {SORTIE}")
