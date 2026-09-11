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
# S'il change, modifiez cette ligne et rien d'autre : tout le site suit.
#
# Ce domaine est écrit dans TOUTES les adresses canoniques et dans le sitemap.
# Une page servie depuis un autre domaine — un sous-domaine de
# prévisualisation, par exemple — désigne donc une adresse qui n'est pas la
# sienne, et aucun moteur ne l'indexera. C'est sans conséquence tant que le
# site est en préparation, et bloquant le jour de l'ouverture.
#
# Pour construire une version de démonstration cohérente avec l'adresse où
# elle sera servie, sans toucher à ce fichier :
#
#     DOMAINE=exemple.hostingersite.com bash scripts/build.sh
DOMAINE="${DOMAINE:-degorgement-richard.fr}"
BASE_URL="https://${DOMAINE}"

# --- Contact ----------------------------------------------------------------
# Numéro repris à l'identique du site serrurerie : même entreprise, même
# standard. Ne créez jamais un second numéro : il diviserait le suivi des
# appels et brouillerait la fiche Google Business Profile.
TELEPHONE="02 20 06 00 75"
TELEPHONE_E164="+33220060075"
EMAIL="contact@deboucheur-richard.fr"

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

# --- Tarifs : prix d'appel « à partir de » -----------------------------------
# ⚠ AUCUN PRIX N'EST INVENTÉ, et aucun ne doit l'être. Un prix affiché engage
# l'entreprise : l'arrêté du 24 janvier 2017 impose l'affichage des tarifs de
# dépannage à domicile, et un montant annoncé puis dépassé sans accord écrit
# est une pratique commerciale trompeuse. Les forfaits du site serrurerie ne
# sont pas transposables : ouvrir une porte et hydrocurer un collecteur n'ont
# ni le même matériel, ni la même durée, ni la même assurance.
#
# Ces montants sont des PRIX D'APPEL, affichés « à partir de ». Ils doivent
# donc être les minima RÉELLEMENT pratiqués, ceux de l'intervention la plus
# simple de chaque catégorie — pas une moyenne, et pas un prix d'accroche que
# personne ne paie jamais.
#
# Le chiffre seul, sans unité ni mention : « 129 », pas « à partir de 129 € ».
# Le site compose la phrase, et l'unité vient de UNITE_PRIX ci-dessus.
#
# Une valeur VIDE n'affiche rien. Aucun crochet, aucun « à renseigner » ne
# part en production : la page /tarifs explique alors les facteurs de prix et
# renvoie au devis, ce qui reste conforme tant qu'aucun tarif n'est publié.
PRIX_DEPUIS_DEBOUCHAGE=""            # évier, lavabo, douche, baignoire
PRIX_DEPUIS_DEBOUCHAGE_WC=""         # WC et toilettes
PRIX_DEPUIS_HYDROCURAGE=""           # curage haute pression
PRIX_DEPUIS_INSPECTION_CAMERA=""     # inspection vidéo
PRIX_DEPUIS_POMPAGE=""               # pompage, fosse, bac à graisses

# Les trois lignes que l'arrêté du 24 janvier 2017 impose d'afficher dès
# qu'un tarif est publié. Même règle : le chiffre seul.
TAUX_HORAIRE=""                      # main-d'œuvre, à l'heure
FRAIS_DEPLACEMENT=""                 # forfait de déplacement
MAJORATION_NUIT=""                   # en pourcentage, ex. « 50 » pour +50 %

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
EMAIL_DEVIS="contact@deboucheur-richard.fr"
# Adresse qui ENVOIE le message. Sur un mutualisé Hostinger, elle DOIT
# appartenir au domaine du site, sinon le message part en spam ou est rejeté
# (SPF/DKIM). Créez-la dans hPanel > Emails avant la mise en ligne.
EMAIL_EXPEDITEUR="site@${DOMAINE}"
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
