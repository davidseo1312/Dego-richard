# Design system

Tout ce qui suit vit dans un seul fichier : `static/assets/css/style.css`.
Aucune page n'écrit de couleur, de rayon ou d'espacement en dur. Changer une
teinte ici la change sur les 111 pages au build suivant — c'est la raison
d'être de ce document autant que du fichier.

---

## 1. Couleurs

L'identité est **entièrement bleue**. Le bleu clair porte les aplats, les
badges et les fonds ; le bleu profond porte le texte, les liens et les boutons
pleins ; le bleu nuit est réservé au pied de page et aux quelques surfaces qui
demandent un contraste fort. Le blanc domine en surface.

### Rôles — ce que les composants écrivent

| Jeton | Valeur | Emploi |
|---|---|---|
| `--color-primary` | `#38bdf8` | aplats, badges, icônes, décor |
| `--color-primary-dark` | `#0284c7` | éléments interactifs |
| `--color-primary-deep` | `#0369a1` | **texte et boutons pleins** — 5,9:1 sur blanc |
| `--color-primary-light` | `#e0f2fe` | cercles d'icône, pastilles, bordures douces |
| `--color-primary-soft` | `#f0f9ff` | fonds de section alternés |
| `--color-accent` | `#0ea5e9` | action secondaire, traits d'accent |
| `--color-dark` | `#0f172a` | pied de page |
| `--color-text` | `#1e293b` | texte courant — 13,6:1 sur blanc |
| `--color-text-secondary` | `#5b687d` | texte secondaire |
| `--color-background` | `#f8fafc` | fond neutre |
| `--color-background-blue` | `#f0f9ff` | fond bleu très clair |
| `--color-border` | `#e2e8f0` | filets |
| `--shadow-soft` | `0 10px 30px rgba(15,23,42,.06)` | ombre par défaut |

Une **échelle** (`--bleu-50` … `--bleu-900`, `--nuit`) est déclarée à côté. Les
rôles y pointent : la couleur principale peut changer de place dans l'échelle
sans qu'un seul composant ne bouge.

### Le seul écart à la palette fournie

`--color-text-secondary` devait être `#64748b`. Posé sur le bleu très pâle des
sections alternées (`#f0f9ff`), il tombe à **4,48:1** — sous le seuil AA de
4,5. Assombri de deux crans à `#5b687d`, il tient 5,4:1 sur ce même fond et
reste visuellement un gris-bleu secondaire. Écart mesuré, pas supposé.

### Pourquoi il n'y a plus d'orange

L'identité précédente réservait un orange aux appels à l'action. Il a été
retiré : la direction demandée est monochrome bleue, et un bouton d'appel en
bleu profond sur fond blanc, ou blanc sur fond bleu soutenu, se détache
suffisamment. La hiérarchie repose désormais sur la **valeur** (clair/foncé)
plutôt que sur la teinte.

Le compromis mérite d'être connu : un accent chaud attire l'œil plus vite
qu'un contraste de valeur. Si le taux d'appel devait baisser, c'est la piste
à rouvrir en premier.

### Boutons

| Classe | Aspect | Rôle |
|---|---|---|
| `.btn-call` | dégradé bleu profond, texte blanc | **appeler** — l'action prioritaire |
| `.btn-call` dans `.bandeau-urgence` | fond blanc, texte bleu profond | inversé : un bouton bleu sur un aplat bleu ne se détacherait pas |
| `.btn-devis` | bleu vif `#0ea5e9`, texte bleu nuit — 6,2:1 | demander un devis |
| `.btn-ghost` | fond blanc, filet gris | action tertiaire |

### Alternance des fonds

Blanc → bleu très clair → blanc… C'est ce qui donne son rythme à la page. Deux
sections `.alt` qui se suivent voient la seconde repasser en blanc : sans quoi
la frontière disparaît et l'alternance ne sert plus à rien.

```
Héros            blanc
Réponse rapide   blanc
Prestations      .alt   bleu très clair
Pourquoi nous    blanc
Interventions    .alt
Comprendre       blanc
Carte des zones  .alt
Avis             blanc
Méthode          .alt
FAQ              blanc
Urgence          bleu soutenu
Appel final      bleu profond
Pied de page     bleu nuit
```

### Règle de contraste

Chaque couleur de texte tient **4,5:1** sur son fond (3:1 pour un grand texte).
Mesuré, pas déclaré : `scripts/check-contraste.py` rend le texte transparent,
capture les fonds réels et échantillonne les pixels sous chaque bloc — dégradés
et photographies compris.

### Mode sombre

Le site s'adapte à `prefers-color-scheme: dark`. Seuls les jetons changent ;
les rôles ne bougent pas.

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
| `.hero-badges` | pastilles de réassurance sous les boutons, repliables |
| `.reponse-rapide` `.definition` `.qr-liste` `.cle` | bloc GEO : réponse autoportante, puis QUI/QUOI/OÙ/QUAND/COMMENT/POURQUOI/COMBIEN en blocs — chacun se cite isolément, ce qui est l'usage qu'en fait un moteur génératif |
| `.etapes` (`.horizontale`) | chronologie numérotée, verticale sur mobile, horizontale au-delà de 900 px |
| `.galerie` (`.mise-en-avant`) | galerie 4 colonnes, première vignette en 2×2 : les cinq photographies remplissent la grille sans trou |
| `.confiance` `.confiance-icone` | les huit arguments vérifiables, icône animée au survol |
| `.schema` `.schemas-grille` | schéma technique accompagné de sa légende, dans le corps du texte |
| `.carte-bloc` `.carte-toile` `.carte-legende` `.carte-liste` | carte des zones et sa liste HTML |
| `.avis-carte` `.avis-note` `.etoile` | avis clients — inactifs tant qu'aucun avis réel n'est renseigné |
| `.bandeau-urgence` `.urgence-encart` | la seule section où l'orange domine |
| `.departements` `.departement-carte` `.numero` | les six départements |
| `.faq details` | accordéons natifs, sans JavaScript |
| `.formulaire` `.champ` `.champs` | formulaire de demande |
| `.champ-radio` `.champ-case` | l'étiquette devient la cible tactile : un bouton radio natif fait 19 px |
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
- `scroll-padding-top` pour que l'en-tête collant ne masque pas les ancres ;
- la FAQ repose sur `<details>` / `<summary>`, et non sur un `<button>` associé
  à un `<div>`. `<summary>` porte nativement le rôle de bouton et l'état
  déplié/replié : les lecteurs d'écran l'annoncent sans un seul attribut ARIA,
  et l'accordéon continue de fonctionner script désactivé. Le reconstruire à
  la main ferait perdre cette dernière propriété sans rien gagner.

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

## 9. Responsive

Le site est vérifié à **onze largeurs** — 320, 375, 390, 414, 430, 768, 820,
1024, 1280, 1440, 1920 — sur seize gabarits, soit 176 rendus, par
`scripts/check-responsive.py`. Le script mesure la page rendue et cherche cinq
choses : débordement du document, élément hors cadre, image qui déborde ou se
déforme, contenu tronqué sans défilement prévu, cible tactile trop petite ou
collée au bord.

Points de rupture :

| Seuil | Ce qui change |
|---|---|
| 480 px | la galerie passe à deux colonnes |
| 560 px | les boutons radio du formulaire passent à deux colonnes |
| 720 px | le bloc « Réponse rapide » passe à deux colonnes |
| 768 px | la barre d'action fixe disparaît au profit de l'en-tête |
| 900 px | grilles et carte des zones passent à deux colonnes |
| 980 px | le héros passe à deux colonnes |
| **1180 px** | le tiroir de navigation cède la place à la barre complète, et la chronologie passe à l'horizontale |

Le seuil de 1180 px mérite une note : à 1080 px, la barre complète — marque,
six entrées, téléphone et devis — dépassait la largeur utile et poussait
**toutes** les pages en défilement horizontal à 1280 px. C'est exactement le
genre de défaut qu'on ne voit pas dans le CSS et que la mesure trouve en une
passe.

---

## 10. Performance

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
