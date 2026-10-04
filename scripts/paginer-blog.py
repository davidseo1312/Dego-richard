#!/usr/bin/env python3
"""
Construit le sommaire du blog, paginé, à partir des articles eux-mêmes.

    python3 scripts/paginer-blog.py

Pourquoi
--------
Le sommaire du blog était une page unique dont les cartes étaient écrites à
la main. À treize articles, c'était déjà long ; à vingt et un, la page
demandait six écrans de défilement avant d'arriver au dernier titre, et
chaque ajout obligeait à recopier un bloc de markup — donc à se tromper.

Le sommaire est désormais DÉRIVÉ des articles. Chacun porte, dans son bloc de
métadonnées, ce qui le décrit dans la liste :

    carte_rang: 12              ordre de présentation à date égale
    carte_etiquette: Urgence
    carte_titre: WC bouché : que faire ?
    carte_resume: Ce qui fonctionne, ce qui ne fonctionne pas…

Les cartes ne portent pas de visuel. Le site compte dix photographies
d'intervention ; à huit cartes par page, deux d'entre elles revenaient deux
fois sur le même écran, et chacune répétait l'image placée en tête de
l'article qu'elle annonce. Une vignette qui n'apprend rien et qu'on a déjà
vue n'aide pas à choisir un article : le titre, l'étiquette et la durée de
lecture, si.

L'ordre est celui de la date de publication, du plus récent au plus ancien ;
à date égale, « carte_rang » tranche. Un article publié aujourd'hui se place
donc de lui-même en tête de la première page, sans qu'on touche au sommaire.

La durée de lecture affichée sur la carte est lue sur l'article, où
scripts/duree-lecture.py l'a écrite à partir du texte rendu. Une seule
source, donc jamais deux chiffres différents pour le même article.

Pages produites, à ARTICLES_PAR_PAGE articles chacune :

    src/pages/blog/index.html     -> /blog/
    src/pages/blog/page/2.html    -> /blog/page/2
    src/pages/blog/page/3.html    -> /blog/page/3   …

Idempotent : relancé sans changement, il réécrit des fichiers identiques.
C'est ce que vérifie « --verifier », appelé par scripts/audit.sh : si le
sommaire ne correspond plus aux articles — parce qu'on en a ajouté un sans
régénérer —, l'audit échoue au lieu de publier une liste incomplète.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BLOG = RACINE / "src" / "pages" / "blog"

ARTICLES_PAR_PAGE = 8

VERT, ROUGE, FIN = "\033[32m", "\033[31m", "\033[0m"

# Chapeau propre à chaque page : une description dupliquée d'une page à
# l'autre est du contenu dupliqué, et le contrôle SEO la refuse.
CHAPEAU_1 = (
    "Des articles écrits à partir de ce que nous voyons réellement en intervention, "
    "sans promesse miracle ni produit à vendre. Quand un problème se règle sans nous, "
    "nous le disons. Les plus récents en premier."
)
DESCRIPTION_1 = (
    "Comprendre pourquoi une canalisation se bouche, quoi faire en cas d'urgence, "
    "comment entretenir son réseau et ce que coûte réellement un dégorgement."
)


def meta(texte: str, cle: str, defaut=None):
    m = re.search(rf"^{cle}:[ \t]*(.*)$", texte, re.M)
    return m.group(1).strip() if m else defaut


def articles() -> list:
    liste = []
    for f in sorted(BLOG.glob("*.html")):
        if f.name == "index.html":
            continue
        s = f.read_text(encoding="utf-8")
        bloc = s.split("-->", 1)[0]
        titre = meta(bloc, "carte_titre")
        if not titre:
            raise SystemExit(f"{f.name} : carte_titre manquant dans le bloc meta")
        duree = re.search(r'<span class="duree">Lecture (\d+) min</span>', s)
        liste.append({
            "slug": f.stem,
            "date": meta(bloc, "date", "0000-00-00"),
            "rang": int(meta(bloc, "carte_rang", "999")),
            "etiquette": meta(bloc, "carte_etiquette", "Conseils"),
            "titre": titre,
            "resume": meta(bloc, "carte_resume", ""),
            "duree": int(duree.group(1)) if duree else 6,
        })
    liste.sort(key=lambda a: (a["date"], -a["rang"]), reverse=True)
    return liste


def carte(a: dict) -> str:
    return f'''      <article class="carte carte-article">
        <p class="carte-etiquettes"><span>{a['etiquette']}</span><span class="duree">Lecture {a['duree']} min</span></p>
        <h2><a href="/blog/{a['slug']}">{a['titre']}</a></h2>
        <p>{a['resume']}</p>
        <a class="lien-fleche" href="/blog/{a['slug']}">Lire l'article</a>
      </article>
'''


def url(n: int) -> str:
    return "/blog/" if n == 1 else f"/blog/page/{n}"


def pagination(n: int, total: int) -> str:
    """La navigation entre pages, en liste ordonnée : c'est une séquence."""
    if total < 2:
        return ""
    liens = []
    for i in range(1, total + 1):
        if i == n:
            liens.append(f'          <li><span aria-current="page">{i}</span></li>')
        else:
            liens.append(
                f'          <li><a href="{url(i)}" aria-label="Page {i}">{i}</a></li>')
    prec = (f'        <a class="pagination-bord" href="{url(n - 1)}" rel="prev">'
            f'<span class="pagination-fleche" aria-hidden="true">&larr;</span>'
            f'<span class="pagination-libelle">Précédent</span></a>' if n > 1 else
            '        <span class="pagination-bord pagination-inactif" aria-hidden="true">'
            '<span class="pagination-fleche">&larr;</span>'
            '<span class="pagination-libelle">Précédent</span></span>')
    suiv = (f'        <a class="pagination-bord" href="{url(n + 1)}" rel="next">'
            f'<span class="pagination-libelle">Suivant</span>'
            f'<span class="pagination-fleche" aria-hidden="true">&rarr;</span></a>'
            if n < total else
            '        <span class="pagination-bord pagination-inactif" aria-hidden="true">'
            '<span class="pagination-libelle">Suivant</span>'
            '<span class="pagination-fleche">&rarr;</span></span>')
    corps = "\n".join(liens)
    return f'''
    <nav class="pagination" aria-label="Pages du sommaire">
{prec}
      <ol>
{corps}
      </ol>
{suiv}
    </nav>
'''


def page(n: int, total: int, lot: list, tous: list) -> str:
    premier, dernier = lot[0], lot[-1]
    if n == 1:
        titre = "Conseils canalisations — blog {{NOM_COMMERCIAL}}"
        description = DESCRIPTION_1
        fil = "Conseils canalisations"
        h1 = "Conseils canalisations"
        chapeau = CHAPEAU_1
        priorite = "0.6"
        entete_meta = ""
    else:
        titre = f"Conseils canalisations — page {n} sur {total}"
        # Composée à partir des RANGS, pas des titres : un titre long faisait
        # dépasser la limite de 160 caractères, et la troncature coupait au
        # milieu d'un nom propre.
        description = (f"Page {n} du sommaire des conseils canalisations : "
                       f"les articles {(n - 1) * ARTICLES_PAR_PAGE + 1} à "
                       f"{(n - 1) * ARTICLES_PAR_PAGE + len(lot)} sur {len(tous)}, "
                       f"du plus récent au plus ancien.")
        fil = f"Page {n}"
        h1 = f"Conseils canalisations — page {n} sur {total}"
        chapeau = (f"Les articles {(n - 1) * ARTICLES_PAR_PAGE + 1} à "
                   f"{(n - 1) * ARTICLES_PAR_PAGE + len(lot)} sur {len(tous)}, "
                   f"du plus récent au plus ancien. "
                   f'<a href="/blog/">Revenir à la première page</a>.')
        priorite = "0.4"
        entete_meta = "parent_nom: Conseils canalisations\nparent_url: /blog/\n"

    assert len(description) <= 160, (n, len(description))

    fil_html = ('          <li>Conseils canalisations</li>' if n == 1 else
                '          <li><a href="/blog/">Conseils canalisations</a></li>\n'
                f'          <li>Page {n}</li>')

    cartes = "".join(carte(a) for a in lot)

    return f'''<!--meta
title: {titre}
description: {description}
breadcrumb: {fil}
{entete_meta}image: /assets/img/partage/og-default.jpg
priority: {priorite}
faq: non
-->

<section class="hero hero-page">
  <div class="wrap">
    <div class="fil">
      <nav aria-label="Fil d'Ariane">
        <ol>
          <li><a href="/">Accueil</a></li>
{fil_html}
        </ol>
      </nav>
    </div>

    <p class="sur-titre">Le blog</p>
    <h1>{h1}</h1>
    <p class="chapeau">
      {chapeau}
    </p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="grille grille-3">
{cartes}    </div>
{pagination(n, total)}  </div>
</section>

<section class="cta-final">
  <div class="wrap">
    <h2>Une canalisation bouchée&nbsp;? N'attendez pas d'avoir tout lu</h2>
    <p>Un bouchon se compacte à chaque utilisation du réseau. Appelez-nous&nbsp;: nous vous dirons au téléphone ce qu'il faut couper tout de suite, et sous quel délai nous pouvons intervenir dans votre commune.</p>
    <p style="margin-top:1.5rem">
      <a class="btn btn-call btn-large" href="tel:{{{{TELEPHONE_E164}}}}" data-track="appel" data-track-zone="cta-final">Appeler le {{{{TELEPHONE}}}}</a>
      <a class="btn btn-ghost btn-large" href="/devis" data-track="clic_devis" data-track-zone="cta-final">Demander une intervention</a>
    </p>
  </div>
</section>
'''


def main(verifier: bool = False) -> int:
    tous = articles()
    lots = [tous[i:i + ARTICLES_PAR_PAGE]
            for i in range(0, len(tous), ARTICLES_PAR_PAGE)]
    total = len(lots)
    dossier = BLOG / "page"

    attendu = {}
    for i, lot in enumerate(lots, 1):
        cible = BLOG / "index.html" if i == 1 else dossier / f"{i}.html"
        attendu[cible] = page(i, total, lot, tous)

    if verifier:
        ecarts = [c for c, t in attendu.items()
                  if not c.is_file() or c.read_text(encoding="utf-8") != t]
        restes = [f for f in (dossier.glob("*.html") if dossier.is_dir() else [])
                  if f not in attendu]
        if ecarts or restes:
            print(f"{ROUGE}Le sommaire du blog ne correspond plus aux "
                  f"articles.{FIN}")
            for f in ecarts + restes:
                print(f"   • {f.relative_to(RACINE)}")
            print("  Régénérez-le : python3 scripts/paginer-blog.py")
            return 1
        print(f"{VERT}Sommaire du blog à jour{FIN} — {len(tous)} article(s) "
              f"sur {total} page(s) de {ARTICLES_PAR_PAGE} au maximum.")
        return 0

    dossier.mkdir(parents=True, exist_ok=True)
    for vieux in dossier.glob("*.html"):
        if vieux not in attendu:
            vieux.unlink()
    for cible, texte in attendu.items():
        cible.write_text(texte, encoding="utf-8")
        print(f"   ✓ {cible.relative_to(RACINE)}")

    if not any(dossier.iterdir()):
        dossier.rmdir()

    print(f"{len(tous)} article(s) répartis sur {total} page(s) "
          f"de {ARTICLES_PAR_PAGE} au maximum")
    return 0


if __name__ == "__main__":
    sys.exit(main("--verifier" in sys.argv))
