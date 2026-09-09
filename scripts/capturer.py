#!/usr/bin/env python3
"""
Capture d'écran des pages construites, pour contrôle visuel.

    python3 scripts/capturer.py [chemin ...] [--largeur 1440] [--pleine]

Sert le dossier public/ derrière le routeur local (mêmes URL sans extension
qu'en production), ouvre chaque page dans Chromium et enregistre un PNG dans
le dossier de travail. Rien de tout cela n'est publié : le script ne sert
qu'à vérifier, avant de livrer, que ce qui est écrit se voit réellement.
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
CHROMIUM = "/opt/pw-browsers/chromium"
SORTIE = Path(os.environ.get("DOSSIER_CAPTURES", "/tmp/captures"))


def port_libre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


async def capturer(chemins, largeur, hauteur, pleine, suffixe):
    SORTIE.mkdir(parents=True, exist_ok=True)
    port = port_libre()
    serveur = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port}", "-t", "public", "scripts/routeur-local.php"],
        cwd=RACINE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        async with async_playwright() as p:
            nav = await p.chromium.launch(executable_path=CHROMIUM)
            page = await nav.new_page(viewport={"width": largeur, "height": hauteur},
                                      device_scale_factor=1)
            for chemin in chemins:
                await page.goto(f"http://127.0.0.1:{port}{chemin}", wait_until="networkidle")
                # Faire défiler déclenche les apparitions au scroll : sans cela,
                # une capture pleine page montre des blocs restés invisibles.
                await page.evaluate(
                    "async () => { const h = document.body.scrollHeight;"
                    " for (let y = 0; y < h; y += 400) { window.scrollTo(0, y);"
                    " await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0);"
                    " await new Promise(r => setTimeout(r, 400)); }")
                # L'observateur d'intersection ne rattrape pas un défilement
                # programmé aussi rapide, et une capture pleine page redimensionne
                # la fenêtre après coup. On force donc l'état révélé : ce qui est
                # contrôlé ici, c'est la mise en page, pas l'animation.
                await page.evaluate(
                    "document.querySelectorAll('[data-reveal]')"
                    ".forEach(e => e.classList.add('est-visible'))")
                # Idem pour le chargement différé des images : on le neutralise
                # et on attend leur décodage, sinon la capture montre des cadres
                # vides là où la page réelle affiche bien un visuel.
                await page.evaluate(
                    "async () => { const i = [...document.images];"
                    " i.forEach(img => { img.loading = 'eager'; });"
                    " await Promise.all(i.map(img => img.complete ? 0 :"
                    " new Promise(r => { img.onload = img.onerror = r; }))); }")
                await page.wait_for_timeout(400)
                nom = (chemin.strip("/").replace("/", "-") or "accueil") + suffixe + ".png"
                await page.screenshot(path=str(SORTIE / nom), full_page=pleine)
                print(f"  ✓ {nom}")
            await nav.close()
    finally:
        serveur.terminate()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    largeur = 1440
    hauteur = 900
    pleine = "--pleine" in args
    if "--largeur" in args:
        i = args.index("--largeur")
        largeur = int(args[i + 1])
        del args[i:i + 2]
    if "--hauteur" in args:
        i = args.index("--hauteur")
        hauteur = int(args[i + 1])
        del args[i:i + 2]
    chemins = [a for a in args if not a.startswith("--")] or ["/"]
    asyncio.run(capturer(chemins, largeur, hauteur, pleine, f"-{largeur}"))
