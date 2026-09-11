# Images du site

Deux familles de fichiers cohabitent ici, produites par deux scripts
différents. Aucune n'est à retoucher à la main : ce sont les scripts qui font
foi, une retouche serait perdue à la régénération suivante.

## Logo, icônes et favicon — `scripts/preparer-logo.py`

Le logo fourni par l'entreprise est dans `logo-source/logo-original.webp`.
C'est la **source** : tout le reste en dérive, et rien ici ne se retouche à la
main.

| Fichier | Rôle |
|---|---|
| `logo/logo-deboucheur-richard.svg` | logo de l'en-tête, vectoriel |
| `logo/logo-deboucheur-richard-clair.svg` | variante encre claire, pour le pied de page |
| `logo/logo-deboucheur-richard{,-clair}-480.{png,webp}` | repli matriciel pour les contextes sans vectoriel (signature de courriel, impression) |
| `logo/monogramme.png` | pictogramme seul, isolé du bloc de texte |
| `favicon.svg` | icône d'onglet, vectorielle — c'est elle que servent les navigateurs récents |
| `favicon.ico` | repli 16/32/48 px, fond opaque |
| `apple-touch-icon.png` | 180 px, écran d'accueil iOS — **jamais transparent**, iOS composerait sur du noir |
| `icone-192.png`, `icone-512.png` | manifeste d'application |
| `icone-512-maskable.png` | variante à marge de sécurité : Android rogne jusqu'à 20 % de chaque bord |

Le script détoure le fond blanc du fichier fourni, ramène chaque pixel à l'une
des deux encres du logo (`#0d1d28` et `#00abf3`, déjà alignées sur la palette
du site), puis vectorise chaque encre avec `potrace` et recompose un SVG
unique. Résultat : 23 Ko de SVG — 10 Ko une fois compressé par le serveur —
net à toutes les définitions, là où il aurait fallu deux bitmaps de 31 et
51 Ko pour un rendu moins bon.

> Le script **remplace** l'ancien `generer-images.py`, qui dessinait une
> goutte faute de logo. Deux scripts ne doivent pas se disputer les mêmes
> fichiers : celui-là a été supprimé, faute de quoi une exécution distraite
> aurait écrasé le vrai logo par le provisoire.

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

## Photographies d'intervention — `scripts/preparer-photos.py`

Les photographies fournies par l'entreprise sont déposées dans
`photos-source/` à la racine du dépôt, puis déclarées dans le dictionnaire
`PHOTOS` du script. Chacune y indique **ce qu'elle montre** (`alt`,
`legende`) et **à quelle famille elle appartient** (`famille`). Le script
produit alors, dans `/assets/img/<famille>/` :

* cinq largeurs (480, 768, 1024, 1366, 1536 px) en AVIF **et** en WebP ;
* le markup `<picture>` complet — `srcset`, `sizes`, `width`, `height`,
  `alt`, chargement — écrit dans `src/photos.sh` sous quatre variantes
  (`HERO`, `MEDIA`, `CARTE`, `LARGE`) ;
* la vignette de partage `partage/og-<slug>.jpg`.

Une page n'écrit alors que `{{PHOTO_REGARD_MEDIA}}` : les dimensions
déclarées sont celles des fichiers réellement produits, ce qui supprime tout
décalage de mise en page au chargement.

### Familles

Une famille est un dossier. Elle n'existe que lorsqu'une photographie
l'occupe : le projet ne crée pas de dossier vide.

| Famille | Ce qu'elle contient | Peuplée |
|---|---|:--:|
| `interventions/` | vue générale d'une intervention, sans matériel spécifique | ✅ |
| `debouchage/` | dépose de siphon, débouchage d'un appareil sanitaire | ✅ |
| `degorgement/` | rétablissement d'un écoulement, aspiration | ✅ |
| `plomberie/` | pièces d'évacuation : siphon, bonde, broyeur, raccordement | ✅ |
| `camera/` | inspection vidéo, regard ouvert, écran de contrôle | ✅ |
| `curage/` | hydrocureur, enrouleur haute pression, buse | — |
| `assainissement/` | fosse, préfiltre, épandage, bac à graisses | — |
| `avant-apres/` | **couples** de clichés du même ouvrage, avant puis après | — |
| `zones/22/` … `zones/49/` | prise de vue dont le lieu est réellement identifiable | — |

Pour ajouter une photographie : la déposer dans `photos-source/` sous un nom
descriptif (`curage-canalisation-hydrocureur.webp`), ajouter son entrée dans
`PHOTOS` avec sa famille, relancer `python3 scripts/preparer-photos.py`, puis
poser `{{PHOTO_<CLÉ>_<VARIANTE>}}` dans la page voulue.

**Règle absolue** : le texte alternatif et la légende ne décrivent que ce que
la photographie montre. Ni lieu, ni date, ni résultat, ni client — rien qui ne
soit visible à l'image.

## Schémas techniques — `schemas/`

Voir [`schemas/README.md`](schemas/README.md). Ils sont entièrement bleus :
le rouge n'y apparaît que là où il signale un incident (refoulement, danger)
ou une convention établie (repère d'eau chaude). Aucune couleur chaude
décorative.
