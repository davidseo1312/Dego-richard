#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Assemble les pages statiques du site.
#
#   src/pages/**/*.html  (contenu + métadonnées)
# + src/partials/*.html  (head, header, footer, JSON-LD)
# + src/config.sh        (valeurs globales)
# ->  public/**/*.html   (site déployable tel quel)
#
# Usage : bash scripts/build.sh
#
# Le script ne rend la main en SUCCESS que si le dossier produit est
# réellement servable : index.html à la racine, aucune couche superflue,
# ressources présentes, aucun token non résolu. Un build « qui n'a pas
# planté » n'est pas un build valide — c'est exactement ce qui produit un
# 403 sur Hostinger.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Charge la configuration et exporte chaque variable pour la substitution.
source src/config.sh
while IFS= read -r var; do
  export "$var"
done < <(grep -oE '^[A-Z][A-Z0-9_]*=' src/config.sh | tr -d '=')

# Markup des photographies, produit par scripts/preparer-photos.py. Chaque
# variable porte un bloc <picture> complet : une page écrit {{PHOTO_WC_MEDIA}}
# et hérite des sources AVIF/WebP, du srcset, du sizes et des dimensions
# réelles des fichiers. Absent, le site se construit quand même — sans
# photographies, mais sans planter.
if [ -f src/photos.sh ]; then
  source src/photos.sh
  while IFS= read -r var; do
    export "$var"
  done < <(grep -oE '^PHOTO_[A-Z0-9_]*=' src/photos.sh | tr -d '=')
fi

ROBOTS_POLICY_GLOBAL="$ROBOTS_POLICY"

OUT="public"
rm -rf "$OUT"
mkdir -p "$OUT"

# Les fichiers statiques (CSS, JS, images, .htaccess…) sont copiés tels quels.
# Les notes de travail en Markdown restent dans le dépôt et ne sont pas
# publiées : elles n'ont rien à faire sur le serveur.
cp -r static/. "$OUT"/
find "$OUT" -name '*.md' -delete

# Remplace {{VARIABLE}} par la valeur de l'environnement.
# Deux passes : un titre de page peut lui-même contenir {{NOM_COMMERCIAL}}.
# Un token inconnu est laissé intact pour être repéré plus bas.
substituer() {
  perl -pe 's/\{\{(\w+)\}\}/exists $ENV{$1} ? $ENV{$1} : "{{$1}}"/ge' \
    | perl -pe 's/\{\{(\w+)\}\}/exists $ENV{$1} ? $ENV{$1} : "{{$1}}"/ge'
}

# Échappe une valeur destinée à un littéral JSON (données structurées).
json_escape() {
  printf '%s' "$1" | perl -pe 's/\\/\\\\/g; s/"/\\"/g; s/\n/ /g'
}

# Lit une clé du bloc de métadonnées en tête de page.
meta_get() {
  sed -n '/^<!--meta$/,/^-->$/p' "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -1
}

# --- Blocs optionnels injectés dans <head> ---------------------------------
# Rien n'est écrit tant que l'identifiant correspondant est vide : pas de
# balise creuse, pas de requête réseau inutile.

export BLOC_VERIFICATION=""
if [ -n "${GSC_CODE:-}" ]; then
  BLOC_VERIFICATION="<meta name=\"google-site-verification\" content=\"${GSC_CODE}\">"
fi

# --- Avis clients -----------------------------------------------------------
# La section est construite depuis src/avis.tsv. Le fichier livré est vide :
# aucun avis n'a été inventé. Tant qu'il le reste, {{SECTION_AVIS}} vaut la
# chaîne vide et la section n'apparaît sur aucune page — une section d'avis
# vide inspire moins confiance que pas de section du tout.
#
# Ces avis ne sont volontairement PAS balisés en JSON-LD : Google interdit le
# balisage d'avis que l'on collecte soi-même à son propre sujet.
export SECTION_AVIS=""
NB_AVIS=0
if [ -f src/avis.tsv ]; then
  AVIS_CARTES=""
  TOTAL_NOTES=0
  while IFS=$'\t' read -r prenom note ville date commentaire; do
    case "$prenom" in ''|'#'*) continue ;; esac
    [ -n "$commentaire" ] || continue
    NB_AVIS=$((NB_AVIS + 1))
    TOTAL_NOTES=$((TOTAL_NOTES + ${note:-0}))
    note=${note:-0}
    etoiles=""
    for i in 1 2 3 4 5; do
      if [ "$i" -le "$note" ]; then
        etoiles="${etoiles}<span class=\"etoile pleine\" aria-hidden=\"true\">★</span>"
      else
        etoiles="${etoiles}<span class=\"etoile\" aria-hidden=\"true\">★</span>"
      fi
    done
    lieu=""
    [ -n "$ville" ] && lieu=" · $ville"
    quand=""
    if [ -n "$date" ]; then
      quand="<time datetime=\"$date\">$(date -d "$date" '+%B %Y' 2>/dev/null || echo "$date")</time>"
    fi
    AVIS_CARTES="${AVIS_CARTES}
      <article class=\"carte avis-carte\" data-reveal>
        <p class=\"avis-note\">${etoiles}<span class=\"visually-hidden\">${note} étoiles sur 5</span></p>
        <blockquote><p>${commentaire}</p></blockquote>
        <p class=\"avis-auteur\"><strong>${prenom}</strong><span>${lieu}</span> ${quand}</p>
      </article>"
  done < src/avis.tsv

  if [ "$NB_AVIS" -gt 0 ]; then
    MOYENNE=$(awk "BEGIN { printf \"%.1f\", $TOTAL_NOTES / $NB_AVIS }")
    export SECTION_AVIS="<section>
  <div class=\"wrap\">
    <div class=\"section-titre\">
      <p class=\"sur-titre\">Avis clients</p>
      <h2>Ce que disent les personnes chez qui nous sommes intervenus</h2>
      <p>Avis reçus après intervention, publiés tels qu'ils ont été écrits. Note moyenne : <strong>${MOYENNE} sur 5</strong> sur ${NB_AVIS} avis.</p>
    </div>
    <div class=\"grille grille-3 avis-grille\">${AVIS_CARTES}
    </div>
  </div>
</section>"
  fi
fi

# --- Formulaire de demande d'intervention ----------------------------------
# Le formulaire n'existe qu'en un seul exemplaire, dans src/partials/. Les
# pages qui l'affichent écrivent simplement {{FORMULAIRE_DEVIS}} : une
# correction sur le partiel se répercute partout au build suivant.
# --- Tarifs « à partir de » --------------------------------------------------
# Un prix non renseigné n'affiche RIEN. Ni crochet, ni « à renseigner », ni
# zéro : une page publique n'a pas à exposer l'état d'avancement de sa propre
# configuration, et un prix faux engage l'entreprise plus sûrement qu'un prix
# absent. La page /tarifs reste conforme sans chiffre — elle explique les
# facteurs de prix et renvoie au devis écrit.
prix_depuis() {                     # $1 = montant brut, "" si non renseigné
  [ -n "${1:-}" ] || return 0
  printf 'à partir de <strong>%s&nbsp;%s</strong>' "$1" "$UNITE_PRIX"
}

# Ligne de prix posée sur une page de prestation.
ligne_prix() {                      # $1 = montant, $2 = intitulé
  [ -n "${1:-}" ] || return 0
  printf '<p class="prix-depuis"><span class="prix-intitule">%s</span>' "$2"
  printf '<span class="prix-montant">%s</span>' "$(prix_depuis "$1")"
  printf '<span class="prix-note">Devis écrit remis avant toute intervention.</span></p>'
}

export PRIX_DEPUIS_DEBOUCHAGE_LIGNE="$(ligne_prix "$PRIX_DEPUIS_DEBOUCHAGE" "Débouchage d'un appareil sanitaire")"
export PRIX_DEPUIS_DEBOUCHAGE_WC_LIGNE="$(ligne_prix "$PRIX_DEPUIS_DEBOUCHAGE_WC" "Débouchage de WC")"
export PRIX_DEPUIS_HYDROCURAGE_LIGNE="$(ligne_prix "$PRIX_DEPUIS_HYDROCURAGE" "Curage haute pression")"
export PRIX_DEPUIS_INSPECTION_CAMERA_LIGNE="$(ligne_prix "$PRIX_DEPUIS_INSPECTION_CAMERA" "Inspection caméra")"
export PRIX_DEPUIS_POMPAGE_LIGNE="$(ligne_prix "$PRIX_DEPUIS_POMPAGE" "Pompage")"

# Le tableau complet de la page /tarifs.
TARIFS_CARTES=""
ajouter_tarif() {                   # $1 = montant, $2 = intitulé, $3 = précision
  [ -n "${1:-}" ] || return 0
  TARIFS_CARTES="${TARIFS_CARTES}
      <li class=\"tarif\">
        <span class=\"tarif-nom\">$2</span>
        <span class=\"tarif-prix\">$(prix_depuis "$1")</span>
        <span class=\"tarif-detail\">$3</span>
      </li>"
}
ajouter_tarif "$PRIX_DEPUIS_DEBOUCHAGE" "Débouchage d'un appareil sanitaire" \
  "Évier, lavabo, douche, baignoire. Démontage du siphon et furet compris."
ajouter_tarif "$PRIX_DEPUIS_DEBOUCHAGE_WC" "Débouchage de WC" \
  "Furet à tête adaptée, sans dépose de la cuvette dans la plupart des cas."
ajouter_tarif "$PRIX_DEPUIS_HYDROCURAGE" "Curage haute pression" \
  "Canalisation intérieure ou enterrée, depuis un regard accessible."
ajouter_tarif "$PRIX_DEPUIS_INSPECTION_CAMERA" "Inspection caméra" \
  "Passage vidéo et compte rendu de l'état réel de la conduite."
ajouter_tarif "$PRIX_DEPUIS_POMPAGE" "Pompage" \
  "Regard, fosse ou bac à graisses, évacuation des matières comprise."

TARIFS_BASE=""
ajouter_base() {                    # $1 = montant, $2 = intitulé, $3 = unité
  [ -n "${1:-}" ] || return 0
  TARIFS_BASE="${TARIFS_BASE}
      <li><span>$2</span><strong>$1&nbsp;$3</strong></li>"
}
ajouter_base "$TAUX_HORAIRE" "Taux horaire de main-d'œuvre" "$UNITE_PRIX"
ajouter_base "$FRAIS_DEPLACEMENT" "Frais de déplacement" "$UNITE_PRIX"
ajouter_base "$MAJORATION_NUIT" "Majoration nuit, dimanche et jours fériés" "%"

# Le chapeau de /tarifs doit dire la vérité dans les deux états : annoncer des
# prix affichés alors qu'aucun ne l'est serait faux, et taire ceux qui le sont
# reviendrait à cacher l'argument le plus utile de la page.
if [ -n "$TARIFS_CARTES" ]; then
  export CHAPEAU_TARIFS="Nos prix d'appel sont affichés, et ce sont de vrais montants :
          celui de l'intervention la plus simple de chaque catégorie, pas une accroche que
          personne ne paie. Cette page explique ce qui fait varier le prix au-delà, et comment
          il vous est communiqué avant que quoi que ce soit ne commence."
else
  export CHAPEAU_TARIFS="Le prix d'un dégorgement n'est pas un chiffre unique : il dépend de
          ce que l'on trouve. Cette page explique ce qui le fait varier, et comment le montant
          vous est annoncé — au téléphone d'abord, par écrit ensuite, avant que quoi que ce soit
          ne commence."
fi

if [ -n "$TARIFS_CARTES" ] || [ -n "$TARIFS_BASE" ]; then
  BASE_HTML=""
  [ -n "$TARIFS_BASE" ] && BASE_HTML="
    <ul class=\"tarifs-base\">$TARIFS_BASE
    </ul>"
  GRILLE_HTML=""
  [ -n "$TARIFS_CARTES" ] && GRILLE_HTML="
    <ul class=\"tarifs-grille\">$TARIFS_CARTES
    </ul>"
  export SECTION_TARIFS="<div class=\"tarifs\">
    <h2>Nos tarifs</h2>
    <p>
      Ces montants sont des prix d'appel : ils correspondent à l'intervention la
      plus simple de chaque catégorie. Le prix exact dépend de la nature du
      bouchon, de son emplacement, de l'accessibilité et du matériel nécessaire.
      Il vous est annoncé par écrit <em>avant</em> le démarrage, et rien n'est
      engagé sans votre accord.
    </p>${GRILLE_HTML}${BASE_HTML}
    <p class=\"tarifs-mention\">
      ${MENTION_TVA:-}. Affichage conforme à l'arrêté du 24 janvier 2017
      relatif à la publicité des prix des prestations de dépannage, de réparation
      et d'entretien dans le secteur du bâtiment.
    </p>
  </div>"
else
  # Aucun tarif publié : on le dit, et on n'invente rien.
  export SECTION_TARIFS="<div class=\"tarifs tarifs-absents\">
    <h2>Nos tarifs</h2>
    <p>
      Le prix dépend de la nature du bouchon, de son emplacement, de
      l'accessibilité et du matériel nécessaire : un siphon d'évier et un
      collecteur enterré ne demandent ni le même temps, ni le même matériel.
      C'est pourquoi nous annonçons un prix au téléphone, après quelques
      questions, puis un <strong>devis écrit remis avant toute
      intervention</strong>. Rien n'est engagé sans votre accord.
    </p>
    <p>
      <a class=\"btn btn-call btn-large\" href=\"tel:${TELEPHONE_E164}\" data-track=\"appel\" data-track-zone=\"tarifs\">${TELEPHONE}</a>
      <a class=\"btn btn-ghost btn-large\" href=\"/devis\" data-track=\"clic_devis\" data-track-zone=\"tarifs\">Demander un devis</a>
    </p>
  </div>"
fi

export FORMULAIRE_DEVIS="$(cat src/partials/formulaire-devis.html)"

# --- Carte des zones d'intervention ----------------------------------------
# Même principe que le formulaire : un seul exemplaire, dans src/partials/.
export SECTION_CARTE="$(cat src/partials/carte-zone.html)"

# --- Génération d'un fil d'Ariane BreadcrumbList ---------------------------
# Google exige que le fil d'Ariane balisé corresponde à celui affiché.
# Les pages composent le leur avec <nav class="fil"> ; ce bloc produit le
# JSON-LD équivalent à partir des métadonnées « breadcrumb » et « parent ».
# --- Empreintes de contenu ---------------------------------------------------
# Les feuilles de style, les scripts et les favicons sont servis avec
# « Cache-Control: immutable, max-age=1 an ». C'est le bon réglage — mais à une
# condition : que leur URL change quand leur contenu change. Sans cela, un
# visiteur déjà venu garde l'ancienne feuille pendant un an et ne la
# redemande même pas, « immutable » dispensant le navigateur de revalider.
# L'empreinte du fichier devient donc son numéro de version.
empreinte() { sha1sum "$1" 2>/dev/null | cut -c1-8; }
export V_CSS="$(empreinte static/assets/css/style.css)"
export V_JS="$(empreinte static/assets/js/site.js)"
# Les icônes changent ensemble : une seule empreinte pour le lot suffit, et
# elle évite de multiplier les jetons dans l'en-tête.
export V_ICONES="$(cat static/assets/img/favicon.svg \
                       static/assets/img/favicon.ico \
                       static/assets/img/apple-touch-icon.png 2>/dev/null \
                   | sha1sum | cut -c1-8)"

# --- WebPage + ImageObject ---------------------------------------------------
# Chaque page décrit ce qu'elle est, à quel site elle appartient et quelle
# image la représente. Les dimensions sont celles des vignettes de partage
# réellement produites par scripts/preparer-photos.py (1200 × 630) : les
# déclarer au jugé produirait une donnée structurée qui ne correspond pas au
# fichier, exactement ce que Google reproche.
schema_webpage() {
  cat <<LD
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "${PAGE_URL}#page",
  "url": "${PAGE_URL}",
  "name": "${PAGE_TITLE}",
  "description": "${PAGE_DESC}",
  "inLanguage": "fr-FR",
  "dateModified": "${PAGE_DATE}",
  "isPartOf": { "@id": "${BASE_URL}/#site" },
  "about": { "@id": "${BASE_URL}/#entreprise" },
  "primaryImageOfPage": {
    "@type": "ImageObject",
    "url": "${BASE_URL}${PAGE_IMAGE}",
    "contentUrl": "${BASE_URL}${PAGE_IMAGE}",
    "width": 1200,
    "height": 630
  }
}
</script>
LD
}

schema_breadcrumb() {
  local nom_page="$1" url_page="$2" nom_parent="$3" url_parent="$4"
  local position=2 items

  items="    { \"@type\": \"ListItem\", \"position\": 1, \"name\": \"Accueil\", \"item\": \"${BASE_URL}/\" }"

  if [ -n "$nom_parent" ] && [ -n "$url_parent" ]; then
    items="${items},
    { \"@type\": \"ListItem\", \"position\": 2, \"name\": \"$(json_escape "$nom_parent")\", \"item\": \"${BASE_URL}${url_parent}\" }"
    position=3
  fi

  items="${items},
    { \"@type\": \"ListItem\", \"position\": ${position}, \"name\": \"$(json_escape "$nom_page")\", \"item\": \"${url_page}\" }"

  cat <<LD
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
${items}
  ]
}
</script>
LD
}

PAGE_COUNT=0
SITEMAP_ENTRIES=""

while IFS= read -r src_file; do
  rel="${src_file#src/pages/}"

  export PAGE_TITLE="$(meta_get "$src_file" title)"
  export PAGE_DESC="$(meta_get "$src_file" description)"
  export PAGE_IMAGE="$(meta_get "$src_file" image)"
  export PAGE_DATE="$(meta_get "$src_file" date)"
  export PAGE_BREADCRUMB="$(meta_get "$src_file" breadcrumb)"
  # Nom de la zone géographique servie, repris tel quel dans le JSON-LD des
  # pages départementales et communales. Séparé du fil d'Ariane, qui porte un
  # libellé rédigé pour l'humain (« Dégorgement à Rennes »).
  export PAGE_ZONE_NOM="$(meta_get "$src_file" zone_nom)"
  export PAGE_ZONE_PARENT="$(meta_get "$src_file" zone_parent)"
  PAGE_SCHEMA="$(meta_get "$src_file" schema)"
  PAGE_PRIORITY="$(meta_get "$src_file" priority)"
  PAGE_SITEMAP="$(meta_get "$src_file" sitemap)"
  PAGE_ROBOTS="$(meta_get "$src_file" robots)"
  PAGE_CONVERSION="$(meta_get "$src_file" conversion)"
  PAGE_FAQ="$(meta_get "$src_file" faq)"
  PAGE_PARENT_NOM="$(meta_get "$src_file" parent_nom)"
  PAGE_PARENT_URL="$(meta_get "$src_file" parent_url)"

  [ -n "$PAGE_PRIORITY" ] || PAGE_PRIORITY="0.6"
  [ -n "$PAGE_IMAGE" ] || PAGE_IMAGE="/assets/img/partage/og-default.jpg"
  [ -n "$PAGE_DATE" ] || PAGE_DATE="$(date +%Y-%m-%d)"

  # Une page peut déclarer une conversion mesurée à son affichage (page de
  # remerciement). L'attribut n'est écrit que si la clé est renseignée.
  if [ -n "$PAGE_CONVERSION" ]; then
    export ATTRIBUT_CONVERSION=" data-conversion=\"$PAGE_CONVERSION\""
  else
    export ATTRIBUT_CONVERSION=""
  fi

  # Une page peut forcer son propre robots (ex : 404 en noindex).
  if [ -n "$PAGE_ROBOTS" ]; then
    export ROBOTS_POLICY="$PAGE_ROBOTS"
  else
    export ROBOTS_POLICY="$ROBOTS_POLICY_GLOBAL"
  fi

  # URL canonique :
  #   index.html        -> /
  #   blog/index.html   -> /blog/     (évite le conflit avec le dossier blog/)
  #   tarifs.html       -> /tarifs    (extension masquée par le .htaccess)
  if [ "$rel" = "index.html" ]; then
    export PAGE_PATH="/"
  elif [ "$(basename "$rel")" = "index.html" ]; then
    export PAGE_PATH="/$(dirname "$rel")/"
  else
    export PAGE_PATH="/${rel%.html}"
  fi
  export PAGE_URL="${BASE_URL}${PAGE_PATH}"

  # Le corps est substitué d'abord : le balisage FAQPage doit contenir les
  # valeurs finales (téléphone, zone), pas les tokens.
  CORPS="$(sed '/^<!--meta$/,/^-->$/d' "$src_file" | substituer)"

  # FAQPage dérivé des blocs <details> réellement affichés. « faq: non » dans
  # les métadonnées désactive la génération pour une page donnée.
  FAQ_LD=""
  if [ "$PAGE_FAQ" != "non" ]; then
    FAQ_LD="$(printf '%s\n' "$CORPS" | perl scripts/faq-jsonld.pl)"
  fi

  dest="$OUT/$rel"
  mkdir -p "$(dirname "$dest")"

  {
    cat src/partials/head.html
    schema_webpage
    if [ -n "$PAGE_SCHEMA" ] && [ -f "src/partials/schema-${PAGE_SCHEMA}.html" ]; then
      cat "src/partials/schema-${PAGE_SCHEMA}.html"
    fi
    # Fil d'Ariane balisé sur toutes les pages sauf l'accueil, qui est la
    # racine du fil et n'a donc rien à décrire.
    if [ "$rel" != "index.html" ]; then
      nom="${PAGE_BREADCRUMB:-$PAGE_TITLE}"
      schema_breadcrumb "$nom" "$PAGE_URL" "$PAGE_PARENT_NOM" "$PAGE_PARENT_URL"
    fi
    [ -n "$FAQ_LD" ] && printf '%s\n' "$FAQ_LD"
    cat src/partials/head-close.html
    cat src/partials/header.html
    printf '%s\n' "$CORPS"
    cat src/partials/footer.html
  } | substituer > "$dest"

  # Les pages marquées "sitemap: non" restent hors du sitemap.
  if [ "$PAGE_SITEMAP" != "non" ]; then
    SITEMAP_ENTRIES="${SITEMAP_ENTRIES}${PAGE_URL}|${PAGE_PRIORITY}|${PAGE_DATE}"$'\n'
  fi
  PAGE_COUNT=$((PAGE_COUNT + 1))
done < <(find src/pages -name '*.html' | sort)

# --- Scripts PHP -----------------------------------------------------------
# Le traitement du formulaire a besoin des mêmes valeurs que les pages
# (adresse de réception, nom commercial…). Les fichiers .php passent donc par
# la même substitution que le HTML.
PHP_COUNT=0
while IFS= read -r php_file; do
  [ -n "$php_file" ] || continue
  rel="${php_file#static/}"
  substituer < "$php_file" > "$OUT/$rel"
  PHP_COUNT=$((PHP_COUNT + 1))
done < <(find static -name '*.php' 2>/dev/null | sort)

# --- Manifeste d'application ------------------------------------------------
[ -f static/manifest.webmanifest ] && substituer < static/manifest.webmanifest > "$OUT/manifest.webmanifest"

bash scripts/gen-sitemap.sh "$SITEMAP_ENTRIES"

# --- Permissions ------------------------------------------------------------
# 755 sur les dossiers, 644 sur les fichiers. Un dossier en 700 ou un
# index.html en 600 produit exactement le 403 que ce projet cherche à éviter,
# et jamais 777, qu'un hébergeur mutualisé refuse d'exécuter.
find "$OUT" -type d -exec chmod 755 {} +
find "$OUT" -type f -exec chmod 644 {} +

echo "✓ $PAGE_COUNT pages générées dans public/"
[ "$PHP_COUNT" -gt 0 ] && echo "✓ $PHP_COUNT script(s) PHP traité(s)"

# ---------------------------------------------------------------------------
# Vérification du résultat.
# ---------------------------------------------------------------------------

MANQUES=0
manque() { echo "  ✗ $1"; MANQUES=$((MANQUES + 1)); }

echo
echo "Vérification du dossier de production…"

# 1. La page d'accueil, à la RACINE de public/ et nulle part ailleurs.
if [ -f "$OUT/index.html" ]; then
  echo "  ✓ index.html présent à la racine de $OUT/"
else
  manque "index.html ABSENT de la racine de $OUT/ — Apache renverrait 403"
fi

# 2. Aucune couche superflue : public/public/, public/dist/…
for indesirable in "$OUT/public" "$OUT/dist" "$OUT/build" "$OUT/src" "$OUT/scripts"; do
  [ -d "$indesirable" ] && manque "couche superflue détectée : $indesirable/"
done

# 3. Les fichiers indispensables au fonctionnement et au référencement.
for requis in \
  "$OUT/.htaccess" \
  "$OUT/404.html" \
  "$OUT/robots.txt" \
  "$OUT/sitemap.xml" \
  "$OUT/manifest.webmanifest" \
  "$OUT/envoi-demande.php" \
  "$OUT/assets/css/style.css" \
  "$OUT/assets/js/site.js" \
  "$OUT/assets/img/favicon.svg" \
  "$OUT/assets/img/partage/og-default.jpg"; do
  [ -f "$requis" ] || manque "fichier requis absent : ${requis#$OUT/}"
done

# 4. Toutes les ressources référencées par les pages existent réellement.
#    Les srcset sont dépouillés au même titre que les src : un fichier
#    manquant dans un srcset ne casse rien de visible en développement, mais
#    fait échouer silencieusement le chargement chez une partie des visiteurs.
RESSOURCES=$( { grep -rhoE 'src="/[^"]+"' "$OUT" --include='*.html'
                grep -rhoE 'href="/assets/[^"]+"' "$OUT" --include='*.html'
                grep -rhoE 'href="/manifest[^"]*"' "$OUT" --include='*.html'
                grep -rhoE 'srcset="[^"]+"' "$OUT" --include='*.html' \
                  | sed 's/^srcset="//;s/"$//' | tr ',' '\n' \
                  | sed 's/^ *//;s/ [0-9]*w$//' | sed 's/^/src="/;s/$/"/'
              } 2>/dev/null | sed 's/^[a-z]*="//;s/"$//;s/?.*$//' | sort -u )
NB_RESSOURCES=0
while IFS= read -r ref; do
  [ -n "$ref" ] || continue
  NB_RESSOURCES=$((NB_RESSOURCES + 1))
  [ -f "$OUT$ref" ] || manque "ressource référencée mais absente : $ref"
done <<< "$RESSOURCES"

# 5. Le sitemap doit contenir des URLs, pas seulement son enveloppe XML.
NB_URLS=$(grep -c '<loc>' "$OUT/sitemap.xml" 2>/dev/null || echo 0)
if [ "${NB_URLS:-0}" -lt 1 ]; then
  manque "sitemap.xml ne contient aucune URL"
fi

# 6. Aucun token de gabarit non résolu.
if grep -rqo '{{[A-Za-z_]*}}' "$OUT" 2>/dev/null; then
  manque "tokens {{...}} non résolus : $(grep -rho '{{[A-Za-z_]*}}' "$OUT" | sort -u | tr '\n' ' ')"
fi

# 7. Le secteur d'intervention est limité à six départements. Un département
#    hérité d'un autre projet, ou ajouté par inadvertance, est une promesse
#    que l'entreprise ne tient pas : le build refuse de le publier.
HORS_ZONE=$(grep -rlniE '\b(Manche \(50\)|Calvados|Orne \(61\)|Mayenne \(53\)|Sarthe \(72\)|Seine-Maritime|Vendée \(85\)|Eure \(27\)|Deux-Sèvres|Charente-Maritime)\b' \
             "$OUT" --include='*.html' 2>/dev/null || true)
if [ -n "$HORS_ZONE" ]; then
  while IFS= read -r f; do
    manque "département hors zone mentionné dans ${f#$OUT/}"
  done <<< "$HORS_ZONE"
fi

echo

if [ "$MANQUES" -gt 0 ]; then
  echo "BUILD FAILED — $MANQUES problème(s). Le dossier $OUT/ n'est pas déployable."
  exit 1
fi

echo "BUILD SUCCESS"
echo "  $PAGE_COUNT pages · $NB_URLS URLs au sitemap · $NB_RESSOURCES ressources vérifiées"
echo "  Dossier de production : $OUT/  (à servir comme document root)"
exit 0
