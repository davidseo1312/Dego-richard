#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Génère public/sitemap.xml et public/robots.txt à partir des pages réellement
# construites. Appelé automatiquement par scripts/build.sh.
#
# Le sitemap ne contient QUE des pages indexables : celles marquées
# « sitemap: non » (404, remerciement) sont écartées en amont par build.sh, et
# celles marquées « robots: noindex » sont refusées ici, car déclarer au
# sitemap une page qu'on demande à Google d'ignorer est contradictoire.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source src/config.sh

ENTRIES="${1:-}"
TODAY="$(date +%Y-%m-%d)"

{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
  echo '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
  while IFS='|' read -r url priority lastmod; do
    [ -n "$url" ] || continue
    [ -n "$lastmod" ] || lastmod="$TODAY"
    printf '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>\n' \
      "$url" "$lastmod" "$priority"
    # Photographies portées par la page. Seules les prises de vue réelles sont
    # déclarées : un schéma technique n'a rien à faire dans Google Images, et
    # les déclarer toutes reviendrait à noyer les cinq qui comptent.
    chemin="public${url#${BASE_URL}}"
    [ "$chemin" = "public" ] && chemin="public/"
    [ -d "$chemin" ] && chemin="${chemin%/}/index.html"
    [ -f "$chemin" ] || chemin="${chemin}.html"
    if [ -f "$chemin" ]; then
      { grep -oE 'src="/assets/img/(interventions|plomberie|debouchage|degorgement|camera|curage|assainissement|avant-apres)/[^"]+"' "$chemin" || true; } \
        | sed 's/^src="//;s/"$//' | sort -u \
        | while read -r img; do
            printf '    <image:image><image:loc>%s%s</image:loc></image:image>\n' "$BASE_URL" "$img"
          done
    fi
    printf '  </url>\n'
  done <<< "$ENTRIES"
  echo '</urlset>'
} > public/sitemap.xml

if [ "$ROBOTS_POLICY" = "index" ]; then
  cat > public/robots.txt <<ROBOTS
User-agent: *
Allow: /

# Le formulaire n'a rien à indexer : c'est un point de traitement, pas une page.
Disallow: /envoi-demande.php

Sitemap: ${BASE_URL}/sitemap.xml
ROBOTS
else
  # Site non prêt : on bloque toute exploration.
  cat > public/robots.txt <<ROBOTS
User-agent: *
Disallow: /
ROBOTS
fi

echo "✓ sitemap.xml ($(grep -c '<loc>' public/sitemap.xml) URLs) et robots.txt générés"
