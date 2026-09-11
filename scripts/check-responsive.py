#!/usr/bin/env python3
"""
Contrôle du responsive sur les largeurs réelles des appareils.

    python3 scripts/check-responsive.py [--pages N] [--largeurs 375,768]

Ce que le script cherche, et pourquoi
-------------------------------------
Un défaut de responsive ne se voit pas dans le CSS : il se voit à une largeur
donnée, sur une page donnée. Le script ouvre donc chaque gabarit à chacune des
largeurs et mesure la page rendue :

  1. DÉBORDEMENT DU DOCUMENT — `scrollWidth` supérieur à la fenêtre. C'est le
     symptôme : la page défile latéralement.
  2. ÉLÉMENT HORS CADRE — un bloc dont le bord droit dépasse la fenêtre, ou
     dont le bord gauche est négatif. C'est la cause, et c'est elle qu'il faut
     corriger.
  3. IMAGE QUI DÉBORDE de son conteneur, ou dont le ratio affiché s'écarte de
     son ratio naturel — une image déformée est un défaut visuel que personne
     ne remarque dans le code.
  4. TEXTE TRONQUÉ — contenu plus large que sa boîte, sans défilement prévu.
  5. CIBLE TACTILE trop petite ou collée au bord de l'écran.

Les éléments volontairement hors cadre (tiroir de navigation fermé, voile) sont
exclus : ils sont positionnés hors écran par conception.

Rend 1 si un défaut est constaté, 0 sinon.
"""

import asyncio
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
CHROMIUM = "/opt/pw-browsers/chromium"

# Les largeurs demandées : téléphones, tablettes, ordinateurs.
LARGEURS = [320, 375, 390, 414, 430, 768, 820, 1024, 1280, 1440, 1920]

# Un gabarit de chaque type. Inutile de tester les 111 pages : elles sont
# construites à partir des mêmes partiels et des mêmes composants.
PAGES = [
    "/",                              # accueil, la plus dense
    "/prestations",                   # sommaire des prestations
    "/debouchage-wc",                 # page de prestation
    "/curage-canalisation",           # prestation avec tableau
    "/departements/finistere",        # page départementale
    "/degorgement-rennes",            # page communale
    "/blog/",                         # index du blog
    "/blog/prix-degorgement",         # article
    "/devis",                         # formulaire
    "/contact",
    "/faq",
    "/tarifs",                        # tableaux
    "/zone-intervention",
    "/degorgement-urgence",           # bande sombre
    "/mentions-legales",
    "/404.html",
]

MESURE = r"""
() => {
  const V = window.innerWidth;
  const defauts = [];
  const vus = new Set();

  const nom = (el) => el.tagName.toLowerCase()
    + (el.className && el.className.toString
        ? '.' + el.className.toString().trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.')
        : '');

  // Positionnés hors écran par conception : ils ne sont pas des défauts.
  const voulu = (el) => el.closest(
    '.nav, .voile, .skip-link, .pot-de-miel, .visually-hidden, [hidden]'
  ) !== null;

  // Un ancêtre qui défile OU qui découpe (un tableau large dans son cadre, un
  // trait de liaison qui traverse la gouttière d'une grille) autorise ses
  // enfants à s'étendre : dans les deux cas, rien ne peut pousser la page.
  const dansUnCadreContenu = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      if (/auto|scroll|hidden|clip/.test(getComputedStyle(n).overflowX)) return true;
    }
    return false;
  };

  const ajouter = (type, el, detail) => {
    const cle = type + '|' + nom(el) + '|' + detail;
    if (vus.has(cle)) return;
    vus.add(cle);
    defauts.push({ type, element: nom(el), detail });
  };

  // 1. Le document déborde-t-il ?
  const scroll = document.documentElement.scrollWidth;
  if (scroll > V + 1) {
    defauts.push({ type: 'document', element: 'html',
                   detail: `scrollWidth ${scroll} > fenêtre ${V}` });
  }

  for (const el of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (voulu(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;

    // 2. Hors cadre — on ignore ce qui est fixe, et ce qui vit dans un cadre
    //    défilant.
    if (cs.position !== 'fixed' && !dansUnCadreContenu(el)) {
      if (r.right > V + 1.5) ajouter('hors-cadre', el, `bord droit à ${Math.round(r.right)} px`);
      if (r.left < -1.5)     ajouter('hors-cadre', el, `bord gauche à ${Math.round(r.left)} px`);
    }

    // 3. Image : déborde de son parent, ou déformée.
    if (el.tagName === 'IMG' && el.naturalWidth) {
      // <picture> est en display:contents : il n'a pas de boîte, et le
      // comparer reviendrait à mesurer l'image contre une largeur de zéro.
      // On remonte donc au premier ancêtre qui en a une.
      let boite = el.parentElement;
      while (boite && getComputedStyle(boite).display === 'contents') {
        boite = boite.parentElement;
      }
      const p = (boite || document.body).getBoundingClientRect();
      if (r.width > p.width + 1.5) {
        ajouter('image-deborde', el, `${Math.round(r.width)} px dans ${Math.round(p.width)} px`);
      }
      const attendu = el.naturalWidth / el.naturalHeight;
      const rendu = r.width / r.height;
      const couvre = cs.objectFit === 'cover' || cs.objectFit === 'contain';
      if (!couvre && r.height > 0 && Math.abs(rendu - attendu) / attendu > 0.04) {
        ajouter('image-deformee', el,
          `ratio ${rendu.toFixed(2)} au lieu de ${attendu.toFixed(2)}`);
      }
    }

    // 4. Contenu plus large que sa boîte, sans défilement ni découpe prévus.
    //    `overflow: hidden` découpe volontairement : un décor qui dépasse d'un
    //    bloc découpé ne se voit pas et ne pousse pas la page.
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) {
      const contenu = /auto|scroll|hidden|clip/.test(cs.overflowX)
        || dansUnCadreContenu(el);
      if (!contenu && !['IMG', 'SVG', 'VIDEO', 'CANVAS'].includes(el.tagName)) {
        ajouter('contenu-tronque', el,
          `contenu ${el.scrollWidth} px dans ${el.clientWidth} px`);
      }
    }
  }

  // 5. Cibles tactiles : taille et distance au bord.
  if (V <= 820) {
    for (const el of document.querySelectorAll('a.btn, button, input, select, textarea')) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || voulu(el)) continue;
      // Pour une case ou un bouton radio, la cible réelle est son étiquette :
      // le contrôle natif fait 19 px et ne peut pas être agrandi utilement.
      let cible = el;
      if (el.type === 'radio' || el.type === 'checkbox') {
        cible = el.closest('label')
          || (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`))
          || el.parentElement;
      }
      const r = cible.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      if (r.height < 40) ajouter('cible-petite', el, `${Math.round(r.height)} px de haut`);
      if (r.left < 4 || r.right > V - 4) {
        ajouter('cible-au-bord', el, `de ${Math.round(r.left)} à ${Math.round(r.right)} px`);
      }
    }
  }

  return defauts;
}
"""


def port_libre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


async def controler(pages, largeurs):
    port = port_libre()
    serveur = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port}", "-t", "public", "scripts/routeur-local.php"],
        cwd=RACINE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    trouves = {}
    mesures = 0
    try:
        async with async_playwright() as p:
            nav = await p.chromium.launch(executable_path=CHROMIUM)
            for largeur in largeurs:
                page = await nav.new_page(
                    viewport={"width": largeur, "height": 900},
                    device_scale_factor=1)
                for url in pages:
                    await page.goto(f"http://127.0.0.1:{port}{url}", wait_until="networkidle")
                    # Tout révéler et tout charger : un défaut de mise en page
                    # caché derrière une animation reste un défaut.
                    await page.evaluate(
                        "async () => {"
                        " document.querySelectorAll('[data-reveal]')"
                        "   .forEach(e => e.classList.add('est-visible'));"
                        " const i = [...document.images];"
                        " i.forEach(x => { x.loading = 'eager'; });"
                        " await Promise.all(i.map(x => Promise.race(["
                        "   x.decode().catch(() => {}),"
                        "   new Promise(r => setTimeout(r, 2500))])));"
                        " document.querySelectorAll('details').forEach(d => { d.open = true; });"
                        "}")
                    await page.wait_for_timeout(120)
                    mesures += 1
                    for d in await page.evaluate(MESURE):
                        cle = (d["type"], d["element"], d["detail"])
                        trouves.setdefault(cle, []).append((largeur, url))
                await page.close()
            await nav.close()
    finally:
        serveur.terminate()

    print(f"Responsive — {len(pages)} gabarits × {len(largeurs)} largeurs "
          f"({mesures} rendus analysés)\n")

    if not trouves:
        print("  v Aucun débordement, aucun élément hors cadre, aucune image déformée.")
        return 0

    par_type = {}
    for cle, ou in trouves.items():
        par_type.setdefault(cle[0], []).append((cle, ou))

    total = 0
    for type_, entrees in sorted(par_type.items()):
        print(f"  x {type_} — {len(entrees)} cas")
        for (t, element, detail), ou in sorted(entrees)[:8]:
            largeurs_touchees = sorted({l for l, _ in ou})
            pages_touchees = sorted({u for _, u in ou})
            print(f"      {element} : {detail}")
            print(f"        largeurs {largeurs_touchees}")
            print(f"        pages    {pages_touchees[:4]}"
                  + (f" (+{len(pages_touchees) - 4})" if len(pages_touchees) > 4 else ""))
            total += 1
        if len(entrees) > 8:
            print(f"      … et {len(entrees) - 8} autres cas de ce type")
        print()
    return 1


if __name__ == "__main__":
    args = sys.argv[1:]
    pages, largeurs = PAGES, LARGEURS
    if "--pages" in args:
        pages = PAGES[:int(args[args.index("--pages") + 1])]
    if "--largeurs" in args:
        largeurs = [int(x) for x in args[args.index("--largeurs") + 1].split(",")]
    sys.exit(asyncio.run(controler(pages, largeurs)))
