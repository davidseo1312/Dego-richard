#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Test HTTP réel du dossier de production.
#
#   bash scripts/test-http.sh            # port 8090 par défaut
#
# Démarre un serveur local sur public/, avec le routeur qui reproduit les
# règles du .htaccess, puis interroge :
#   - toutes les URLs déclarées au sitemap ;
#   - les fichiers techniques (robots.txt, sitemap.xml, .htaccess, assets) ;
#   - les redirections 301 ;
#   - une URL inexistante, qui doit répondre 404 et non 403 ni 200.
#
# Aucune réponse ne doit être un 403 : c'est le défaut exact que ce projet
# cherche à rendre impossible.
#
# Sortie 1 dès qu'une URL ne répond pas comme attendu.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${1:-8090}"
BASE="http://localhost:${PORT}"

command -v php   >/dev/null || { echo "PHP est requis pour ce test."; exit 1; }
command -v curl  >/dev/null || { echo "curl est requis pour ce test."; exit 1; }
[ -d public ] || { echo "public/ absent — lancez d'abord : bash scripts/build.sh"; exit 1; }

php -S "localhost:${PORT}" -t public scripts/routeur-local.php > /dev/null 2>&1 &
SERVEUR=$!
trap 'kill "$SERVEUR" 2>/dev/null' EXIT INT TERM

for _ in $(seq 1 60); do
  curl -sf -o /dev/null "${BASE}/" && break
  sleep 0.25
done

ROUGE=$'\033[31m'; VERT=$'\033[32m'; GRAS=$'\033[1m'; FIN=$'\033[0m'
ECHECS=0
NB=0
INTERDITS=0

verifier() {                    # verifier <chemin> <code attendu>
  local chemin="$1" attendu="$2" code
  code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}${chemin}")
  NB=$((NB + 1))
  [ "$code" = "403" ] && INTERDITS=$((INTERDITS + 1))
  if [ "$code" != "$attendu" ]; then
    echo "  ${ROUGE}x${FIN} $chemin -> $code (attendu $attendu)"
    ECHECS=$((ECHECS + 1))
    return 1
  fi
  return 0
}

echo
echo "${GRAS}Test HTTP du dossier de production — ${BASE}${FIN}"

# --- 1. Toutes les URLs du sitemap -----------------------------------------
echo
echo "1. URLs declarees au sitemap"
source src/config.sh
NB_SITEMAP=0
while IFS= read -r url; do
  chemin="${url#$BASE_URL}"
  [ -n "$chemin" ] || chemin="/"
  verifier "$chemin" 200 && NB_SITEMAP=$((NB_SITEMAP + 1))
done <<< "$(sed -n 's/.*<loc>\(.*\)<\/loc>.*/\1/p' public/sitemap.xml)"
echo "  ${VERT}v${FIN} $NB_SITEMAP URL(s) du sitemap repondent 200"

# --- 2. Pages et fichiers techniques ---------------------------------------
echo
echo "2. Fichiers techniques et pages cles"
for chemin in / /robots.txt /sitemap.xml /manifest.webmanifest \
              /prestations /assets/css/style.css /assets/js/site.js \
              /assets/img/favicon.svg /assets/img/partage/og-default.jpg \
              /degorgement /degorgement-urgence /debouchage-canalisation /debouchage-wc \
              /departements/cotes-d-armor /departements/finistere \
              /departements/ille-et-vilaine /departements/morbihan \
              /departements/loire-atlantique /departements/maine-et-loire \
              /degorgement-rennes /degorgement-nantes /degorgement-brest \
              /blog/ /tarifs /devis /contact /faq \
              /mentions-legales /politique-confidentialite /conditions-generales; do
  verifier "$chemin" 200
done
[ "$ECHECS" -eq 0 ] && echo "  ${VERT}v${FIN} toutes les pages cles repondent 200"

# --- 3. Redirections 301 ---------------------------------------------------
echo
echo "3. Redirections 301"
# La liste vient du .htaccess lui-meme, pas d'une copie : c'est une copie
# divergente qui a laisse passer « /services -> /services », une boucle
# infinie invisible en local et fatale en ligne.
#
# Chaque redirection est suivie : elle doit aboutir a un 200 EN UN SEUL SAUT.
# Verifier le seul code 301 ne suffisait pas - une boucle repond 301, elle
# aussi.
NB_REDIR=0
ECHECS_AVANT_REDIR="$ECHECS"
while IFS='|' read -r source cible; do
  [ -z "$source" ] && continue
  NB_REDIR=$((NB_REDIR + 1))
  NB=$((NB + 1))
  RECU=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${source}")
  ARRIVEE=$(curl -s -o /dev/null -w "%{redirect_url}" "${BASE}${source}")
  FINAL=$(curl -s -o /dev/null -w "%{http_code}" --max-redirs 3 -L "${BASE}${source}")
  if [ "$RECU" != "301" ]; then
    echo "  ${ROUGE}x${FIN} ${source} repond $RECU au lieu de 301"
    ECHECS=$((ECHECS + 1))
  elif [ "${ARRIVEE##*"${BASE}"}" = "$source" ]; then
    echo "  ${ROUGE}x${FIN} ${source} redirige vers lui-meme - boucle infinie"
    ECHECS=$((ECHECS + 1))
  elif [ "$FINAL" != "200" ]; then
    echo "  ${ROUGE}x${FIN} ${source} aboutit a $FINAL (attendu : $cible)"
    ECHECS=$((ECHECS + 1))
  fi
done <<< "$(sed -n 's#^RewriteRule \^\([a-z0-9/-]*\)/?\$ *\(/[^ ]*\).*\[R=301.*#/\1|\2#p' public/.htaccess)"
[ "$ECHECS" -eq "$ECHECS_AVANT_REDIR" ] \
  && echo "  ${VERT}v${FIN} $NB_REDIR redirection(s) du .htaccess aboutissent en un saut"

for chemin in /index.html /tarifs.html /tarifs/; do
  verifier "$chemin" 301
done

# --- 4. Page inexistante ---------------------------------------------------
echo
echo "4. Page inexistante"
verifier "/cette-page-n-existe-pas" 404
CORPS_404=$(curl -s "${BASE}/cette-page-n-existe-pas")
if grep -q "404" <<< "$CORPS_404"; then
  echo "  ${VERT}v${FIN} la page 404 personnalisee est bien servie"
else
  echo "  ${ROUGE}x${FIN} la reponse 404 ne sert pas public/404.html"
  ECHECS=$((ECHECS + 1))
fi

# --- Bilan -----------------------------------------------------------------
echo
echo "${GRAS}Bilan${FIN}"
echo "  $NB URL(s) testee(s), $ECHECS echec(s)"
if [ "$INTERDITS" -eq 0 ]; then
  echo "  ${VERT}v${FIN} aucun 403 Forbidden"
else
  echo "  ${ROUGE}x${FIN} $INTERDITS reponse(s) 403 Forbidden"
  ECHECS=$((ECHECS + 1))
fi
echo

[ "$ECHECS" -eq 0 ] || { echo "TEST HTTP : ECHEC"; exit 1; }
echo "TEST HTTP : OK"
