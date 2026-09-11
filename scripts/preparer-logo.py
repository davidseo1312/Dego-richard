#!/usr/bin/env python3
"""
Prépare le logo de l'entreprise pour le web.

    logo-source/logo-original.webp  ->  static/assets/img/logo/*.png|webp
                                    ->  static/assets/img/favicon*, icone-*.png

Ce que fait le script
---------------------
1. Il détoure le logo. Le fichier fourni est un aplat sur fond blanc : posé
   tel quel dans l'en-tête, le blanc du fichier ne se distingue pas du blanc
   de la page tant que rien ne bouge — mais il réapparaît au moindre fond
   coloré, et il empêche tout contre-emploi. Le fond est donc retiré par
   « division par le blanc » : chaque pixel garde sa couleur d'origine une
   fois recomposé sur blanc, y compris ses bords lissés.

2. Il produit une variante claire pour le pied de page. Le mot « DEBOUCHEUR »
   est en bleu nuit (#0d1d28) : sur le bleu nuit du pied de page, il
   disparaît. La variante bascule cette encre-là en blanc et laisse le cyan
   intact — c'est le logo, pas une recoloration arbitraire.

3. Il découpe le monogramme et en tire les favicons. Le repère de marque de
   l'onglet devient celui de l'entreprise, au lieu de la goutte dessinée
   faute de mieux au démarrage du projet.

Les deux encres du fichier fourni tombent déjà sur la palette du site :
#0d1d28 contre --color-dark #0f172a, et #00abf3 entre --color-accent et
--color-primary. Rien n'a donc été retouché.

Dépendances : Pillow.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "logo-source" / "logo-original.webp"
SORTIE = RACINE / "static" / "assets" / "img" / "logo"
ICONES = RACINE / "static" / "assets" / "img"

# Largeurs servies. L'en-tête affiche le logo à 46 px de haut, soit ~159 px de
# large ; 320 et 480 couvrent les écrans à 2× et 3× sans jamais rien
# télécharger d'inutile.
LARGEURS = [320, 480]


def detourer(im: Image.Image) -> Image.Image:
    """Retire le fond blanc en conservant le lissage des bords.

    Pour un aplat sur blanc, la couche alpha se déduit du canal le plus
    sombre : un pixel blanc pur est transparent, une encre pleine est opaque,
    et un pixel de bord est partiellement opaque. La couleur est ensuite
    « dé-prémultipliée », faute de quoi toutes les encres seraient éclaircies
    par le blanc qu'elles contiennent encore.
    """
    im = im.convert("RGB")
    px = list(im.getdata())
    sortie = []
    for r, v, b in px:
        a = 255 - min(r, v, b)
        # Le fichier fourni est un export compressé : son fond « blanc » est
        # en réalité constellé de 253 et de 254, que la formule ci-dessus
        # traduirait en un voile d'opacité 1 à 2 sur toute la surface. Les
        # deux extrémités sont donc ramenées au franc.
        if a <= 18:
            sortie.append((0, 0, 0, 0))
            continue
        if a >= 240:
            a = 255
        f = 255 - a
        sortie.append((
            max(0, min(255, round((r - f) * 255 / a))),
            max(0, min(255, round((v - f) * 255 / a))),
            max(0, min(255, round((b - f) * 255 / a))),
            a,
        ))
    hors = Image.new("RGBA", im.size)
    hors.putdata(sortie)
    return hors


def recadrer(im: Image.Image) -> Image.Image:
    """Supprime la marge du fichier fourni.

    Le recadrage se fait APRÈS le détourage, sur la couche alpha : sur l'image
    d'origine il faudrait comparer au blanc, et cette comparaison rendrait un
    résultat faux dès que l'image est déjà transparente — le noir des pixels
    vides passerait alors pour du contenu.
    """
    boite = im.getchannel("A").point(lambda p: 255 if p > 8 else 0).getbbox()
    return im.crop(boite)


# Les deux encres réelles du fichier, relevées sur les aplats.
NUIT, CYAN = (13, 29, 40), (0, 171, 243)


def aplatir(im: Image.Image) -> Image.Image:
    """Ramène chaque pixel à l'une des deux encres du logo.

    Le fichier fourni est un export compressé : ses aplats sont constellés de
    variantes à un ou deux points d'écart, invisibles à l'œil mais qui
    empêchent toute compression sans perte — 41 Ko de PNG pour un logo à deux
    couleurs. En ramenant chaque pixel à son encre et en ne laissant le lissage
    que dans la couche alpha, le même fichier tombe sous les 5 Ko, et les
    contours y gagnent en netteté.
    """
    hors = Image.new("RGBA", im.size)
    hors.putdata([(0, 0, 0, 0) if not a else (*(CYAN if v >= 110 else NUIT), a)
                  for r, v, b, a in im.getdata()])
    return hors


def variante_claire(im: Image.Image) -> Image.Image:
    """L'encre sombre passe au blanc ; le cyan ne bouge pas.

    Le tri se fait sur le canal vert : 29 pour le bleu nuit, 171 pour le cyan.
    Aucune autre encre n'existe dans ce fichier, le seuil est donc franc.
    """
    px = list(im.getdata())
    hors = Image.new("RGBA", im.size)
    hors.putdata([(255, 255, 255, a) if a and v < 110 else (r, v, b, a)
                  for r, v, b, a in px])
    return hors


def monogramme(im: Image.Image) -> Image.Image:
    """Isole le pictogramme, à gauche du bloc de texte.

    La coupure se trouve dans la colonne vide la plus large du premier tiers
    de l'image : c'est la gouttière entre le monogramme et « DEBOUCHEUR ».
    """
    L, H = im.size
    alpha = im.getchannel("A")
    vides = [x for x in range(L // 2)
             if max(alpha.crop((x, 0, x + 1, H)).getdata()) < 8]
    coupure, debut, meilleure = L // 3, None, (0, 0)
    for x in vides + [10 ** 9]:
        if debut is None:
            debut, precedent = x, x
        elif x == precedent + 1:
            precedent = x
        else:
            if precedent - debut > meilleure[1] - meilleure[0]:
                meilleure = (debut, precedent)
            debut, precedent = x, x
    if meilleure[1] > meilleure[0]:
        coupure = (meilleure[0] + meilleure[1]) // 2
    mono = im.crop((0, 0, coupure, H))
    boite = mono.getchannel("A").point(lambda p: 255 if p > 8 else 0).getbbox()
    return mono.crop(boite)


def carre(im: Image.Image, cote: int, marge: float = .10,
          fond=(255, 255, 255, 255)) -> Image.Image:
    """Le monogramme centré dans un carré, avec sa marge.

    Le fond est opaque par défaut, et ce n'est pas un détail : iOS compose
    l'icône d'écran d'accueil sur du noir, et une icône transparente y
    apparaît comme un aplat sombre. Android, lui, rogne jusqu'à 20 % de chaque
    bord des icônes « maskable » — d'où la marge plus large pour celle-là.
    """
    utile = round(cote * (1 - 2 * marge))
    copie = im.copy()
    copie.thumbnail((utile, utile), Image.LANCZOS)
    toile = Image.new("RGBA", (cote, cote), fond)
    toile.paste(copie, ((cote - copie.width) // 2, (cote - copie.height) // 2), copie)
    return toile


def tracer(im: Image.Image, clair: bool = False) -> str:
    """Vectorise le logo : deux encres, deux tracés, un seul fichier.

    Un logo est un aplat à deux couleurs. Le servir en bitmap oblige à choisir
    une définition — et à la payer deux fois pour les écrans à 2× — pour un
    résultat qui reste flou d'un cran sur les autres. Le tracé, lui, est net à
    toutes les tailles et pèse moins que la seule version 320 px.

    Chaque encre est isolée en masque bilevel, vectorisée par potrace, puis
    recomposée dans un unique SVG. L'image est doublée avant le tracé : les
    escaliers du fichier d'origine s'y moyennent, et les contours sortent plus
    francs.
    """
    grand = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    px = list(grand.getdata())
    tracés = []
    with tempfile.TemporaryDirectory() as tmp:
        for encre, garder in ((NUIT, lambda v: v < 110), (CYAN, lambda v: v >= 110)):
            masque = Image.new("1", grand.size)
            # potrace trace le NOIR : le masque vaut 0 là où l'encre est.
            masque.putdata([0 if (a > 128 and garder(v)) else 1 for _, v, _, a in px])
            pbm, svg = Path(tmp, "m.pbm"), Path(tmp, "m.svg")
            masque.save(pbm)
            subprocess.run(["potrace", "-s", "-o", str(svg), "--flat",
                            "-a", "1.0", "-O", "0.35", "-t", "3", str(pbm)],
                           check=True)
            brut = svg.read_text()
            d = re.search(r'<path d="(.*?)"', brut, re.S).group(1)
            # potrace écrit six décimales dans un espace de 33 180 unités :
            # elles ne décrivent rien et pèsent la moitié du fichier.
            d = re.sub(r"\d+\.\d+", lambda m: str(round(float(m.group(0)))), d)
            d = re.sub(r"\s+", " ", d).strip()
            couleur = "#ffffff" if (clair and encre is NUIT) else "#%02x%02x%02x" % encre
            tracés.append(f'<path fill="{couleur}" d="{d}"/>')
    L, H = grand.size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L*10} {H*10}" '
            f'role="img" aria-label="Déboucheur Richard en Bretagne">'
            f'<g transform="translate(0,{H*10}) scale(1,-1)">'
            + "".join(tracés) + "</g></svg>\n")


def ecrire(im: Image.Image, base: Path, largeurs) -> None:
    for l in largeurs:
        h = round(im.height * l / im.width)
        v = im.resize((l, h), Image.LANCZOS)
        v.save(base.with_name(f"{base.name}-{l}.png"), "PNG", optimize=True)
        v.save(base.with_name(f"{base.name}-{l}.webp"), "WEBP", quality=92, method=6)
        poids = (base.with_name(f"{base.name}-{l}.png").stat().st_size,
                 base.with_name(f"{base.name}-{l}.webp").stat().st_size)
        print(f"  ✓ {base.name}-{l}  {l}×{h}  "
              f"PNG {poids[0]/1024:.1f} Ko · WebP {poids[1]/1024:.1f} Ko")


def main() -> int:
    if not SOURCE.is_file():
        print(f"Fichier introuvable : {SOURCE}", file=sys.stderr)
        return 1
    SORTIE.mkdir(parents=True, exist_ok=True)

    logo = aplatir(recadrer(detourer(Image.open(SOURCE))))
    print(f"Logo détouré : {logo.width}×{logo.height} "
          f"(rapport {logo.width / logo.height:.2f})\n")

    for nom, clair in (("logo-deboucheur-richard", False),
                       ("logo-deboucheur-richard-clair", True)):
        f = SORTIE / f"{nom}.svg"
        f.write_text(tracer(logo, clair), encoding="utf-8")
        print(f"  ✓ {f.name}  {f.stat().st_size / 1024:.1f} Ko")

    # Un seul bitmap, pour les contextes qui n'acceptent pas le vectoriel :
    # vignettes de partage, signatures de courriel, documents imprimés.
    ecrire(logo, SORTIE / "logo-deboucheur-richard", [480])
    ecrire(variante_claire(logo), SORTIE / "logo-deboucheur-richard-clair", [480])

    mono = monogramme(logo)
    print(f"\nMonogramme : {mono.width}×{mono.height}")
    mono.save(SORTIE / "monogramme.png", "PNG", optimize=True)

    # Favicons et icônes d'application, tirés du monogramme.
    # Le favicon vectoriel est celui que servent Chrome, Firefox et Safari
    # récents : à 16 px, c'est lui qui reste net là où le bitmap se brouille.
    (ICONES / "favicon.svg").write_text(tracer(mono), encoding="utf-8")
    carre(mono, 180).save(ICONES / "apple-touch-icon.png", "PNG", optimize=True)
    carre(mono, 192).save(ICONES / "icone-192.png", "PNG", optimize=True)
    carre(mono, 512).save(ICONES / "icone-512.png", "PNG", optimize=True)
    carre(mono, 512, marge=.22).save(ICONES / "icone-512-maskable.png", "PNG", optimize=True)
    carre(mono, 48, marge=.04).convert("RGB").save(
        ICONES / "favicon.ico", "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  ✓ favicon.svg, favicon.ico, apple-touch-icon.png, "
          "icone-192/512/512-maskable.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
