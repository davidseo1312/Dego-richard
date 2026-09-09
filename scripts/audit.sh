#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Audit complet avant mise en ligne.
#
#   bash scripts/audit.sh
#
# Enchaîne tous les contrôles disponibles et affiche un tableau de synthèse.
# Les étapes qui demandent un outil absent (Python, PHP) sont marquées
# « ignorée » et n'empêchent pas l'audit d'aboutir : seuls le build et le
# contrôle SEO sont indispensables.
#
# Code de sortie 1 si une étape obligatoire échoue.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; VERT=$'\033[32m'; GRAS=$'\033[1m'; FIN=$'\033[0m'

RESULTATS=""
ECHEC=0

etape() { RESULTATS="${RESULTATS}$1|$2"$'\n'; }
titre() { echo; echo "${GRAS}=== $1 ===${FIN}"; echo; }

# --- 1. Construction --------------------------------------------------------
titre "1/6  Construction"
if bash scripts/build.sh; then
  etape "BUILD" "OK"
else
  etape "BUILD" "ECHEC"; ECHEC=1
  echo "${ROUGE}Le build a échoué : les étapes suivantes n'ont pas de sens.${FIN}"
  exit 1
fi

# --- 2. SEO, GEO, liens, ressources ----------------------------------------
titre "2/6  Contrôle SEO / GEO, liens internes et ressources"
if bash scripts/check-seo.sh; then
  etape "SEO / GEO / LIENS" "OK"
else
  etape "SEO / GEO / LIENS" "ECHEC"; ECHEC=1
fi

# --- 3. Structure HTML ------------------------------------------------------
titre "3/6  Structure HTML"
if command -v python3 >/dev/null; then
  if python3 scripts/check-html.py; then
    etape "STRUCTURE HTML" "OK"
  else
    etape "STRUCTURE HTML" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : contrôle ignoré."
  etape "STRUCTURE HTML" "IGNOREE"
fi

# --- 4. Contenu local -------------------------------------------------------
titre "4/6  Similarité des pages locales"
if command -v python3 >/dev/null; then
  if python3 scripts/check-contenu-local.py; then
    etape "CONTENU LOCAL" "OK"
  else
    etape "CONTENU LOCAL" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : contrôle ignoré."
  etape "CONTENU LOCAL" "IGNOREE"
fi

# --- 5. Données structurées -------------------------------------------------
titre "5/6  Données structurées (JSON-LD)"
if command -v python3 >/dev/null; then
  if python3 - <<'PY'
import json, re, glob, sys
invalides, blocs = [], 0
for f in sorted(set(glob.glob('public/**/*.html', recursive=True))):
    html = open(f, encoding='utf-8').read()
    for bloc in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        blocs += 1
        try:
            json.loads(bloc)
        except Exception as e:
            invalides.append(f"{f} : {e}")
print(f"{blocs} bloc(s) JSON-LD analysé(s)")
for i in invalides:
    print("x", i)
sys.exit(1 if invalides else 0)
PY
  then
    etape "JSON-LD" "OK"
  else
    etape "JSON-LD" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : contrôle ignoré."
  etape "JSON-LD" "IGNOREE"
fi

# --- 6. Test HTTP -----------------------------------------------------------
titre "6/6  Test HTTP du dossier de production"
if command -v php >/dev/null && command -v curl >/dev/null; then
  if bash scripts/test-http.sh; then
    etape "TEST HTTP / 403" "OK"
  else
    etape "TEST HTTP / 403" "ECHEC"; ECHEC=1
  fi
else
  echo "PHP ou curl absent : test ignoré."
  etape "TEST HTTP / 403" "IGNOREE"
fi

# --- Synthèse ---------------------------------------------------------------
echo
echo "${GRAS}=== Synthèse ===${FIN}"
echo
while IFS='|' read -r libelle statut; do
  [ -n "$libelle" ] || continue
  case "$statut" in
    OK)      couleur="$VERT" ;;
    IGNOREE) couleur="$JAUNE" ;;
    *)       couleur="$ROUGE" ;;
  esac
  printf "  %-22s %s%s%s\n" "$libelle" "$couleur" "$statut" "$FIN"
done <<< "$RESULTATS"
echo

if [ "$ECHEC" -eq 0 ]; then
  echo "  ${VERT}Audit réussi. Le dossier public/ est déployable tel quel.${FIN}"
else
  echo "  ${ROUGE}Audit en échec. Corrigez avant de publier.${FIN}"
fi
echo

exit "$ECHEC"
