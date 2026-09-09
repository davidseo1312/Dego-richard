# ---------------------------------------------------------------------------
# Configuration centrale du site.
# Toute valeur modifiée ici est répercutée sur l'ensemble des pages au build.
#
# Les valeurs d'identité juridique proviennent du site serrurerie exploité par
# la même entité (dépôt davidseo1312/serrurier-richard, branche
# claude/locksmith-website-build-xv5qk7, fichier src/config.sh). Elles n'ont
# pas été ressaisies à la main : même entreprise, mêmes mentions légales.
# ---------------------------------------------------------------------------

# --- Identité ---------------------------------------------------------------
NOM_COMMERCIAL="Dégorgement Richard"
BASELINE="Dégorgement, débouchage et assainissement dans le Grand Ouest"
# ⚠ DOMAINE À CONFIRMER : aucun nom de domaine n'était fixé pour ce nouveau
# site. Celui-ci est un choix par défaut, cohérent avec le nom commercial.
# S'il change, modifiez ces deux lignes et rien d'autre : tout le site suit.
DOMAINE="degorgement-richard.fr"
BASE_URL="https://degorgement-richard.fr"

# --- Contact ----------------------------------------------------------------
# Numéro repris à l'identique du site serrurerie : même entreprise, même
# standard. Ne créez jamais un second numéro : il diviserait le suivi des
# appels et brouillerait la fiche Google Business Profile.
TELEPHONE="02 20 06 00 75"
TELEPHONE_E164="+33220060075"
EMAIL="contact@degorgement-richard.fr"

# --- Identité légale --------------------------------------------------------
# Données reprises du registre national des entreprises via le site
# serrurerie (SIREN 901133041), vérifiées le 08/09/2026.
RAISON_SOCIALE="Bilal Assoul"
FORME_JURIDIQUE="Entrepreneur individuel"
CAPITAL=""                       # Sans objet pour une entreprise individuelle
SIRET="901 133 041 00011"
SIREN="901 133 041"
RCS="Immatriculée au Registre National des Entreprises (RNE) sous le numéro 901 133 041"
DATE_CREATION="6 juillet 2021"

# Aucun numéro de TVA intracommunautaire actif au 08/09/2026 (vérifié VIES).
TVA_NUMERO=""
MENTION_TVA="TVA non applicable, article 293 B du code général des impôts"
UNITE_PRIX="€"                   # Mettre "€ TTC" si assujetti à la TVA

# --- Adresse du siège (mentions légales) ------------------------------------
SIEGE_RUE="1 rue Albert Simonin"
SIEGE_CP="92400"
SIEGE_VILLE="Courbevoie"

# --- Établissement de rattachement (balisage LocalBusiness) -----------------
# ⚠ Le siège déclaré au registre est en Île-de-France, alors que l'activité
# couvre les six départements du Grand Ouest. Tant qu'aucun établissement
# n'est réellement immatriculé dans la zone, le balisage LocalBusiness reprend
# l'adresse RÉELLE du siège : inventer une agence à Rennes ou à Nantes serait
# une adresse fictive, sanctionnée par Google et trompeuse pour le client.
# Le site n'affiche donc jamais « agence à [ville] », seulement
# « intervention à [ville] ». Voir README, section « Cohérence géographique ».
ADRESSE_RUE="1 rue Albert Simonin"
ADRESSE_CP="92400"
ADRESSE_VILLE="Courbevoie"
LATITUDE="48.897442"
LONGITUDE="2.256290"

# --- Activité déclarée ------------------------------------------------------
# ⚠ APE au registre : 81.29A (désinfection, désinsectisation, dératisation).
# Le débouchage et le curage de canalisations relèvent du 37.00Z (collecte et
# traitement des eaux usées) ou du 43.22B (travaux d'installation d'eau et de
# gaz). À faire corriger auprès de l'INSEE, et vérifier que la RC Pro couvre
# bien l'assainissement avant la première intervention.
CODE_APE="81.29A"

# --- Assurances et médiation (obligatoires) ---------------------------------
# Ces valeurs ne peuvent pas être devinées : ce sont des obligations légales.
ASSUREUR_RCPRO="[ASSUREUR RC PRO]"
POLICE_RCPRO="[N° DE POLICE]"
ASSUREUR_DECENNALE="[ASSUREUR DÉCENNALE]"
MEDIATEUR_NOM="[NOM DU MÉDIATEUR DE LA CONSOMMATION]"
MEDIATEUR_URL="[URL DU MÉDIATEUR]"

# --- Tarifs (arrêté du 24 janvier 2017) -------------------------------------
# ⚠ AUCUN PRIX N'EST INVENTÉ. Les forfaits du site serrurerie ne sont PAS
# transposables : ouvrir une porte et hydrocurer un collecteur n'ont ni le même
# matériel, ni la même durée, ni la même assurance. Renseignez ici les montants
# RÉELLEMENT pratiqués ; tant qu'ils restent entre crochets, la page /tarifs
# affiche l'explication des facteurs de prix et renvoie au devis, sans chiffre.
# L'affichage des prix est obligatoire pour le dépannage à domicile.
TAUX_HORAIRE="[TAUX HORAIRE À RENSEIGNER]"
FRAIS_DEPLACEMENT="[FRAIS DE DÉPLACEMENT À RENSEIGNER]"
MAJORATION_NUIT="[MAJORATION NUIT ET WEEK-END À RENSEIGNER]"
FORFAIT_DEBOUCHAGE_SIMPLE="[FORFAIT DÉBOUCHAGE SIMPLE À RENSEIGNER]"
FORFAIT_DEBOUCHAGE_WC="[FORFAIT DÉBOUCHAGE WC À RENSEIGNER]"
FORFAIT_HYDROCURAGE="[FORFAIT HYDROCURAGE À RENSEIGNER]"
FORFAIT_INSPECTION_CAMERA="[FORFAIT INSPECTION CAMÉRA À RENSEIGNER]"
FORFAIT_POMPAGE="[FORFAIT POMPAGE À RENSEIGNER]"

# --- Indexation -------------------------------------------------------------
# "index" en production, "noindex" pour une préproduction ou une recette.
# Cette valeur pilote à la fois la balise <meta name="robots"> de chaque page
# et le contenu de robots.txt : les deux ne peuvent pas diverger.
ROBOTS_POLICY="index"

# --- Disponibilité et horaires ---------------------------------------------
# ⚠ N'annoncez que la disponibilité réellement assurée. Une promesse « 24h/24 »
# non tenue est une pratique commerciale trompeuse (art. L121-2 code de la
# consommation). Ces valeurs alimentent aussi le balisage LocalBusiness.
DISPONIBILITE="24h/24 et 7j/7"
HORAIRES_URGENCE="24 heures sur 24, 7 jours sur 7, jours fériés compris"
HORAIRES_BUREAU="du lundi au vendredi, 8h – 19h"
DELAI_REPONSE="24 à 48 heures ouvrées"

# --- Zone d'intervention (texte affiché) ------------------------------------
# SIX départements, et aucun autre. Toute page qui annonce une intervention
# hors de cette liste est un défaut : scripts/check-seo.sh la refuse.
ZONE_INTERVENTION="Côtes-d'Armor (22), Finistère (29), Ille-et-Vilaine (35), Morbihan (56), Loire-Atlantique (44) et Maine-et-Loire (49)"
ZONE_COURTE="Bretagne et Pays de la Loire"

# --- Formulaire de demande d'intervention -----------------------------------
EMAIL_DEVIS="contact@degorgement-richard.fr"
# Adresse qui ENVOIE le message. Sur un mutualisé Hostinger, elle DOIT
# appartenir au domaine du site, sinon le message part en spam ou est rejeté
# (SPF/DKIM). Créez-la dans hPanel > Emails avant la mise en ligne.
EMAIL_EXPEDITEUR="site@degorgement-richard.fr"
DEVIS_PHOTO_MAX_MO="5"

# --- Mesure d'audience et vérification Google -------------------------------
# Laisser vide désactive proprement la fonctionnalité : aucun script tiers
# n'est chargé, aucune balise vide n'est écrite dans le HTML.
#   GA4_ID   : « G-XXXXXXXXXX »
#   GTM_ID   : « GTM-XXXXXXX » (laisser vide si GA4 est utilisé seul)
#   GSC_CODE : contenu de l'attribut « content » fourni par Search Console
GA4_ID=""
GTM_ID=""
GSC_CODE=""

# --- Réseaux sociaux et fiche Google Business Profile -----------------------
# Renseignez uniquement les profils qui existent réellement : ils alimentent
# le champ « sameAs » des données structurées, que Google recoupe.
URL_GOOGLE_BUSINESS=""
URL_FACEBOOK=""
URL_LINKEDIN=""
