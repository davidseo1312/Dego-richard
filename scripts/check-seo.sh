#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Contrôle SEO, GEO et pré-vol de mise en ligne.
# À lancer après scripts/build.sh, et à rejouer après chaque modification.
#
#   bash scripts/check-seo.sh
#
# Sortie 1 si au moins une erreur bloquante est détectée.
# Les compteurs transitent par un fichier : les boucles derrière un pipe
# s'exécutent dans des sous-shells et perdraient des variables ordinaires.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source src/config.sh

[ -d public ] || { echo "public/ absent — lancez d'abord : bash scripts/build.sh"; exit 1; }

COMPTEURS="$(mktemp)"
trap 'rm -f "$COMPTEURS"' EXIT

ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; VERT=$'\033[32m'; GRAS=$'\033[1m'; FIN=$'\033[0m'

erreur() { echo "  ${ROUGE}x${FIN} $1"; echo E >> "$COMPTEURS"; }
# Distinct d'une erreur : le code est correct, il manque une information que
# seul l'exploitant peut fournir (assurance, médiateur, tarifs).
adonner() { echo "  ${JAUNE}#${FIN} $1"; echo D >> "$COMPTEURS"; }
avert()  { echo "  ${JAUNE}!${FIN} $1"; echo A >> "$COMPTEURS"; }
ok()     { echo "  ${VERT}v${FIN} $1"; }
titre()  { echo; echo "${GRAS}$1${FIN}"; }

PAGES=$(find public -name '*.html' | sort)
NB_PAGES=$(echo "$PAGES" | wc -l)

lire_title() { sed -n 's/.*<title>\(.*\)<\/title>.*/\1/p' "$1" | head -1; }
lire_desc()  { sed -n 's/.*<meta name="description" content="\([^"]*\)".*/\1/p' "$1" | head -1; }

# --- 1. Balises title ------------------------------------------------------
titre "1. Balises title"
while IFS= read -r f; do
  t=$(lire_title "$f"); n=${#t}
  if   [ -z "$t" ];      then erreur "${f#public/} : title absent"
  elif [ "$n" -gt 65 ];  then avert  "${f#public/} : title de $n caracteres (tronque au-dela de ~60)"
  elif [ "$n" -lt 25 ];  then avert  "${f#public/} : title de $n caracteres, trop court"
  fi
done <<< "$PAGES"

DOUBLONS=""
while IFS= read -r f; do DOUBLONS+="$(lire_title "$f")"$'\n'; done <<< "$PAGES"
DOUBLONS=$(echo "$DOUBLONS" | sort | uniq -d | grep -v '^$' || true)
if [ -n "$DOUBLONS" ]; then
  while IFS= read -r d; do erreur "title duplique : $d"; done <<< "$DOUBLONS"
else
  ok "Titles tous uniques ($NB_PAGES pages)"
fi

# --- 2. Meta descriptions --------------------------------------------------
titre "2. Meta descriptions"
while IFS= read -r f; do
  d=$(lire_desc "$f"); n=${#d}
  if   [ -z "$d" ];       then erreur "${f#public/} : description absente"
  elif [ "$n" -gt 165 ];  then avert  "${f#public/} : description de $n caracteres (tronquee au-dela de ~160)"
  elif [ "$n" -lt 70 ];   then avert  "${f#public/} : description de $n caracteres, trop courte"
  fi
done <<< "$PAGES"

DOUBLONS=""
while IFS= read -r f; do DOUBLONS+="$(lire_desc "$f")"$'\n'; done <<< "$PAGES"
DOUBLONS=$(echo "$DOUBLONS" | sort | uniq -d | grep -v '^$' || true)
if [ -n "$DOUBLONS" ]; then
  while IFS= read -r d; do erreur "description dupliquee : ${d:0:70}..."; done <<< "$DOUBLONS"
else
  ok "Descriptions toutes uniques"
fi

# --- 3. Titres H1 ----------------------------------------------------------
titre "3. Titres H1"
PB=0
while IFS= read -r f; do
  n=$(grep -o '<h1[ >]' "$f" | wc -l)
  if [ "$n" -ne 1 ]; then erreur "${f#public/} : $n balise(s) H1, il en faut exactement une"; PB=1; fi
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Une seule H1 par page"

DOUBLONS=""
while IFS= read -r f; do
  DOUBLONS+="$(sed -n 's/.*<h1[^>]*>\(.*\)<\/h1>.*/\1/p' "$f" | head -1)"$'\n'
done <<< "$PAGES"
DOUBLONS=$(echo "$DOUBLONS" | sort | uniq -d | grep -v '^$' || true)
if [ -n "$DOUBLONS" ]; then
  while IFS= read -r d; do erreur "H1 dupliquee : ${d:0:70}"; done <<< "$DOUBLONS"
else
  ok "H1 toutes uniques"
fi

# --- 4. Attributs alt ------------------------------------------------------
titre "4. Accessibilite des images"
PB=0
while IFS= read -r f; do
  while IFS= read -r img; do
    [ -z "$img" ] && continue
    case "$img" in
      *alt=*) : ;;
      *) erreur "${f#public/} : <img> sans alt -> ${img:0:70}"; PB=1 ;;
    esac
  done <<< "$(grep -o '<img [^>]*>' "$f" || true)"
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Toutes les images portent un attribut alt"

PB=0
while IFS= read -r f; do
  while IFS= read -r img; do
    [ -z "$img" ] && continue
    case "$img" in
      *width=*height=*|*width=*\ height=*) : ;;
      *) avert "${f#public/} : <img> sans width/height (decalage de mise en page)"; PB=1 ;;
    esac
  done <<< "$(grep -o '<img [^>]*>' "$f" || true)"
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Toutes les images declarent leurs dimensions"

# --- 5. Liens internes -----------------------------------------------------
titre "5. Liens internes"
PB=0
while IFS= read -r f; do
  while IFS= read -r lien; do
    [ -z "$lien" ] && continue
    case "$lien" in /assets/*) continue ;; esac
    cible="public${lien}"
    if   [ "$lien" = "/" ] && [ -f public/index.html ]; then continue
    elif [ -f "$cible" ];          then continue
    elif [ -f "${cible}.html" ];   then continue
    elif [ -f "${cible}/index.html" ]; then continue
    elif [ -f "${cible%/}.html" ]; then continue
    else erreur "${f#public/} : lien brise vers $lien"; PB=1
    fi
  done <<< "$(grep -o 'href="/[^"#]*"' "$f" | sed 's/href="//;s/"$//' | sort -u)"
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Aucun lien interne brise"

# --- 6. Pages orphelines ---------------------------------------------------
# Une page qu'aucune autre ne lie n'est explorée que par le sitemap : elle
# reste faible en maillage et convertit mal. On ignore l'accueil et les pages
# volontairement hors navigation (404, remerciement).
titre "6. Pages orphelines"
LIENS=$(grep -rhoE 'href="/[^"#]*"' public --include='*.html' | sed 's/href="//;s/"$//' | sort -u)
PB=0
while IFS= read -r f; do
  chemin="/${f#public/}"; chemin="${chemin%.html}"
  case "$chemin" in
    /index|/404|/merci) continue ;;
  esac
  chemin_dossier="${chemin%/index}/"
  if ! grep -qxF "$chemin" <<< "$LIENS" && ! grep -qxF "$chemin_dossier" <<< "$LIENS"; then
    erreur "page orpheline (aucun lien interne n'y mene) : ${f#public/}"
    PB=1
  fi
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Aucune page orpheline"

# --- 7. Canoniques et donnees structurees ----------------------------------
titre "7. URL canoniques et donnees structurees"
PB=0
while IFS= read -r f; do
  grep -q '<link rel="canonical"' "$f" || { erreur "${f#public/} : canonique absente"; PB=1; }
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Canonique presente sur toutes les pages"

PB=0
while IFS= read -r f; do
  grep -q 'property="og:title"' "$f" || { erreur "${f#public/} : Open Graph absent"; PB=1; }
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Open Graph present sur toutes les pages"

NB_LD=$(grep -l 'application/ld+json' $PAGES 2>/dev/null | wc -l)
if [ "$NB_LD" -eq "$NB_PAGES" ]; then
  ok "JSON-LD present sur les $NB_LD pages"
else
  avert "JSON-LD present sur $NB_LD page(s) sur $NB_PAGES"
fi

PB=0
while IFS= read -r f; do
  case "${f#public/}" in index.html) continue ;; esac
  grep -q '"@type": "BreadcrumbList"' "$f" || { erreur "${f#public/} : BreadcrumbList absent"; PB=1; }
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "BreadcrumbList present sur toutes les pages internes"

# --- 8. Optimisation pour les moteurs generatifs (GEO) ---------------------
# Une page de service, de departement ou de ville doit porter un bloc
# « Reponse rapide » : une definition factuelle, autoportante, citable telle
# quelle par un moteur de reponse sans avoir a recomposer le contexte.
titre "8. GEO — blocs de reponse rapide"
PB=0
while IFS= read -r f; do
  rel="${f#public/}"
  case "$rel" in
    index.html|404.html|merci.html|mentions-legales.html|conditions-generales.html|\
politique-confidentialite.html|contact.html|devis.html|blog/index.html) continue ;;
    blog/*) continue ;;
  esac
  grep -q 'class="reponse-rapide"' "$f" || { erreur "$rel : bloc « Reponse rapide » absent"; PB=1; }
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Bloc de reponse rapide present sur toutes les pages concernees"

# --- 9. Tokens non resolus -------------------------------------------------
titre "9. Tokens de gabarit"
RESTES=$(grep -rho '{{[A-Za-z_]*}}' public/ 2>/dev/null | sort -u || true)
if [ -n "$RESTES" ]; then
  while IFS= read -r t; do erreur "token non resolu : $t"; done <<< "$RESTES"
else
  ok "Aucun token non resolu"
fi

# --- 10. Perimetre geographique --------------------------------------------
# Le site n'annonce d'intervention que dans SIX departements. Toute autre
# zone presentee comme couverte est une promesse non tenue.
titre "10. Perimetre geographique (6 departements)"
HORS=$(grep -rlniE '\b(Manche \(50\)|Calvados|Orne \(61\)|Mayenne \(53\)|Sarthe \(72\)|Seine-Maritime|Vendee \(85\)|Vendée \(85\)|Eure \(27\)|Deux-Sevres|Deux-Sèvres|Charente-Maritime|Normandie)\b' \
        public --include='*.html' 2>/dev/null || true)
if [ -n "$HORS" ]; then
  while IFS= read -r f; do erreur "departement hors zone mentionne : ${f#public/}"; done <<< "$HORS"
else
  ok "Aucun departement hors des six annonces"
fi
for d in "Côtes-d'Armor" "Finistère" "Ille-et-Vilaine" "Morbihan" "Loire-Atlantique" "Maine-et-Loire"; do
  grep -qF "$d" public/index.html || erreur "l'accueil ne mentionne pas $d"
done
for d in cotes-d-armor finistere ille-et-vilaine morbihan loire-atlantique maine-et-loire; do
  [ -f "public/departements/$d.html" ] || erreur "page departementale absente : /departements/$d"
done
ok "Six pages departementales presentes"

# --- 11. Donnees d'entreprise ----------------------------------------------
titre "11. Donnees d'entreprise a fournir (bloquant avant mise en ligne)"
MOTIF='\[(RAISON SOCIALE|SIRET|ADRESSE|FORME|CAPITAL|RCS|N. TVA|ASSUREUR|N. DE POLICE|NOM DU M|URL DU M|.TABLISSEMENT|TAUX HORAIRE|FRAIS DE|MAJORATION|FORFAIT)[^]]*\]'
PLACEHOLDERS=$(grep -rlE "$MOTIF" public/ 2>/dev/null | sed 's|^public/||' | sort || true)
if [ -n "$PLACEHOLDERS" ]; then
  NB_PAGES_PH=$(echo "$PLACEHOLDERS" | grep -c .)
  adonner "Champs a renseigner dans src/config.sh, presents sur $NB_PAGES_PH page(s) :"
  grep -rhoE "$MOTIF" public/ 2>/dev/null | sort -u | sed 's/^/        /'
  echo "        -> ces valeurs sont des obligations legales ou contractuelles :"
  echo "           elles ne peuvent pas etre inventees. Voir la section"
  echo "           « Avant la mise en ligne » du README."
else
  ok "Donnees d'entreprise renseignees"
fi

TEL_ATTENDU=$(grep -c "$TELEPHONE" public/index.html 2>/dev/null || echo 0)
if [ "${TEL_ATTENDU:-0}" -gt 0 ]; then
  ok "Numero de telephone present sur l'accueil ($TELEPHONE)"
else
  erreur "le numero $TELEPHONE n'apparait pas sur l'accueil"
fi
NB_SANS_TEL=$(grep -Lc "tel:${TELEPHONE_E164}" $PAGES 2>/dev/null | grep -c . || true)
if [ "${NB_SANS_TEL:-0}" -eq 0 ]; then
  ok "Lien d'appel present sur les $NB_PAGES pages"
else
  erreur "${NB_SANS_TEL} page(s) sans lien d'appel"
fi
AUTRES_TEL=$(grep -rhoE 'tel:\+33[0-9]{9}' public --include='*.html' | sort -u | grep -v "^tel:${TELEPHONE_E164}$" || true)
if [ -n "$AUTRES_TEL" ]; then
  while IFS= read -r t; do erreur "second numero de telephone detecte : $t"; done <<< "$AUTRES_TEL"
else
  ok "Un seul numero de telephone sur tout le site"
fi

# --- 12. Fichiers requis ---------------------------------------------------
titre "12. Fichiers requis"
for f in public/robots.txt public/sitemap.xml public/.htaccess public/404.html \
         public/manifest.webmanifest public/envoi-demande.php \
         public/assets/css/style.css public/assets/js/site.js \
         public/assets/img/favicon.svg public/assets/img/favicon.ico \
         public/assets/img/apple-touch-icon.png public/assets/img/og-default.jpg \
         public/assets/img/icone-192.png public/assets/img/icone-512.png \
         public/assets/img/icone-512-maskable.png; do
  [ -f "$f" ] && ok "${f#public/}" || erreur "${f#public/} manquant"
done

# --- 13. Ressources referencees --------------------------------------------
titre "13. Ressources referencees (images, feuilles, scripts)"
PB=0
REFS=$( { grep -rhoE 'src="/[^"]+"'  public --include='*.html'
          grep -rhoE 'href="/assets/[^"]+"' public --include='*.html'
          grep -rhoE 'href="/manifest[^"]*"' public --include='*.html'
        } | sed 's/^[a-z]*="//;s/"$//' | sort -u )
while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ ! -f "public$ref" ]; then erreur "ressource absente : $ref"; PB=1; fi
done <<< "$REFS"
[ "$PB" -eq 0 ] && ok "Toutes les ressources referencees existent ($(echo "$REFS" | grep -c .) fichiers)"

NB_SVG=$(grep -rhoE 'src="/assets/img/[a-z0-9-]+\.svg"' public --include='*.html' | sort -u | grep -c . || true)
[ "${NB_SVG:-0}" -gt 0 ] && avert "$NB_SVG illustration(s) encore vectorielle(s) - voir static/assets/img/README.md pour deposer de vraies photos"

# --- 14. Redirections 301 --------------------------------------------------
titre "14. Redirections 301"
PB=0
for ancienne in \
  "urgence" "debouchage" "canalisation-bouchee" "wc-bouche" "toilettes-bouchees" \
  "evier-bouche" "lavabo-bouche" "douche-bouchee" "baignoire-bouchee" \
  "hydrocurage" "camera-canalisation" "zones-d-intervention" "devis-degorgement" \
  "tarif" "politique-de-confidentialite"; do
  if [ -f "public/${ancienne}.html" ]; then
    erreur "$ancienne existe en page : conflit avec la redirection"
    PB=1
  elif ! grep -qF "^${ancienne}/?\$" public/.htaccess; then
    erreur "aucune redirection 301 pour /$ancienne dans .htaccess"
    PB=1
  fi
done
[ "$PB" -eq 0 ] && ok "Variantes d'URL toutes redirigees en 301"

# --- 15. Donnees structurees FAQ -------------------------------------------
# Deux pages portant la meme question se concurrencent dans les resultats
# enrichis de Google : aucune des deux ne ressort.
titre "15. Donnees structurees FAQ"
DOUBLES=$(grep -rhoE '"name": "[^"]+\?"' public --include='*.html' | sort | uniq -d || true)
if [ -n "$DOUBLES" ]; then
  while IFS= read -r q; do avert "question FAQ presente sur plusieurs pages : ${q:10:70}"; done <<< "$DOUBLES"
else
  NB_FAQ=$(grep -rl '"@type": "FAQPage"' public --include='*.html' | grep -c . || true)
  ok "FAQPage sur ${NB_FAQ:-0} page(s), aucune question dupliquee"
fi

# --- 16. Indexation --------------------------------------------------------
titre "16. Parametres d'indexation"
if [ "$ROBOTS_POLICY" = "index" ]; then
  ok "Site en index"
  grep -q "Sitemap: ${BASE_URL}/sitemap.xml" public/robots.txt \
    && ok "robots.txt declare le sitemap" \
    || erreur "robots.txt ne declare pas le sitemap"
else
  adonner "Site en '$ROBOTS_POLICY' : il ne sera PAS reference tant que"
  echo "        ROBOTS_POLICY n'est pas passe a \"index\" dans src/config.sh."
fi
ok "sitemap.xml : $(grep -c '<loc>' public/sitemap.xml) URLs"

# Aucune page en noindex ne doit figurer au sitemap : la consigne serait
# contradictoire et Search Console la signalerait en « exclue par balise ».
PB=0
while IFS= read -r url; do
  chemin="${url#$BASE_URL}"
  case "$chemin" in
    /) f=public/index.html ;;
    */) f="public${chemin}index.html" ;;
    *)  f="public${chemin}.html" ;;
  esac
  if [ -f "$f" ] && grep -q 'name="robots" content="noindex' "$f"; then
    erreur "page en noindex presente au sitemap : $chemin"
    PB=1
  fi
done <<< "$(sed -n 's/.*<loc>\(.*\)<\/loc>.*/\1/p' public/sitemap.xml)"
[ "$PB" -eq 0 ] && ok "Aucune page noindex au sitemap"

NB_NOINDEX=$(grep -rl 'name="robots" content="noindex' public --include='*.html' | grep -c . || true)
ok "${NB_NOINDEX:-0} page(s) volontairement en noindex (404, remerciement)"

# --- 17. Poids -------------------------------------------------------------
titre "17. Poids des fichiers"
PB=0
while IFS= read -r l; do
  [ -n "$l" ] && { avert "${l#public/} depasse 100 Ko"; PB=1; }
done <<< "$(find public -name '*.html' -size +100k)"
while IFS= read -r g; do
  [ -n "$g" ] && { avert "${g#public/} depasse 250 Ko"; PB=1; }
done <<< "$(find public/assets -type f -size +250k 2>/dev/null)"
[ "$PB" -eq 0 ] && ok "Aucun fichier trop lourd"
ok "CSS $(du -k public/assets/css/style.css | cut -f1) Ko, JS $(du -k public/assets/js/site.js | cut -f1) Ko, total site $(du -sk public | cut -f1) Ko"

# --- Bilan -----------------------------------------------------------------
NB_ERR=$(grep -c '^E$' "$COMPTEURS" 2>/dev/null || true)
NB_AVERT=$(grep -c '^A$' "$COMPTEURS" 2>/dev/null || true)
NB_DONN=$(grep -c '^D$' "$COMPTEURS" 2>/dev/null || true)
NB_ERR=${NB_ERR:-0}; NB_AVERT=${NB_AVERT:-0}; NB_DONN=${NB_DONN:-0}

echo
echo "${GRAS}Bilan${FIN}"
echo "  $NB_PAGES pages analysees"
echo "  ${ROUGE}$NB_ERR defaut(s) technique(s)${FIN}     - a corriger dans le code"
echo "  ${JAUNE}$NB_DONN information(s) a fournir${FIN} - a renseigner dans src/config.sh"
echo "  ${JAUNE}$NB_AVERT avertissement(s)${FIN}"
echo

if [ "$NB_ERR" -eq 0 ] && [ "$NB_DONN" -eq 0 ]; then
  echo "  ${VERT}Le site est pret a etre mis en ligne.${FIN}"
elif [ "$NB_ERR" -eq 0 ]; then
  echo "  ${VERT}Aucun defaut technique.${FIN} Le site se construit et se deploie."
  echo "  Completez les informations ci-dessus avant la mise en ligne : ce sont"
  echo "  des mentions legalement obligatoires, elles ne peuvent pas etre devinees."
fi
echo

# Le code de sortie ne signale que les defauts techniques : les informations
# manquantes relevent de l'exploitant, pas d'un echec de construction.
[ "$NB_ERR" -eq 0 ]
