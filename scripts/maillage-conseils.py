#!/usr/bin/env python3
"""
Relie les articles de conseils aux pages de prestation qui les concernent.

    python3 scripts/maillage-conseils.py

Pourquoi
--------
Les cinquante-trois articles du blog n'étaient atteignables que depuis le sommaire du
blog et, pour certains, depuis un autre article. Une page qui ne reçoit qu'un
lien interne est explorée rarement et classée comme secondaire : le travail
d'écriture est fait, mais il ne sert pas.

Chaque page de prestation reçoit donc un bloc « À lire aussi » listant les
articles qui traitent VRAIMENT de son sujet. Pas une liste automatique de
tous les articles : un lien qui ne correspond à rien n'aide ni le visiteur,
ni le référencement.

Le bloc s'insère avant l'appel à l'action final. Idempotent.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "src" / "pages"

TITRES = {
    "canalisation-bouchee-que-faire": "Que faire face à une canalisation bouchée ?",
    "canalisation-bouchee-signes": "Les signes qui annoncent un bouchon",
    "comment-entretenir-canalisations": "Comment entretenir ses canalisations",
    "degorgement-ou-curage": "Dégorgement ou curage : lequel choisir ?",
    "depannage-urgence-vos-droits": "Dépannage en urgence : vos droits, les prix, les pièges",
    "eau-remonte-evier": "L'eau remonte dans l'évier : pourquoi ?",
    "entretenir-assainissement-non-collectif": "Entretenir un assainissement non collectif",
    "eviter-bouchons-canalisation": "Éviter les bouchons de canalisation",
    "pourquoi-canalisation-se-bouche": "Pourquoi une canalisation se bouche",
    "prix-degorgement": "Le prix d'un dégorgement, poste par poste",
    "quand-utiliser-camera-inspection": "Quand l'inspection caméra est utile",
    "residence-secondaire-reouverture": "Rouvrir une résidence secondaire",
    "wc-bouche-que-faire": "WC bouché : ce qu'il faut faire, et ne pas faire",
    # Huit articles d'urgence ancrés sur les quatre départements bretons.
    "regard-deborde-cotes-d-armor": "Regard qui déborde dans les Côtes-d'Armor",
    "fosse-septique-refoule-cotes-d-armor": "Fosse toutes eaux qui refoule (22)",
    "colonne-immeuble-bouchee-brest": "Colonne d'immeuble bouchée à Brest",
    "cuisine-professionnelle-bloquee-finistere": "Cuisine professionnelle bloquée (29)",
    "evacuation-bouchee-logement-etudiant-rennes": "Logement étudiant bouché à Rennes",
    "cave-inondee-pompage-urgence-ille-et-vilaine": "Cave inondée : pompage d'urgence (35)",
    "location-saisonniere-bouchon-entre-deux-arrivees-morbihan": "Location saisonnière bouchée (56)",
    "degorgement-dimanche-jour-ferie-morbihan": "Dégorgement un dimanche ou un jour férié (56)",
    # Seize articles d'urgence, quatre villes par département breton.
    "urgence-soir-appartement-saint-brieuc": "Urgence du soir en appartement (Saint-Brieuc)",
    "wc-bouche-samedi-soir-lannion": "WC bouché un samedi soir (Lannion)",
    "maison-ancienne-canalisation-bouchee-dinan": "Maison ancienne bouchée (Dinan)",
    "commerce-bouche-avant-ouverture-guingamp": "Commerce bloqué avant l'ouverture (Guingamp)",
    "evier-refoule-dimanche-midi-quimper": "L'évier refoule un dimanche midi (Quimper)",
    "odeurs-glouglous-le-soir-morlaix": "Odeurs et glouglous le soir (Morlaix)",
    "sanitaires-collectifs-bouches-week-end-concarneau": "Sanitaires collectifs bouchés (Concarneau)",
    "broyeur-sanitaire-bloque-le-soir-landerneau": "Broyeur sanitaire bloqué le soir (Landerneau)",
    "refoulement-maree-haute-saint-malo": "Refoulement à marée haute (Saint-Malo)",
    "urgence-nuit-personne-fragile-fougeres": "Urgence de nuit, personne fragile (Fougères)",
    "atelier-production-arretee-vitre": "Atelier à l'arrêt (Vitré)",
    "etat-des-lieux-reseau-bouche-bruz": "Bouchon le jour de l'état des lieux (Bruz)",
    "sanitaires-bureaux-hors-service-vannes": "Sanitaires de bureaux hors service (Vannes)",
    "lave-linge-refoule-buanderie-lorient": "Le lave-linge refoule dans la buanderie (Lorient)",
    "canalisation-bouchee-apres-travaux-auray": "Canalisation bouchée après travaux (Auray)",
    "urgence-habitat-rural-isole-pontivy": "Urgence en habitat rural isolé (Pontivy)",
    # Seize articles d'installation sanitaire et de chauffage.
    "ballon-eau-chaude-qui-fuit-saint-brieuc": "Ballon d'eau chaude qui fuit (Saint-Brieuc)",
    "robinet-qui-ne-ferme-plus-lannion": "Robinet qui ne ferme plus (Lannion)",
    "douche-italienne-maison-ancienne-dinan": "Douche à l'italienne dans l'ancien (Dinan)",
    "radiateur-qui-fuit-guingamp": "Radiateur qui fuit (Guingamp)",
    "plus-d-eau-chaude-que-verifier-brest": "Plus d'eau chaude : que vérifier (Brest)",
    "fuite-canalisation-encastree-quimper": "Fuite sur canalisation encastrée (Quimper)",
    "salle-d-eau-dans-une-chambre-morlaix": "Créer une salle d'eau (Morlaix)",
    "remplacer-wc-suspendu-concarneau": "Remplacer un WC, poser un suspendu (Concarneau)",
    "fuite-apres-compteur-rennes": "Fuite après compteur : qui paie (Rennes)",
    "baignoire-remplacee-par-douche-saint-malo": "Remplacer une baignoire par une douche (Saint-Malo)",
    "seche-serviettes-radiateur-electrique-fougeres": "Sèche-serviettes et radiateur électrique (Fougères)",
    "canalisation-gelee-rupture-au-degel-vitre": "Canalisation gelée et rupture au dégel (Vitré)",
    "raccorder-lave-linge-lave-vaisselle-vannes": "Raccorder un lave-linge (Vannes)",
    "robinet-arret-flexibles-vetustes-lorient": "Robinet d'arrêt et flexibles vétustes (Lorient)",
    "pression-trop-forte-coups-de-belier-auray": "Pression trop forte et coups de bélier (Auray)",
    "remise-en-eau-maison-inoccupee-pontivy": "Remise en eau d'une maison inoccupée (Pontivy)",
}

# Quelle prestation renvoie vers quels articles. Le rapprochement est fait
# sujet par sujet : c'est ce qui distingue un maillage utile d'un pied de page
# rempli de liens.
LIENS = {
    "degorgement": ["prix-degorgement", "degorgement-ou-curage", "residence-secondaire-reouverture"],
    "degorgement-urgence": ["canalisation-bouchee-que-faire", "canalisation-bouchee-signes",
                            "depannage-urgence-vos-droits", "degorgement-dimanche-jour-ferie-morbihan",
                            "cave-inondee-pompage-urgence-ille-et-vilaine",
                            "urgence-nuit-personne-fragile-fougeres",
                            "refoulement-maree-haute-saint-malo",
                            "canalisation-gelee-rupture-au-degel-vitre",
                            "ballon-eau-chaude-qui-fuit-saint-brieuc"],
    "debouchage-canalisation": ["canalisation-bouchee-que-faire", "pourquoi-canalisation-se-bouche",
                                "eviter-bouchons-canalisation", "depannage-urgence-vos-droits"],
    "debouchage-canalisation-exterieure": ["pourquoi-canalisation-se-bouche",
                                           "quand-utiliser-camera-inspection",
                                           "regard-deborde-cotes-d-armor"],
    "debouchage-wc": ["wc-bouche-que-faire", "eviter-bouchons-canalisation",
                      "degorgement-dimanche-jour-ferie-morbihan",
                      "wc-bouche-samedi-soir-lannion",
                      "remplacer-wc-suspendu-concarneau"],
    "debouchage-toilettes": ["wc-bouche-que-faire", "broyeur-sanitaire-bloque-le-soir-landerneau",
                             "salle-d-eau-dans-une-chambre-morlaix"],
    "debouchage-evier": ["eau-remonte-evier", "comment-entretenir-canalisations",
                         "evier-refoule-dimanche-midi-quimper"],
    "debouchage-lavabo": ["eau-remonte-evier", "eviter-bouchons-canalisation",
                          "evacuation-bouchee-logement-etudiant-rennes",
                          "robinet-qui-ne-ferme-plus-lannion",
                          "robinet-arret-flexibles-vetustes-lorient"],
    "debouchage-cuisine": ["comment-entretenir-canalisations", "eau-remonte-evier",
                           "cuisine-professionnelle-bloquee-finistere",
                           "raccorder-lave-linge-lave-vaisselle-vannes"],
    "debouchage-douche": ["eviter-bouchons-canalisation",
                          "evacuation-bouchee-logement-etudiant-rennes",
                          "location-saisonniere-bouchon-entre-deux-arrivees-morbihan",
                          "douche-italienne-maison-ancienne-dinan",
                          "baignoire-remplacee-par-douche-saint-malo"],
    "debouchage-baignoire": ["canalisation-bouchee-signes"],
    "curage-canalisation": ["degorgement-ou-curage", "pourquoi-canalisation-se-bouche",
                            "canalisation-bouchee-apres-travaux-auray",
                            "lave-linge-refoule-buanderie-lorient"],
    "inspection-camera-canalisation": ["quand-utiliser-camera-inspection"],
    "recherche-bouchon": ["canalisation-bouchee-signes", "quand-utiliser-camera-inspection",
                          "odeurs-glouglous-le-soir-morlaix",
                          "maison-ancienne-canalisation-bouchee-dinan",
                          "fuite-canalisation-encastree-quimper",
                          "fuite-apres-compteur-rennes"],
    "entretien-canalisation": ["comment-entretenir-canalisations", "eviter-bouchons-canalisation",
                               "canalisation-bouchee-signes",
                               "plus-d-eau-chaude-que-verifier-brest",
                               "radiateur-qui-fuit-guingamp"],
    "pompage": ["entretenir-assainissement-non-collectif",
                "cave-inondee-pompage-urgence-ille-et-vilaine",
                "fosse-septique-refoule-cotes-d-armor"],
    "assainissement": ["entretenir-assainissement-non-collectif", "residence-secondaire-reouverture",
                       "fosse-septique-refoule-cotes-d-armor",
                       "urgence-habitat-rural-isole-pontivy",
                       "remise-en-eau-maison-inoccupee-pontivy"],
    "degorgement-professionnel": ["comment-entretenir-canalisations", "degorgement-ou-curage",
                                  "cuisine-professionnelle-bloquee-finistere",
                                  "atelier-production-arretee-vitre",
                                  "sanitaires-bureaux-hors-service-vannes",
                                  "commerce-bouche-avant-ouverture-guingamp"],
    "degorgement-collectif": ["eviter-bouchons-canalisation", "pourquoi-canalisation-se-bouche",
                              "colonne-immeuble-bouchee-brest",
                              "urgence-soir-appartement-saint-brieuc",
                              "sanitaires-collectifs-bouches-week-end-concarneau"],
    "tarifs": ["prix-degorgement", "degorgement-ou-curage", "depannage-urgence-vos-droits"],
    "devis": ["prix-degorgement", "depannage-urgence-vos-droits",
              "etat-des-lieux-reseau-bouche-bruz",
              "pression-trop-forte-coups-de-belier-auray",
              "seche-serviettes-radiateur-electrique-fougeres"],
    "faq": ["prix-degorgement", "canalisation-bouchee-que-faire", "wc-bouche-que-faire"],

    # Les pages départementales renvoient vers les articles écrits POUR elles :
    # c'est ce qui donne à chaque département un contenu propre plutôt qu'un
    # gabarit recopié six fois.
    "departements/cotes-d-armor": ["urgence-soir-appartement-saint-brieuc",
                                   "wc-bouche-samedi-soir-lannion",
                                   "maison-ancienne-canalisation-bouchee-dinan",
                                   "commerce-bouche-avant-ouverture-guingamp",
                                   "regard-deborde-cotes-d-armor",
                                   "fosse-septique-refoule-cotes-d-armor",
                                   "ballon-eau-chaude-qui-fuit-saint-brieuc",
                                   "robinet-qui-ne-ferme-plus-lannion",
                                   "douche-italienne-maison-ancienne-dinan",
                                   "radiateur-qui-fuit-guingamp"],
    "departements/finistere": ["evier-refoule-dimanche-midi-quimper",
                               "odeurs-glouglous-le-soir-morlaix",
                               "sanitaires-collectifs-bouches-week-end-concarneau",
                               "broyeur-sanitaire-bloque-le-soir-landerneau",
                               "colonne-immeuble-bouchee-brest",
                               "cuisine-professionnelle-bloquee-finistere",
                               "plus-d-eau-chaude-que-verifier-brest",
                               "fuite-canalisation-encastree-quimper",
                               "salle-d-eau-dans-une-chambre-morlaix",
                               "remplacer-wc-suspendu-concarneau"],
    "departements/ille-et-vilaine": ["refoulement-maree-haute-saint-malo",
                                     "urgence-nuit-personne-fragile-fougeres",
                                     "atelier-production-arretee-vitre",
                                     "etat-des-lieux-reseau-bouche-bruz",
                                     "cave-inondee-pompage-urgence-ille-et-vilaine",
                                     "evacuation-bouchee-logement-etudiant-rennes",
                                     "fuite-apres-compteur-rennes",
                                     "baignoire-remplacee-par-douche-saint-malo",
                                     "seche-serviettes-radiateur-electrique-fougeres",
                                     "canalisation-gelee-rupture-au-degel-vitre"],
    "departements/morbihan": ["sanitaires-bureaux-hors-service-vannes",
                              "lave-linge-refoule-buanderie-lorient",
                              "canalisation-bouchee-apres-travaux-auray",
                              "urgence-habitat-rural-isole-pontivy",
                              "degorgement-dimanche-jour-ferie-morbihan",
                              "location-saisonniere-bouchon-entre-deux-arrivees-morbihan",
                              "raccorder-lave-linge-lave-vaisselle-vannes",
                              "robinet-arret-flexibles-vetustes-lorient",
                              "pression-trop-forte-coups-de-belier-auray",
                              "remise-en-eau-maison-inoccupee-pontivy"],
}

MARQUE = '<!-- maillage-conseils -->'


def bloc(articles) -> str:
    items = "\n".join(
        f'      <li><a href="/blog/{a}">{TITRES[a]}</a></li>' for a in articles)
    return f'''{MARQUE}
<section class="alt">
  <div class="wrap">
    <div class="liens-connexes">
      <h2>À lire aussi</h2>
      <ul>
{items}
        <li><a href="/blog/">Tous nos conseils canalisations</a></li>
      </ul>
    </div>
  </div>
</section>

'''


def traiter(slug: str, articles) -> str | None:
    f = PAGES / f"{slug}.html"
    if not f.is_file():
        return f"{slug} : page introuvable"
    s = f.read_text(encoding="utf-8")

    # Un bloc déjà posé est REMPLACÉ, pas laissé tel quel : sans cela, un
    # article ajouté au blog après coup ne serait jamais relié aux pages déjà
    # traitées, et le script mentirait sur ce qu'il garantit.
    if MARQUE in s:
        debut = s.index(MARQUE)
        fin = s.index("</section>", debut) + len("</section>\n\n")
        avant = s[debut:fin]
        neuf = bloc(articles)
        if avant == neuf:
            return None
        f.write_text(s[:debut] + neuf + s[fin:], encoding="utf-8")
        return f"{slug} → bloc mis à jour, {len(articles)} article(s)"

    i = s.rfind('<section class="cta-final">')
    if i == -1:
        return f"{slug} : pas d'appel à l'action final, bloc non posé"
    f.write_text(s[:i] + bloc(articles) + s[i:], encoding="utf-8")
    return f"{slug} → {len(articles)} article(s)"


if __name__ == "__main__":
    faits = [r for slug, a in LIENS.items() if (r := traiter(slug, a))]
    print(f"{len(faits)} page(s) traitée(s)")
    for r in faits:
        print("   ✓", r)
    sys.exit(0)
