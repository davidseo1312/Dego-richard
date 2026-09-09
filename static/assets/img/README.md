# Images du site

Deux familles de fichiers cohabitent ici, produites par deux scripts
différents. Aucune n'est à retoucher à la main : ce sont les scripts qui font
foi, une retouche serait perdue à la régénération suivante.

## Icônes et favicon — `scripts/generer-images.py`

| Fichier | Rôle |
|---|---|
| `favicon.svg` | icône d'onglet, écrite à la main (vectorielle) |
| `favicon.ico` | repli 16/32/48 px pour les navigateurs anciens |
| `apple-touch-icon.png` | 180 px, écran d'accueil iOS |
| `icone-192.png`, `icone-512.png` | manifeste d'application |
| `icone-512-maskable.png` | variante à marge de sécurité (Android) |

## Images de partage — `scripts/generer-visuels.py`

Les fichiers `og-*.jpg` (1200 × 630) sont les vignettes affichées lorsqu'une
page est partagée sur un réseau social ou une messagerie. Elles reprennent les
visuels du site, surmontés d'un cartouche de marque.

Le format est imposé : un SVG n'est pas affiché par les réseaux sociaux, et
WebP y reste inégalement pris en charge. JPEG est la seule combinaison
acceptée partout. Chaque page désigne la sienne par la clé `image:` de son
bloc de métadonnées ; `og-default.jpg` sert de valeur par défaut.

Le numéro de téléphone n'y est **pas** incrusté : ces images sont mises en
cache des mois par les plateformes, et un numéro périmé y ferait plus de
dégâts que son absence.

## Visuels du site — `photos/`

Voir [`photos/README.md`](photos/README.md) : origine, licence, inventaire, et
la marche à suivre pour remplacer une illustration par une photographie.
