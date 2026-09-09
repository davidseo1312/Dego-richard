# Design system

Tout ce qui suit vit dans un seul fichier : `static/assets/css/style.css`.
Aucune page n'écrit de couleur, de rayon ou d'espacement en dur. Changer une
teinte ici la change sur les 111 pages au build suivant — c'est la raison
d'être de ce document autant que du fichier.

---

## 1. Couleurs

### Bleu azur — couleur dominante

| Jeton | Valeur | Emploi |
|---|---|---|
| `--bleu-50` | `#f0f9ff` | fonds de section très clairs |
| `--bleu-100` | `#e0f2fe` | pastilles, cercles d'icône, lavis de héros |
| `--bleu-200` | `#bae6fd` | bordures accentuées, survols |
| `--bleu-300` | `#7dd3fc` | traits décoratifs, eau dans les visuels |
| `--bleu-400` | `#38bdf8` | aplats et dégradés, jamais du texte sur blanc |
| `--bleu-500` | `#0ea5e9` | accent vif : dégradés, halos, fonds sombres |
| `--bleu-600` | `#0284c7` | dégradés, icônes sur fond clair |
| `--bleu-700` | `#0369a1` | **texte et boutons pleins** — 5,9:1 sur blanc |
| `--bleu-800` | `#075985` | survols, dégradés foncés |

### Bleu nuit

| Jeton | Valeur | Emploi |
|---|---|---|
| `--nuit` | `#0f172a` | titres, bandeau d'annonce, pied de page, sections sombres |
| `--nuit-800` | `#1e293b` | aplats secondaires sur fond sombre |

### Orange — conversion et urgence, jamais dominant

| Jeton | Valeur | Emploi |
|---|---|---|
| `--orange` | `#f97316` | accent vif **sur fond sombre** ou en aplat clair |
| `--orange-cta` | `#c2410c` | **boutons pleins** — 5,3:1 avec du blanc |
| `--orange-fonce` | `#9a3412` | survol des boutons d'appel |
| `--orange-100` | `#ffedd5` | fonds de pastille, cercle d'icône téléphone |

> **Pourquoi deux oranges.** `#f97316` sur blanc ne donne que 2,9:1 : il est
> illisible en texte et non conforme en aplat de bouton. Il reste donc réservé
> aux fonds sombres, où il atteint 6,8:1, et aux petits aplats clairs. Les
> boutons pleins prennent `--orange-cta`, seule teinte de la famille qui
> supporte du texte blanc.

### Neutres

`--texte` `#475569` · `--texte-fort` `#0f172a` · `--texte-doux` `#5b687d`
`--bordure` `#e2e8f0` · `--bordure-forte` `#cbd5e1`
`--gris-50` `#f8fafc` · `--blanc` `#ffffff`

### Deux jeux de noms, et pourquoi

Les jetons ci-dessus décrivent une **échelle** : `--bleu-100` à `--bleu-900`.
Un second jeu, déclaré juste après, décrit un **rôle** :

```css
--color-primary        --color-background        --color-text
--color-primary-dark   --color-background-soft   --color-text-strong
--color-primary-light  --color-background-tint   --color-text-secondary
--color-primary-pale   --color-surface           --color-border
--color-accent         --color-accent-light      --color-border-strong
--color-accent-strong  --color-white
```

Les deux pointent sur les mêmes couleurs et suivent tous deux le mode sombre.
L'intérêt de les avoir séparés : un rôle peut changer de place dans l'échelle
— décider que la couleur principale passe de `--bleu-500` à `--bleu-600` —
sans qu'aucun composant ne bouge. Écrire les composants avec l'échelle seule
reviendrait à figer ce choix dans cent règles.

### Règle de contraste

Chaque couleur de texte tient **4,5:1** sur son fond (3:1 pour un grand
texte : 24 px, ou 18,7 px en gras). Ce n'est pas une intention, c'est mesuré :
`scripts/check-contraste.py` rend le texte transparent, capture les fonds
réels et échantillonne les pixels sous chaque bloc. Les dégradés et les
textes posés sur une image sont donc évalués comme le voit un visiteur.

### Mode sombre

Le site s'adapte à `prefers-color-scheme: dark`. Seuls les **jetons** sont
redéfinis : les rôles, eux, ne bougent pas. Le bleu reste l'accent, l'orange
reste l'urgence.

---

## 2. Typographie

| Rôle | Famille | Graisses |
|---|---|---|
| Titres, chiffres, boutons de marque | **Plus Jakarta Sans** (`--police-titre`) | 600 → 800 |
| Texte courant, interface | **Inter** (`--police`) | 400 → 700 |

Deux fichiers, deux familles **variables**, sous-ensemble latin,
auto-hébergés dans `static/assets/fonts/` : 75 Ko au total pour toute
l'échelle de graisses. Aucune requête vers un tiers, donc aucun cookie et
aucune dépendance externe au premier rendu. Les deux fichiers sont
préchargés dans `<head>` car le H1 est l'élément LCP.

Échelle fluide, en `clamp()` :

```
h1  2 rem     → 3.35 rem
h2  1.5 rem   → 2.25 rem
h3  1.15 rem  → 1.35 rem
corps 1.0625 rem, interligne 1.68
```

---

## 3. Rayons, ombres, espacement

```
--r-xs 8px   --r-sm 12px   --r-md 16px   --r-lg 20px   --r-xl 28px
```

Trois ombres seulement, toutes à deux couches et très douces
(`--ombre-sm`, `--ombre-md`, `--ombre-lg`), plus deux ombres colorées pour
les boutons pleins. Aucune ombre lourde : c'est la marque des gabarits
vieillissants.

Espacement sur une échelle de 4 px (`--e-1` … `--e-11`). Le rythme vertical
des sections est fluide : `--section-y: clamp(3rem, 1.6rem + 5.2vw, 5.5rem)`.

Largeurs : `--largeur` 1200 px, `--largeur-etroite` 760 px pour les articles
(≈ 70 caractères par ligne, la longueur de lecture confortable).

---

## 4. Composants

| Classe | Rôle |
|---|---|
| `.btn` `.btn-call` `.btn-devis` `.btn-ghost` `.btn-large` `.btn-bloc` | boutons ; `.btn-call` est l'appel, seule action à porter l'orange plein |
| `.carte` `.carte-service` `.carte-media` `.carte-icone` `.carte-pied` | cartes : fond blanc, rayon 20 px, filet 1 px, ombre légère, survol qui soulève de 3 px |
| `.hero` `.hero-interieur` `.hero-article` `.hero-page` | quatre déclinaisons de la bande d'ouverture |
| `.reponse-rapide` `.definition` `.qr-liste` `.cle` | bloc GEO : réponse autoportante + QUI/QUOI/OÙ/QUAND/COMMENT/POURQUOI/COMBIEN |
| `.etapes` (`.horizontale`) | chronologie numérotée, verticale sur mobile, horizontale au-delà de 900 px |
| `.galerie` (`.mise-en-avant`) | galerie 4 colonnes, première vignette en 2×2 : les cinq photographies remplissent la grille sans trou |
| `.confiance` `.confiance-icone` | les huit arguments vérifiables, icône animée au survol |
| `.schema` `.schemas-grille` | schéma technique accompagné de sa légende, dans le corps du texte |
| `.carte-bloc` `.carte-toile` `.carte-legende` `.carte-liste` | carte des zones et sa liste HTML |
| `.avis-carte` `.avis-note` `.etoile` | avis clients — inactifs tant qu'aucun avis réel n'est renseigné |
| `.stats` `.reassurance` | chiffres clés et engagements |
| `.bandeau-urgence` `.urgence-encart` | la seule section où l'orange domine |
| `.departements` `.departement-carte` `.numero` | les six départements |
| `.faq details` | accordéons natifs, sans JavaScript |
| `.formulaire` `.champ` `.champs` | formulaire de demande |
| `.sur-titre` `.badge` `.pastille` `.lien-fleche` | micro-éléments |
| `.barre-mobile` | barre d'action fixe, sous 768 px |

---

## 5. Mouvement

Trois effets, tous discrets : soulèvement des cartes au survol, décalage de
la flèche des liens d'action, apparition en fondu des blocs au défilement.

L'apparition mérite une note. Elle est pilotée par `IntersectionObserver`,
mais **l'état masqué n'existe que si `<html>` porte la classe `anim`**, posée
par un script en tête de page. Sans JavaScript, script en échec, ou
`prefers-reduced-motion` demandé, aucune règle ne masque quoi que ce soit. Un
filet de sécurité révèle en outre tout après trois secondes. Une animation ne
peut pas être la condition d'affichage d'un contenu commercial.

`prefers-reduced-motion: reduce` désactive aussi les transitions, le
défilement doux et les survols qui déplacent.

---

## 6. Accessibilité

- contrastes AA vérifiés sur la page rendue (voir ci-dessus) ;
- anneau de focus visible de 3 px sur tout élément interactif ;
- lien d'évitement en premier arrêt de tabulation ;
- cibles tactiles de 24 px minimum (WCAG 2.5.8), y compris dans les listes
  denses du pied de page ; l'exception « lien en pleine phrase » n'est
  appliquée qu'aux liens réellement rendus en `display: inline` ;
- le tiroir de navigation fermé est retiré de l'ordre de tabulation par
  `visibility: hidden` — un simple décalage hors écran le laisserait
  atteignable au clavier ;
- `scroll-padding-top` pour que l'en-tête collant ne masque pas les ancres.

---

## 7. Images

Deux familles, deux rôles, et les confondre les affaiblit toutes les deux.

| | Rôle | Où |
|---|---|---|
| **Photographies** (`assets/img/interventions/`) | montrer qui intervient | ouverture de page, galerie, cartes d'article |
| **Schémas** (`assets/img/schemas/`) | expliquer où se forme un bouchon | corps du texte, accompagnés d'une légende |

Les photographies sont produites par `scripts/preparer-photos.py` en cinq
largeurs (480 → 1536) et deux formats, AVIF puis WebP en repli. Le script
écrit aussi `src/photos.sh`, où chaque variante d'affichage devient un bloc
`<picture>` complet : une page écrit `{{PHOTO_EVIER_HERO}}` et hérite du
`srcset`, du `sizes`, des dimensions réelles et du texte alternatif.

Écrire ces attributs à la main serait la garantie qu'ils divergent au premier
recadrage — et une dimension fausse produit exactement le décalage de mise en
page que `width`/`height` servent à supprimer.

`sizes` décrit la largeur que l'image occupera vraiment, mise en page
comprise. C'est cette valeur, et non `srcset` seule, qui détermine le fichier
téléchargé : sur un écran de 1440 px, le héros reçoit la version 768 px, pas
la 1536.

---

## 8. Carte des zones

Leaflet 1.9.4 (BSD 2-Clause), **auto-hébergé** dans `assets/vendor/leaflet/` :
la politique de sécurité du site interdit les scripts venus d'un CDN.

La carte n'est chargée **qu'après un clic**. Deux raisons, dans cet ordre :
les tuiles viennent d'OpenStreetMap, donc d'un tiers qui verrait l'adresse IP
de chaque visiteur sans que personne l'ait demandé ; et la bibliothèque pèse à
elle seule plus lourd que le reste de la page.

La liste des six départements, elle, est dans le HTML dès le départ. C'est
elle qui porte l'information — pour un moteur de recherche comme pour un
lecteur d'écran ; la carte ne fait que l'illustrer. Les repères marquent les
préfectures et portent une étiquette permanente : la carte reste lisible même
si les tuiles ne chargent pas.

---

## 9. Performance

| Ressource | Poids | Chargée |
|---|---|---|
| CSS | ~60 Ko non compressé, un seul fichier | toujours |
| JS | ~17 Ko, sans framework | `defer` |
| Polices | 75 Ko, deux fichiers variables | préchargées |
| Photographie du héros | ~45 Ko en AVIF à 768 px | `fetchpriority="high"` |
| Autres photographies | AVIF/WebP, 5 largeurs | `loading="lazy"` |
| Schémas techniques | 15 fichiers, ~350 Ko | `loading="lazy"` |
| Leaflet | 163 Ko | **uniquement après un clic** |

Sur un écran de 1440 px, le héros ne télécharge pas la version 1536 px mais
la 768 px : c'est `sizes` qui le décide, et c'est pour cela qu'il est calculé
à partir de la mise en page réelle plutôt qu'écrit au jugé.

Les images hors écran portent `loading="lazy"` et `decoding="async"` ; toutes
déclarent `width` et `height`, ce qui supprime le décalage de mise en page.
