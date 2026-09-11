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
| `--color-success` | `#16a34a` | jalon franchi, résultat rétabli |
| `--color-success-deep` | `#15803d` | même rôle **en texte** — 4,6:1 sur blanc |
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

### Appels à l'action : quatre formes, quatre moments

Répéter le même pavé cinq fois dans une page le rend invisible. Chaque
emplacement a donc son traitement :

| Classe | Fond | Où | Ce qu'il demande |
|---|---|---|---|
| héros | clair | ouverture | le numéro, en toutes lettres |
| `.cta-clair` | bleu très pâle, filet gauche épais | après une explication | une demande d'intervention |
| `.cta-plein` | dégradé bleu profond, texte centré | après une démonstration | l'un ou l'autre, au choix |
| `.cta-final` | bande de bas de page | avant le pied de page | un devis |

Les pages départementales en portent cinq, dans cet ordre : héros, après les
prestations, après les cas de figure, après les avis, avant le pied de page.

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

### Angles vifs

```
--r-xs 0   --r-sm 0   --r-md 0   --r-lg 0   --r-xl 0   --r-full 0
```

L'identité est **à angles vifs**. Boutons, cartes, encadrés, champs de
formulaire, pastilles d'icône, puces de liste, incrustations des schémas,
cartouche des vignettes de partage, bulles et boutons de la carte Leaflet :
tout est carré, sans exception. Un seul angle adouci au milieu se remarquerait
comme un oubli.

Les six jetons sont **conservés** plutôt que supprimés des règles. Un
composant continue d'écrire son intention — « ce bloc porte le rayon d'une
carte », « cette pastille est pleinement arrondie » — et revenir à des angles
adoucis se fait ici, en six valeurs, sans toucher à une seule règle de
composant.

Deux exceptions, et elles sont fonctionnelles :

* **Les boutons radio et les cases à cocher natifs** restent ronds et carrés
  respectivement. Cette différence de forme est ce qui distingue « un seul
  choix » de « plusieurs choix » ; l'uniformiser serait une faute
  d'utilisabilité, pas un choix de style. Leur cible tactile, elle — la
  bordure de l'étiquette — est carrée.
* **Les rayons qui décrivent un objet réel** dans les schémas techniques —
  carter de machine, céramique d'une cuvette, arête de béton d'un regard — ne
  relèvent pas de la charte et n'ont pas été touchés.

### Ombres et espacement

Trois ombres seulement, toutes à deux couches et très douces
(`--ombre-sm`, `--ombre-md`, `--ombre-lg`), plus deux ombres colorées pour
les boutons pleins. Aucune ombre lourde : c'est la marque des gabarits
vieillissants.

Espacement sur une échelle de 4 px (`--e-1` … `--e-11`). Le rythme vertical
des sections est fluide : `--section-y: clamp(3rem, 1.6rem + 5.2vw, 5.5rem)`.

Largeurs : `--largeur` 1200 px, `--largeur-etroite` 760 px pour les articles
(≈ 70 caractères par ligne, la longueur de lecture confortable).

---

## 4. Logo

Le logo fourni par l'entreprise (`logo-source/logo-original.webp`) est la
source unique. `scripts/preparer-logo.py` le détoure, le ramène à ses deux
encres et le **vectorise** ; tout le reste en dérive : variante claire du pied
de page, favicon, icônes d'application, replis matriciels.

| | Valeur | Rôle |
|---|---|---|
| encre sombre | `#0d1d28` | « DEBOUCHEUR », « EN BRETAGNE », l'eau du monogramme |
| encre claire | `#00abf3` | « RICHARD », le D, la machine, les éclaboussures |

Les deux tombent déjà sur la palette du site — `#0d1d28` contre
`--color-dark` `#0f172a`, `#00abf3` entre `--color-accent` et
`--color-primary`. Rien n'a été retouché.

**Pourquoi du vectoriel.** 23 Ko de SVG, 10 Ko une fois compressés par le
serveur, nets à toutes les définitions. Le même logo en bitmap demandait
31 Ko pour la version 320 px et 51 Ko pour la 480 px, et restait flou d'un
cran partout ailleurs. Le fichier est mis en cache une fois pour les 111
pages.

**Deux variantes, pas une recoloration.** Sur le bleu nuit du pied de page,
l'encre sombre disparaîtrait. La variante claire bascule cette encre-là en
blanc et laisse le cyan intact.

**Hauteurs.** En-tête : 2,9 rem, porté à 3,2 rem au-delà de 1400 px, réduit à
2,5 rem sous 560 px et 2,25 rem sous 360 px — la ligne « EN BRETAGNE » doit
rester lisible là où il y a la place. Pied de page : 3 rem. La largeur suit
toujours le rapport de 3,46 ; les attributs `width` et `height` de la balise
réservent la place avant chargement.

> **À trancher.** Le logo dit « DEBOUCHEUR RICHARD », le site dit
> « Dégorgement Richard » — titres, JSON-LD, nom de domaine compris. Les deux
> cohabitent aujourd'hui sans se contredire (ce sont deux métiers voisins),
> mais c'est une décision de marque, pas une décision technique.

---

## 5. En-tête

Trois zones sur une grille `auto 1fr auto` : la marque à gauche, le menu au
centre, le téléphone et le bouton d'intervention à droite.

Le menu est centré **dans l'espace laissé entre les deux blocs latéraux**, et
non sur la largeur totale de la barre. Ce n'est pas un raccourci : le bloc de
droite (téléphone + « Demander une intervention ») fait environ 415 px contre
232 px pour la marque, et un centrage mathématique ferait chevaucher le menu
et les actions dès 1440 px. `tests/navigateur.mjs` mesure l'égalité des marges
de part et d'autre du menu, ce qui est la propriété réellement visée.

Deux détails ne survivent qu'aux largeurs qui peuvent les payer : la ligne
d'accroche de la marque et l'étiquette « Appel direct » n'apparaissent qu'à
partir de 1400 px. Entre 1180 et 1339 px, le menu et le bouton perdent deux
crans de respiration. Sans ces deux réglages, la barre dépasse la largeur
utile à 1180 px et met **toutes** les pages en défilement horizontal.

Sous 1180 px, le menu devient un tiroir ; le numéro reste visible dans la
barre sous forme de raccourci, réduit à son icône sous 560 px.

---

## 6. Composants

| Classe | Rôle |
|---|---|
| `.btn` `.btn-call` `.btn-devis` `.btn-ghost` `.btn-large` `.btn-bloc` | boutons ; `.btn-call` porte l'aplat bleu profond, `.btn-devis` le bleu ciel, `.btn-ghost` le contour |
| `.carte` `.carte-service` `.carte-media` `.carte-icone` `.carte-pied` | cartes : fond blanc, rayon 20 px, filet 1 px, ombre légère, survol qui soulève de 3 px |
| `.hero` `.hero-interieur` `.hero-article` `.hero-page` | quatre déclinaisons de la bande d'ouverture |
| `.reponse-rapide` `.definition` `.qr-liste` `.cle` | bloc GEO : réponse autoportante, puis QUI/QUOI/OÙ/QUAND/COMMENT/POURQUOI/COMBIEN en blocs — chacun se cite isolément, ce qui est l'usage qu'en fait un moteur génératif |
| `.etapes` (`.horizontale`) | chronologie numérotée, verticale sur mobile, horizontale au-delà de 900 px |
| `.galerie` (`.mise-en-avant`) | galerie 4 colonnes, première vignette en 2×2 : les cinq photographies remplissent la grille sans trou |
| `.confiance` `.confiance-icone` | les huit arguments vérifiables, icône animée au survol |
| `.schema` `.schemas-grille` | schéma technique accompagné de sa légende, dans le corps du texte |
| `.carte-bloc` `.carte-toile` `.carte-legende` `.carte-liste` | carte des zones et sa liste HTML |
| `.avis-carte` `.avis-note` `.etoile` | avis clients — inactifs tant qu'aucun avis réel n'est renseigné |
| `.bandeau-urgence` `.urgence-encart` | la seule section sur fond sombre |
| `.departements` `.departement-carte` `.numero` | les six départements |
| `.faq details` | accordéons natifs, sans JavaScript |
| `.formulaire` `.champ` `.champs` | formulaire de demande |
| `.champ-radio` `.champ-case` | l'étiquette devient la cible tactile : un bouton radio natif fait 19 px |
| `.sur-titre` `.pastille` `.lien-fleche` | micro-éléments |
| `.barre-mobile` | barre d'action fixe, sous 768 px : numéro complet à gauche, demande d'intervention à droite |
| `.rassurance` `.rassurance-carte` | les quatre points de réassurance, sous le héros |
| `.problemes` | grille de symptômes : le visiteur reconnaît sa situation avant de lire |
| `.cas` `.cas-visuel` `.cas-corps` `.cas-etapes` `.cle-cas` | cas de figure : problème → diagnostic → méthode → résultat, illustré |
| `.avant-apres` (`.avant` `.apres`) | **réservé** : ne s'affiche que si un couple de clichés du même ouvrage existe |
| `.villes-liste` (`.principale`) | communes d'un département, préfecture et sous-préfectures en tête |
| `.cta-clair` `.cta-plein` | deux des quatre traitements d'appel à l'action (voir plus bas) |
| `.evacuations` | les points d'évacuation traités, en pavés cliquables |
| `.footer-departements` | les six départements, jusqu'au bas de la dernière page |

---

## 7. Mouvement

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

## 8. Accessibilité

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

## 9. Images

Deux familles, deux rôles, et les confondre les affaiblit toutes les deux.

| | Rôle | Où |
|---|---|---|
| **Photographies** (`assets/img/<famille>/`) | montrer qui intervient | ouverture de page, galerie, cartes de prestation, cas de figure |
| **Schémas** (`assets/img/schemas/`) | expliquer où se forme un bouchon | corps du texte, accompagnés d'une légende, largeur limitée à 44 rem |

Les photographies sont rangées par famille — `interventions/`, `debouchage/`,
`degorgement/`, `plomberie/`, `camera/`, et `curage/`, `assainissement/`,
`avant-apres/`, `zones/<code>/` réservées pour la suite. Le dossier n'existe
que lorsqu'une photographie l'occupe. Voir
[`static/assets/img/README.md`](../static/assets/img/README.md) pour la marche
à suivre à chaque nouvel envoi.

Les schémas sont eux aussi entièrement bleus : le rouge n'y sert qu'à signaler
un incident (refoulement, danger) ou une convention établie (repère d'eau
chaude). Aucune couleur chaude décorative — le contraire ferait mentir la
page d'à côté.

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

## 10. Carte des zones

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

## 11. Responsive

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

## 12. Performance

### Versionnement des ressources

Feuilles de style, scripts et icônes sont servis `immutable` pour un an. Leur
URL porte donc une empreinte de leur contenu — `style.css?v=c3ea0a87` — sans
quoi un visiteur déjà venu garderait l'ancienne version pendant un an sans
même la revalider, et ne verrait jamais une refonte. Le HTML, servi en
`must-revalidate`, pointe toujours vers la bonne empreinte.

C'est un vrai piège, et il a été rencontré : le logo est apparu en pleine
largeur chez un visiteur dont le navigateur servait encore la feuille de style
d'avant. Deux protections ont été posées — l'empreinte ci-dessus, et des
attributs `width`/`height` qui portent la taille **d'affichage** du logo et
non celle de son tracé, pour qu'une page privée de CSS reste sensée.


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
