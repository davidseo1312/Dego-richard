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
| `.galerie` (`.mise-en-avant`) | galerie 3 colonnes, première vignette en 2×2 |
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

## 7. Performance

| Ressource | Poids |
|---|---|
| CSS | ~56 Ko non compressé, un seul fichier, aucune dépendance |
| JS | ~16 Ko, sans framework, chargé en `defer` |
| Polices | 75 Ko, deux fichiers variables, préchargés |
| Visuel du héros | ~38 Ko en WebP, `fetchpriority="high"` |
| Bibliothèque de visuels | 15 fichiers, ~350 Ko au total |

Les images hors écran portent `loading="lazy"` et `decoding="async"` ; toutes
déclarent `width` et `height`, ce qui supprime le décalage de mise en page.
