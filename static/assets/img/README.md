# Images du site

Ce fichier n'est pas publié : `scripts/build.sh` retire les `.md` de `public/`.

## Ce qui est en place

| Fichier | Rôle | Type |
|---|---|---|
| `hero-degorgement.svg` | Illustration du héros de l'accueil | vectoriel |
| `debouchage-wc.svg` | Pages WC et toilettes | vectoriel |
| `debouchage-evier.svg` | Pages évier, lavabo, cuisine | vectoriel |
| `canalisation.svg` | Pages canalisation, recherche de bouchon | vectoriel |
| `canalisation-exterieure.svg` | Pages canalisation extérieure, assainissement | vectoriel |
| `hydrocurage.svg` | Pages curage et entretien | vectoriel |
| `inspection-camera.svg` | Page inspection caméra | vectoriel |
| `pompage.svg` | Page pompage | vectoriel |
| `favicon.svg` | Icône d'onglet | vectoriel |
| `favicon.ico` | Repli pour les navigateurs qui ignorent le SVG | 16/32/48 px |
| `apple-touch-icon.png` | Icône d'écran d'accueil iOS | 180 × 180 |
| `icone-192.png`, `icone-512.png` | Icônes du manifeste | PNG |
| `icone-512-maskable.png` | Icône Android « maskable », 20 % de marge | PNG |
| `og-default.jpg` | Vignette de partage sur les réseaux sociaux | 1200 × 630 |

Les illustrations sont **vectorielles** : 1 à 3 Ko chacune, nettes sur tous les
écrans, aucune version « retina » à produire, aucun surcoût de chargement. Le
site est complet et déployable tel quel.

## Remplacer par de vraies photos

Sur ce métier, une photo de chantier convertit nettement mieux qu'un
pictogramme : le visiteur veut voir un camion, un flexible, un regard ouvert.
Quand vous disposez de photos d'intervention, remplacez les SVG par des JPEG ou
WebP en gardant :

* le **même nom de fichier** — aucune page n'est à modifier ;
* les **mêmes proportions** (720 × 540 pour le héros, 640 × 420 pour les
  illustrations de service), sinon les attributs `width`/`height` des pages
  provoqueraient un décalage de mise en page ;
* un poids **inférieur à 250 Ko** : au-delà, `scripts/check-seo.sh` avertit ;
* un `alt` décrivant réellement la scène, à corriger dans la page concernée.

Photographiez avec l'accord écrit du client, et jamais de manière à rendre le
logement ou son occupant identifiables.

## Régénérer les fichiers matriciels

```bash
python3 scripts/generer-images.py     # nécessite Pillow
```

À relancer après un changement de nom commercial, de baseline ou de couleurs.
Le numéro de téléphone n'y est volontairement pas incrusté : les réseaux
sociaux mettent ces images en cache des mois, et un numéro périmé y ferait plus
de dégâts que son absence.
