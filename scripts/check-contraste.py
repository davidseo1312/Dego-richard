#!/usr/bin/env python3
"""
Contrôle des contrastes de texte sur les pages construites (WCAG 1.4.3).

    python3 scripts/check-contraste.py

Méthode
-------
Lire la feuille de style ne suffit pas : la couleur de fond réelle d'un texte
peut venir d'un dégradé, d'une image, d'une superposition translucide ou d'un
ancêtre lointain. Le script mesure donc ce que l'écran affiche vraiment :

  1. il relève chaque nœud portant du texte, avec sa couleur, sa taille et sa
     graisse ;
  2. il rend TOUT le texte transparent et prend une capture — il ne reste que
     les fonds ;
  3. pour chaque nœud, il échantillonne cette capture sur l'emprise du texte
     et retient la teinte dominante ;
  4. il calcule le rapport de contraste et le compare au seuil applicable :
     3:1 pour un grand texte (24 px, ou 18,7 px en gras), 4,5:1 sinon.

Un texte posé sur une photographie est donc mesuré contre la photographie,
et un texte sur dégradé contre la portion de dégradé qu'il occupe vraiment.

Le script rend 1 si un défaut est mesuré, 0 sinon.
"""

import asyncio
import io
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
CHROMIUM = "/opt/pw-browsers/chromium"

# Un échantillon couvrant tous les gabarits du site.
PAGES = [
    "/", "/prestations", "/debouchage-wc", "/curage-canalisation",
    "/departements/finistere", "/degorgement-rennes", "/degorgement-vannes",
    "/blog/", "/blog/prix-degorgement", "/devis", "/contact", "/faq",
    "/tarifs", "/zone-intervention", "/degorgement-urgence",
    "/mentions-legales", "/a-propos", "/404.html",
]

# Relevé des candidats : un nœud qui porte directement du texte visible.
RELEVE = r"""
() => {
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const texte = [...el.childNodes]
      .filter(n => n.nodeType === 3 && n.textContent.trim().length > 1)
      .map(n => n.textContent.trim()).join(' ');
    if (!texte) continue;

    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (parseFloat(cs.opacity) < 0.5) continue;

    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (r.bottom < 0 || r.top > document.documentElement.scrollHeight) continue;

    const m = cs.color.match(/rgba?\(([^)]+)\)/);
    if (!m) continue;
    const p = m[1].split(',').map(x => parseFloat(x));
    if (p.length > 3 && p[3] < 0.5) continue;

    const px = parseFloat(cs.fontSize);
    const gras = parseInt(cs.fontWeight, 10) >= 700;
    out.push({
      texte: texte.slice(0, 44),
      etiquette: el.tagName.toLowerCase() + (el.className && el.className.toString
        ? '.' + el.className.toString().trim().split(/\s+/).filter(Boolean)[0] : ''),
      couleur: p.slice(0, 3),
      seuil: (px >= 24 || (px >= 18.66 && gras)) ? 3 : 4.5,
      x: r.left + window.scrollX, y: r.top + window.scrollY,
      w: r.width, h: r.height,
    });
  }
  return out;
}
"""

# Neutralise le texte sans toucher aux fonds : la capture ne montre plus que
# ce qui se trouve DERRIÈRE les lettres.
MASQUER = """
() => {
  const st = document.createElement('style');
  st.id = 'mesure-contraste';
  st.textContent = '*, *::before, *::after { color: transparent !important;'
    + ' text-shadow: none !important; text-decoration-color: transparent !important;'
    + ' caret-color: transparent !important; }';
  document.head.appendChild(st);
}
"""


def luminance(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def teinte_dominante(image, boite):
    """Couleur la plus fréquente sous l'emprise d'un texte, quantifiée."""
    x, y, w, h = boite
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(image.width, int(x + w)), min(image.height, int(y + h))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None
    zone = image.crop((x0, y0, x1, y1))
    if zone.width * zone.height > 40000:
        zone = zone.resize((max(2, zone.width // 4), max(2, zone.height // 4)))
    # Quantifier évite qu'un dégradé produise mille couleurs distinctes et
    # qu'aucune ne ressorte comme dominante.
    brut = zone.convert("RGB")
    # `list(brut.getdata())` est déprécié en Pillow 12 ; `tobytes` donne les
    # mêmes octets et reste stable.
    octets = brut.tobytes()
    pixels = [(octets[i] // 8 * 8, octets[i + 1] // 8 * 8, octets[i + 2] // 8 * 8)
              for i in range(0, len(octets), 3)]
    return Counter(pixels).most_common(1)[0][0]


def port_libre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


async def controler():
    port = port_libre()
    serveur = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port}", "-t", "public", "scripts/routeur-local.php"],
        cwd=RACINE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    defauts, mesures = [], 0
    try:
        async with async_playwright() as p:
            nav = await p.chromium.launch(executable_path=CHROMIUM)
            page = await nav.new_page(viewport={"width": 1360, "height": 900})
            for url in PAGES:
                await page.goto(f"http://127.0.0.1:{port}{url}", wait_until="networkidle")
                # Les apparitions au défilement et le chargement différé
                # doivent être neutralisés, sinon la moitié de la page est
                # mesurée dans un état qu'un visiteur ne voit jamais.
                await page.evaluate(
                    "() => { document.querySelectorAll('[data-reveal]')"
                    ".forEach(e => e.classList.add('est-visible'));"
                    " [...document.images].forEach(i => { i.loading = 'eager'; }); }")
                await page.wait_for_timeout(500)

                candidats = await page.evaluate(RELEVE)
                await page.evaluate(MASQUER)
                await page.wait_for_timeout(150)
                png = await page.screenshot(type="png", full_page=True)
                fonds = Image.open(io.BytesIO(png)).convert("RGB")

                vus = set()
                for c in candidats:
                    fond = teinte_dominante(fonds, (c["x"], c["y"], c["w"], c["h"]))
                    if fond is None:
                        continue
                    mesures += 1
                    r = contraste(c["couleur"], fond)
                    if r >= c["seuil"] - 0.02:
                        continue
                    cle = (c["etiquette"], tuple(c["couleur"]), fond)
                    if cle in vus:
                        continue
                    vus.add(cle)
                    defauts.append((url, c, fond, round(r, 2)))
            await nav.close()
    finally:
        serveur.terminate()

    print(f"Contraste — {len(PAGES)} gabarits, {mesures} textes mesurés sur la page rendue\n")
    if defauts:
        print(f"  x {len(defauts)} texte(s) sous le seuil :")
        for url, c, fond, r in defauts:
            print(f"      {url} · {c['etiquette']} « {c['texte']} »")
            print(f"        rgb{tuple(c['couleur'])} sur rgb{fond} = {r}:1 "
                  f"(minimum {c['seuil']}:1)")
        return 1

    print("  v Tous les textes atteignent le seuil WCAG AA, fonds unis, dégradés")
    print("    et images compris.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(controler()))
