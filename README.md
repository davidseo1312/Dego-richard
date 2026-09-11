# Dégorgement Richard

Site de dégorgement, débouchage de canalisation et assainissement pour les six
départements du Grand Ouest : **Côtes-d'Armor (22), Finistère (29),
Ille-et-Vilaine (35), Morbihan (56), Loire-Atlantique (44), Maine-et-Loire (49)**.

Site **statique**, construit par un script `bash` sans aucune dépendance à
installer. Un seul élément dynamique : le formulaire de demande d'intervention,
en PHP. Le résultat se sert tel quel par n'importe quel hébergement mutualisé.

```
branche source → sources, scripts, documentation
deploy         → uniquement le site construit, index.html à la racine
```

La branche source est la branche par défaut du dépôt, aujourd'hui
`claude/plumbing-site-brittany-eoxa6x` ; `main` reste acceptée si le dépôt est
réorganisé plus tard.

---

## Sommaire

1. [Démarrage rapide](#démarrage-rapide)
2. [Comment le site est construit](#comment-le-site-est-construit)
3. [Organisation des fichiers](#organisation-des-fichiers)
4. [Design system](#design-system)
5. [Photographies, carte et avis](#photographies-carte-et-avis)
6. [Modifier le site](#modifier-le-site)
7. [Le formulaire de demande](#le-formulaire-de-demande)
8. [Google Search Console, Analytics, Tag Manager](#google-search-console-analytics-tag-manager)
9. [Contrôles avant mise en ligne](#contrôles-avant-mise-en-ligne)
10. [DEPLOYMENT HOSTINGER](#deployment-hostinger)
11. [Cohérence géographique et commerciale](#cohérence-géographique-et-commerciale)
12. [Avant la mise en ligne : informations à fournir](#avant-la-mise-en-ligne--informations-à-fournir)
13. [Sécurité](#sécurité)

---

## Démarrage rapide

```bash
bash scripts/build.sh      # construit public/
bash scripts/audit.sh      # build + SEO/GEO + HTML + contenu local + JSON-LD + test HTTP
bash scripts/apercu.sh     # aperçu sur http://localhost:8080
bash tests/lancer.sh       # tests de navigateur (facultatif, nécessite Playwright)
```

Aucun `npm install`, aucun gestionnaire de paquets : le build n'utilise que
`bash`, `perl`, `find` et `sed`, présents partout. `python3` et `php` ne servent
qu'aux contrôles et à l'aperçu.

---

## Comment le site est construit

`scripts/build.sh` assemble trois choses :

| Source | Rôle |
|---|---|
| `src/config.sh` | Toutes les valeurs globales : téléphone, identité légale, zone, horaires, tarifs, indexation. |
| `src/partials/*.html` | En-tête, pied de page, `<head>`, formulaire, blocs JSON-LD. |
| `src/pages/**/*.html` | Le contenu de chaque page, avec un bloc de métadonnées en tête. |

Chaque page source commence par un bloc de métadonnées :

```html
<!--meta
title: Dégorgement et débouchage à Rennes (35)
description: …
schema: ville
breadcrumb: Dégorgement à Rennes
zone_nom: Rennes
zone_parent: Ille-et-Vilaine
parent_nom: Ille-et-Vilaine (35)
parent_url: /departements/ille-et-vilaine
image: /assets/img/canalisation.svg
priority: 0.8
-->
```

### Clés de métadonnées disponibles

| Clé | Effet | Défaut |
|---|---|---|
| `title` | Balise `<title>`, Open Graph, Twitter | — (obligatoire) |
| `description` | Meta description, Open Graph | — (obligatoire) |
| `schema` | Bloc JSON-LD injecté : `home`, `service`, `departement`, `ville`, `article` | aucun |
| `breadcrumb` | Nom de la page dans le `BreadcrumbList` | `title` |
| `parent_nom` / `parent_url` | Niveau intermédiaire du fil d'Ariane | aucun |
| `zone_nom` / `zone_parent` | `areaServed` des schémas départementaux et communaux | aucun |
| `image` | Vignette Open Graph | `/assets/img/og-default.jpg` |
| `date` | `datePublished` des articles | date du build |
| `priority` | Priorité au sitemap | `0.6` |
| `sitemap: non` | Exclut la page du sitemap | incluse |
| `robots: noindex` | Force le `noindex` sur cette page | valeur globale |
| `faq: non` | Désactive la génération du `FAQPage` | activée |
| `conversion` | Attribut `data-conversion` sur `<body>` (page de remerciement) | aucun |

Le `FAQPage` est **dérivé des blocs `<details>` réellement affichés**
(`scripts/faq-jsonld.pl`). Le balisage ne peut donc jamais diverger du texte
visible, ce que Google exige.

Le `BreadcrumbList` est généré à partir de `breadcrumb`, `parent_nom` et
`parent_url` : il correspond exactement au fil d'Ariane affiché.

---

## Organisation des fichiers

```
src/
  config.sh              toutes les valeurs globales
  avis.tsv               avis clients — VIDE, à ne jamais inventer
  photos.sh              markup <picture> généré, ne pas modifier à la main
  partials/              head, header, footer, formulaire, carte, JSON-LD
  pages/
    index.html           accueil
    services.html        sommaire des prestations
    degorgement*.html    19 pages de prestation + 60 pages communales
    departements/        6 pages départementales
    blog/                index + 12 articles
    …                    tarifs, devis, contact, faq, à-propos, mentions…
static/
  .htaccess              configuration Apache, copiée telle quelle
  envoi-demande.php      traitement du formulaire
  manifest.webmanifest
  assets/
    css/style.css        design system complet (jetons, composants)
    js/site.js           menu, micro-interactions, carte, consentement, mesure
    fonts/               Inter et Plus Jakarta Sans, variables, auto-hébergées
    vendor/leaflet/      Leaflet 1.9.4 (BSD 2-Clause), auto-hébergé
    img/                 favicon et icônes d'application
    img/interventions/   photographies, 5 largeurs × 2 formats
    img/schemas/         schémas techniques
    img/partage/         images Open Graph (JPEG 1200×630)
photos-source/           photographies d'origine, source de la chaîne images
scripts/
  build.sh               construit public/ et refuse un résultat non déployable
  gen-sitemap.sh         sitemap.xml + robots.txt
  faq-jsonld.pl          FAQPage dérivé des <details>
  check-seo.sh           17 familles de contrôles SEO, GEO, liens, périmètre
  check-html.py          structure HTML, hiérarchie des titres, labels
  check-contenu-local.py similarité des pages locales (anti-duplication)
  check-contraste.py     contrastes mesurés sur la page rendue (WCAG 1.4.3)
  check-responsive.py    11 largeurs d'appareil : débordements, images, cibles
  audit.sh               enchaîne tous les contrôles
  test-http.sh           sert public/ et interroge toutes les URLs (aucun 403)
  apercu.sh              aperçu local avec les URLs de production
  routeur-local.php      reproduit les règles du .htaccess en local
  preparer-logo.py       détoure et vectorise le logo, en tire favicon et icônes
  generer-visuels.py     régénère les schémas techniques et les images de
                         partage, rendus en WebP et JPEG par Chromium
  preparer-photos.py     dérivés AVIF/WebP des photographies + src/photos.sh
  placer-photos.py       répartit photographies et schémas dans les pages
  refonte-heros.py       applique le gabarit de héros aux pages intérieures
  refonte-articles.py    applique le gabarit d'article et génère les sommaires
  capturer.py            captures d'écran des pages, pour contrôle visuel
tests/
  lancer.sh              parcours réels dans un navigateur (facultatif)
  navigateur.mjs
docs/
  configuration.md       référence de src/config.sh
  design-system.md       couleurs, typographie, composants, contrastes
  deploiement-hostinger.md
.github/workflows/deploy.yml
```

`public/` est **régénéré à chaque build** et n'est pas versionné sur la branche
source :
c'est la branche `deploy` qui porte le site prêt à servir.

---

## Design system

Couleurs, typographie, composants, règles de contraste et de mouvement :
**[`docs/design-system.md`](docs/design-system.md)**.

En résumé : bleu azur dominant, orange réservé à l'urgence et aux appels à
l'action, Plus Jakarta Sans pour les titres et Inter pour le texte, deux
polices variables auto-hébergées. Tout passe par des variables CSS déclarées
en tête de `static/assets/css/style.css` ; aucune page n'écrit de couleur en
dur.

---

## Logo

`logo-source/logo-original.webp` est la source unique. Pour le remplacer :

```bash
cp nouveau-logo.png logo-source/logo-original.webp
python3 scripts/preparer-logo.py
bash scripts/build.sh
```

Le script détoure le fond, ramène l'image à ses deux encres, la vectorise avec
`potrace` et produit d'un coup : le logo de l'en-tête, sa variante claire pour
le pied de page (sans quoi l'encre sombre disparaîtrait sur le bleu nuit), le
monogramme, le favicon vectoriel, le `.ico` et les quatre icônes
d'application. Il n'y a rien d'autre à toucher : l'en-tête et le pied de page
pointent vers des chemins fixes.

> L'ancien `scripts/generer-images.py`, qui dessinait une goutte faute de logo,
> a été supprimé. Il écrivait les mêmes fichiers : l'avoir laissé en place
> aurait suffi à écraser le vrai logo par le provisoire à la première
> exécution distraite.

Le logo porte « DEBOUCHEUR RICHARD », le site « Dégorgement Richard ». Les
deux cohabitent, mais c'est une décision de marque à trancher — voir
[`docs/design-system.md`](docs/design-system.md), section Logo.

---

## Photographies, carte et avis

### Photographies

Dix photographies d'intervention vivent dans `photos-source/`. Elles sont la
**source** : `scripts/preparer-photos.py` en tire cinq largeurs (480 → 1536)
en AVIF et WebP, puis écrit `src/photos.sh`, où chaque variante d'affichage
devient un bloc `<picture>` complet. Une page écrit `{{PHOTO_EVIER_HERO}}` et
hérite du `srcset`, du `sizes`, des dimensions réelles et du texte alternatif.

Chaque photographie appartient à une **famille**, qui décide de son dossier :
`interventions/`, `debouchage/`, `degorgement/`, `plomberie/`, `camera/` sont
peuplées ; `curage/`, `assainissement/`, `avant-apres/` et `zones/<code>/`
attendent leurs premières prises de vue. Un dossier n'est créé que lorsqu'une
photographie l'occupe.

Pour ajouter une photographie :

```bash
cp ma-photo.webp photos-source/curage-canalisation-hydrocureur.webp
$EDITOR scripts/preparer-photos.py     # déclarer alt, légende et famille
python3 scripts/preparer-photos.py     # dérivés + markup + vignette de partage
bash scripts/build.sh
```

Le texte alternatif et la légende se déclarent dans le dictionnaire `PHOTOS`
en tête de `scripts/preparer-photos.py` — un seul endroit, pour qu'une
description ne puisse pas diverger d'une page à l'autre.

**Ils ne décrivent que ce que la photographie montre.** Pas de lieu, pas de
date, pas de résultat, pas de client : rien qui ne soit visible à l'image. Une
photographie légendée « intervention à Saint-Brieuc » alors que rien ne le
prouve est exactement le genre de détail qui ruine la crédibilité du reste.

Photographies et schémas ne jouent pas le même rôle : la photographie ouvre
la page et montre qui intervient, le schéma descend dans le texte et explique
où se forme un bouchon. `scripts/placer-photos.py` applique cette règle.

Les photographies portées par une page sont déclarées au sitemap sous
`<image:image>` : c'est ce qui les rend éligibles à Google Images. Les schémas
ne le sont pas — ils n'ont rien à y faire.

### Cas de figure et avant / après

Les pages départementales portent deux **cas de figure** chacune : problème,
diagnostic, méthode, résultat. Ils décrivent une séquence de travail, pas un
chantier passé — ni date, ni adresse, ni client. Le composant `.cas` est prêt
à recevoir de vraies interventions documentées le jour où il en existe.

Le composant `.avant-apres` existe dans la feuille de style et n'est posé sur
aucune page : il attend un couple de clichés du même ouvrage, pris avant puis
après. Deux photographies d'ouvrages différents présentées comme un avant /
après seraient un faux résultat.

### Carte des zones d'intervention

`src/partials/carte-zone.html`, affichée par `{{SECTION_CARTE}}`. Leaflet est
auto-hébergé (`static/assets/vendor/leaflet/`) et **chargé seulement après un
clic du visiteur** : les tuiles viennent d'OpenStreetMap, donc d'un tiers qui
verrait sinon l'adresse IP de chacun sans que personne l'ait demandé.

La liste des six départements est dans le HTML dès le départ : c'est elle que
lisent les moteurs de recherche et les lecteurs d'écran. Les coordonnées des
préfectures sont dans `static/assets/js/site.js` (`PREFECTURES`).

### Pages d'atterrissage départementales

`scripts/landing-departements.py` a transformé les six pages de département en
pages locales à conversion : bloc de symptômes sous le héros, cas de figure
illustrés, liste de communes, emplacement des avis, cinq appels à l'action de
formes différentes. Le script est **idempotent** — il ne retouche pas une page
déjà traitée.

Les contenus (symptômes, cas de figure, formulation des appels à l'action)
sont écrits département par département dans le dictionnaire `DEPARTEMENTS` du
script. `tests/navigateur.mjs` mesure la similarité de Jaccard entre les
quatre pages prioritaires : au-delà de 0,4, deux pages raconteraient la même
chose avec un nom substitué, et le test échoue.

### Avis clients

`src/avis.tsv`. **Le fichier est vide, et c'est volontaire** : aucun avis n'a
été inventé. Tant qu'aucune ligne n'est renseignée, la section n'est pas
publiée du tout — mieux vaut pas de section qu'une section vide.

Pour l'activer, recopiez-y de vrais avis reçus, avec l'accord des personnes
concernées ; le format est décrit en tête du fichier.

> Un faux témoignage est une pratique commerciale trompeuse (article L121-2
> du code de la consommation), et Google supprime les fiches qui en publient.
>
> Ces avis ne sont volontairement **pas** balisés en JSON-LD : Google
> interdit le balisage d'avis que l'on collecte soi-même à son propre sujet.
> Pour obtenir des étoiles dans les résultats de recherche, il faut passer par
> la fiche d'établissement Google.

---

## Modifier le site

### Téléphone, adresse, horaires, zone, tarifs

Tout est dans `src/config.sh`, et **nulle part ailleurs**. Le numéro de
téléphone y figure une seule fois et se propage à l'en-tête, au héros, aux
appels à l'action, au pied de page, aux 111 pages, au formulaire, à la barre
mobile et aux données structurées.

```bash
sed -i 's/^TELEPHONE=.*/TELEPHONE="02 20 06 00 75"/' src/config.sh
bash scripts/build.sh
```

`scripts/check-seo.sh` refuse un second numéro de téléphone sur le site : si
un `tel:` différent apparaît quelque part, le contrôle échoue.

### Ajouter une page de prestation

1. Copier une page existante de `src/pages/` (par exemple `debouchage-evier.html`).
2. Adapter le bloc `<!--meta`, en gardant `schema: service`.
3. Écrire le contenu, en conservant le bloc `<div class="reponse-rapide">` :
   `check-seo.sh` l'exige sur toute page de prestation, de département ou de
   commune.
4. Ajouter le lien dans `src/partials/footer.html` et sur `services.html` —
   une page qu'aucune autre ne lie est signalée comme orpheline.

### Ajouter une page communale

Les pages communales s'appellent `src/pages/degorgement-<commune>.html` et
produisent l'URL `/degorgement-<commune>`.

**Une page communale doit avoir un contenu réellement propre à la commune.**
`scripts/check-contenu-local.py` compare les 66 pages locales deux à deux sur
les 5-grammes de mots de leur contenu éditorial :

* au-delà de **42 %** de similarité : avertissement, à traiter ;
* au-delà de **60 %** : échec, la page ne doit pas être publiée ;
* en dessous de **380 mots** de contenu propre : avertissement — la commune ne
  justifie probablement pas une page autonome, traitez-la dans la page
  départementale.

Concrètement, une page communale utile parle du bâti local, du type de réseau
qu'on y rencontre, des problématiques réellement observées, des communes
alentour et répond à des questions locales. Remplacer un nom de ville dans un
texte type ne passe pas ce contrôle, et ne se positionne pas.

### Ajouter un article de blog

`src/pages/blog/<slug>.html`, avec `schema: article`, `date`,
`parent_nom: Conseils canalisations` et `parent_url: /blog/`. Ajouter la carte
correspondante dans `src/pages/blog/index.html`.

### Modifier le menu ou le pied de page

`src/partials/header.html` et `src/partials/footer.html`. Une seule
modification se répercute sur les 111 pages au build suivant.

### Remplacer les illustrations par des photographies

Les visuels du site sont des **illustrations originales** produites par
`scripts/generer-visuels.py`, et non des photographies : l'environnement de
construction n'a accès à aucune banque d'images. Elles n'appartiennent donc
à personne d'autre — aucun filigrane, aucun logo tiers, aucune licence à
respecter au-delà de celle du dépôt.

Pour passer à de vraies photographies, déposez un fichier WebP de **mêmes nom
et dimensions** dans `static/assets/img/photos/`. Le HTML référence les
fichiers par leur nom et porte déjà `width`, `height`, `loading`, `decoding`
et `alt` : aucune page n'est à modifier. Vérifiez seulement que la
photographie est libre de droits pour un usage commercial et que le texte
alternatif la décrit toujours. L'inventaire complet, avec dimensions et
textes alternatifs, est dans `static/assets/img/photos/README.md`.

---

## Le formulaire de demande

`static/envoi-demande.php`, affiché par `src/partials/formulaire-devis.html`.

Champs : nom, téléphone, e-mail, ville, **département** (liste fermée aux six
départements couverts), code postal, type de problème, degré d'urgence,
description, photo facultative, consentement.

Chaîne de contrôle côté serveur :

1. méthode `POST` uniquement ;
2. limitation à cinq envois par heure et par adresse IP ;
3. piège à robots (champ hors écran) et horodatage minimal ;
4. validation et nettoyage de chaque champ, avec neutralisation de l'injection
   d'en-têtes ;
5. **cohérence entre le code postal et le département choisi** ;
6. contrôle réel du fichier joint (type MIME lu dans le fichier, image
   déchiffrable) ;
7. envoi, puis redirection 303 vers `/merci`.

Le message de succès n'est **jamais** affiché sans envoi réel : en cas d'échec
de `mail()`, une page d'erreur explicite est retournée avec le numéro de
téléphone en repli.

**Avant la mise en ligne**, créez la boîte `EMAIL_EXPEDITEUR` dans hPanel :
sur un mutualisé, un expéditeur hors domaine est rejeté ou classé en
indésirable (SPF/DKIM).

---

## Google Search Console, Analytics, Tag Manager

Trois identifiants, tous dans `src/config.sh`, tous vides par défaut :

| Clé | Valeur | Effet si vide |
|---|---|---|
| `GA4_ID` | `G-XXXXXXXXXX` | aucun script tiers chargé, aucun bandeau cookies |
| `GTM_ID` | `GTM-XXXXXXX` | idem — n'utilisez pas GA4 et GTM ensemble |
| `GSC_CODE` | contenu de l'attribut `content` fourni par Search Console | aucune balise écrite |

Tant qu'aucun identifiant n'est renseigné, **aucun cookie n'est déposé** et le
bandeau de consentement ne s'affiche pas. Dès qu'un identifiant est présent, le
bandeau apparaît et rien n'est chargé avant acceptation explicite
(`static/assets/js/site.js`).

Pour Search Console, la vérification par fichier HTML ou par DNS est préférable :
elle ne pèse rien sur les pages.

---

## Contrôles avant mise en ligne

```bash
bash scripts/audit.sh
```

| Étape | Ce qu'elle vérifie |
|---|---|
| `build.sh` | pages générées, `index.html` à la racine, aucune couche superflue, ressources présentes, aucun token non résolu, aucun département hors zone, permissions 755/644 |
| `check-seo.sh` | titles et descriptions uniques et calibrés, H1 unique, `alt` et dimensions des images, liens internes, pages orphelines, canoniques, Open Graph, `BreadcrumbList`, blocs « Réponse rapide » (GEO), périmètre des six départements, un seul numéro de téléphone, fichiers requis, redirections 301, questions FAQ non dupliquées, cohérence indexation/sitemap, poids |
| `check-html.py` | balises équilibrées, hiérarchie des titres, identifiants uniques, ancres valides, étiquetage des champs |
| `check-contenu-local.py` | similarité des pages locales, longueur minimale |
| JSON-LD | validité de chaque bloc de données structurées |
| `test-http.sh` | toutes les URLs du sitemap en 200, redirections 301, 404 personnalisée, **aucun 403** |
| `check-contraste.py` | rapport de contraste de chaque texte, mesuré sur la page **rendue** (dégradés et images compris) — 4,5:1, ou 3:1 pour un grand texte |
| `check-responsive.py` | 16 gabarits × 11 largeurs d'appareil : débordement du document, élément hors cadre, image qui déborde ou se déforme, contenu tronqué, cible tactile |

Le build **échoue** (code de sortie ≠ 0) si le dossier produit n'est pas
déployable. Un build qui n'a pas planté n'est pas un build valide : c'est
exactement ce qui produit un 403 sur Hostinger.

---

## DEPLOYMENT HOSTINGER

### En une ligne

Le workflow GitHub construit le site et publie **le contenu de `public/` à la
racine de la branche `deploy`**. Hostinger clone cette branche dans
`public_html/`. `index.html` s'y trouve au premier niveau.

```
git push (branche source)  →  GitHub Actions  →  branche deploy  →  Hostinger  →  public_html/index.html  →  HTTP 200
```

### Pourquoi une branche `deploy`

Le déploiement Git de Hostinger, sur une offre mutualisée, se contente de
cloner le dépôt dans le dossier choisi. Il n'exécute **aucun** build : ni npm,
ni script shell, ni `post-receive`.

Un dépôt dont la page d'accueil se trouve dans un sous-dossier produit donc une
racine web sans `index.html`. Apache, faute de fichier d'index et avec
`Options -Indexes`, répond **403 Forbidden**. C'est la cause exacte du 403
rencontré sur le projet précédent.

La branche `deploy` supprime le problème à la racine : elle ne contient que le
site, `index.html` au premier niveau, sans `public/`, sans `src/`, sans
`scripts/`.

Le workflow vérifie explicitement, après la poussée :

```bash
test -f index.html    || exit 1   # sinon Apache renverrait 403
test ! -d public      || exit 1   # sinon deploy/public/index.html → 403
```

### Configuration dans hPanel

1. **Sites → votre domaine → Avancé → Git**.
2. *Repository* : `https://github.com/davidseo1312/Dego-richard.git`
   (ou l'URL SSH si le dépôt est privé — déposez alors la clé publique
   d'Hostinger dans **Settings → Deploy keys** sur GitHub).
3. **Branch : `deploy`** — jamais la branche source.
4. **Directory : `public_html`** — laissez le champ vide s'il correspond déjà
   à la racine web. **Ne mettez jamais `public_html/public`.**
5. *Create*, puis *Deploy*.

Hostinger clone alors le contenu de `deploy` dans `public_html/` :

```
public_html/
  index.html          ← servi par Apache
  .htaccess
  robots.txt
  sitemap.xml
  404.html
  envoi-demande.php
  assets/
  departements/
  blog/
  degorgement-rennes.html …
```

### Déploiement automatique

hPanel affiche une **Webhook URL** dans la même page Git. Copiez-la, puis sur
GitHub : **Settings → Webhooks → Add webhook**, *Payload URL* = l'URL copiée,
*Content type* = `application/json`, événement `push`. Chaque publication sur
`deploy` déclenche alors la mise à jour du site.

### Vérifications après déploiement

```bash
curl -I https://degorgement-richard.fr/                     # 200
curl -I https://degorgement-richard.fr/degorgement-rennes   # 200
curl -I https://degorgement-richard.fr/robots.txt           # 200
curl -I https://degorgement-richard.fr/sitemap.xml          # 200
curl -I https://degorgement-richard.fr/page-inexistante     # 404, pas 403
curl -I https://degorgement-richard.fr/.git/config          # 403 (attendu)
```

### Si le site renvoie encore 403

Dans l'ordre :

1. **`index.html` est-il à la racine de `public_html/` ?** Regardez le
   gestionnaire de fichiers hPanel. Si vous voyez `public_html/public/index.html`,
   le dossier de déploiement est mal réglé : corrigez-le, ne déplacez pas les
   fichiers à la main.
2. **La branche déployée est-elle `deploy` ?** La branche source ne contient pas de
   `public/` versionné : la racine web serait vide.
3. **Permissions.** Dossiers `755`, fichiers `644`. `build.sh` les applique,
   mais un dépôt par FTP peut les écraser.
4. **`.htaccess`.** Aucune directive n'y refuse une page du site. Si le serveur
   renvoie 500 sur *toutes* les pages, commentez la ligne `Options -MultiViews
   -Indexes` : quelques offres mutualisées interdisent `Options` en `.htaccess`.

Le détail complet, étape par étape, figure dans
[`docs/deploiement-hostinger.md`](docs/deploiement-hostinger.md).

### Le workflow GitHub Actions

`.github/workflows/deploy.yml`, déclenché par une poussée sur la branche source
(`claude/plumbing-site-brittany-eoxa6x`, ou `main`) :

1. checkout ;
2. `scripts/build.sh` ;
3. `scripts/check-seo.sh` ;
4. `scripts/check-html.py` ;
5. `scripts/check-contenu-local.py` ;
6. validation de tous les blocs JSON-LD ;
7. `php -l` sur le script du formulaire ;
8. `scripts/test-http.sh` — toutes les URLs, aucun 403 ;
9. vérification que `public/` est servable tel quel (`index.html`, `.htaccess`,
   `robots.txt`, `sitemap.xml`, `404.html`, aucune couche superflue) ;
10. publication du **contenu** de `public/` à la racine de `deploy`, avec
    vérification finale de `index.html` et de l'absence de `public/`.

Aucun secret n'est nécessaire : `GITHUB_TOKEN` suffit.

> Le workflow ne publie que depuis les branches listées dans son déclencheur
> `push`. Depuis toute autre branche, lancez-le manuellement depuis l'onglet
> **Actions** (`workflow_dispatch`), ou fusionnez d'abord dans la branche
> source.

---

## Cohérence géographique et commerciale

Trois points ont été tranchés explicitement, et méritent d'être connus avant
toute modification.

**1. Le siège social est en Île-de-France, l'activité est dans le Grand Ouest.**
`RAISON_SOCIALE`, `SIRET` et l'adresse du siège proviennent du registre national
et sont repris à l'identique du site de serrurerie exploité par la même entité.
Le balisage `LocalBusiness` utilise donc **l'adresse réelle du siège**, et non
une adresse bretonne inventée. Le site n'affiche jamais « agence à [ville] »,
seulement « intervention à [ville] », et la page
[zone d'intervention](src/pages/zone-intervention.html) l'explique au visiteur.
Si un établissement est un jour immatriculé dans la zone, renseignez
`ADRESSE_RUE`, `ADRESSE_CP`, `ADRESSE_VILLE`, `LATITUDE` et `LONGITUDE` dans
`src/config.sh` : le balisage suivra.

**2. Le code APE déclaré est 81.29A** (désinfection, désinsectisation,
dératisation). Le débouchage et le curage relèvent du 37.00Z ou du 43.22B. À
faire corriger auprès de l'INSEE, et **vérifier que la RC Pro couvre bien
l'assainissement** avant la première intervention.

**3. Six départements, et aucun autre.** Le périmètre est verrouillé à trois
niveaux : `build.sh` échoue si un département hors zone apparaît dans une page,
`check-seo.sh` le contrôle également, et le formulaire refuse une demande dont
le département n'est pas dans la liste. Le sitemap ne contient aucune page hors
de ces six départements.

---

## Avant la mise en ligne : informations à fournir

`scripts/check-seo.sh` liste ces champs à chaque exécution. Ils sont entre
crochets dans `src/config.sh` parce qu'ils **ne peuvent pas être devinés** :
ce sont des obligations légales ou des données contractuelles.

| Clé | Nature |
|---|---|
| `ASSUREUR_RCPRO`, `POLICE_RCPRO` | Responsabilité civile professionnelle — art. L.243-2 du code des assurances |
| `ASSUREUR_DECENNALE` | Garantie décennale |
| `MEDIATEUR_NOM`, `MEDIATEUR_URL` | Médiateur de la consommation — art. L.616-1 du code de la consommation |
| `TAUX_HORAIRE`, `FRAIS_DEPLACEMENT`, `MAJORATION_NUIT`, `FORFAIT_*` | Affichage des prix — arrêté du 24 janvier 2017 |
| `DOMAINE`, `BASE_URL` | Nom de domaine retenu — `degorgement-richard.fr` est un choix par défaut, à confirmer |

Les forfaits du site de serrurerie **n'ont pas été repris** : ouvrir une porte
et hydrocurer un collecteur n'ont ni le même matériel, ni la même durée, ni la
même assurance. Tant que les montants réels ne sont pas renseignés, la page
`/tarifs` explique les facteurs de prix et renvoie au devis, sans afficher de
chiffre inventé.

Rien d'autre n'a été inventé sur ce site : aucun avis client, aucune note
moyenne, aucune certification, aucune ancienneté, aucune agence locale, aucun
prix.

---

## Sécurité

* Aucun secret dans le dépôt. `.env` est ignoré par Git **et** refusé par le
  `.htaccess`. `.env.exemple` ne contient que des champs vides.
* Le `.htaccess` refuse `/.git`, `/.github`, `/src`, `/scripts`, `/tests`,
  `/docs` et les fichiers `.env`, `.sh`, `.ini`, `.log`, `.sql`, `.yml`, `.md`.
* En-têtes de sécurité : `X-Content-Type-Options`, `Referrer-Policy`,
  `X-Frame-Options`, `Permissions-Policy`, `Content-Security-Policy`.
  HSTS est présent mais **commenté** : à activer une fois le certificat HTTPS
  confirmé, la directive étant mémorisée deux ans par le navigateur.
* Le formulaire neutralise l'injection d'en-têtes, limite les envois par IP,
  contrôle le type MIME réel des fichiers joints et n'écrit rien dans la racine
  web.
* Aucun cookie n'est déposé tant qu'aucun identifiant de mesure d'audience
  n'est configuré, et jamais avant consentement explicite.
