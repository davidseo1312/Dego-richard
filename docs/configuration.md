# Référence de configuration

Toutes les valeurs globales du site vivent dans `src/config.sh`. Elles sont
lues par `scripts/build.sh`, exportées dans l'environnement, puis substituées
partout où le HTML et le PHP écrivent `{{NOM_DE_LA_CLE}}`.

Après toute modification :

```bash
bash scripts/build.sh
```

Une valeur inconnue laisse le token `{{...}}` intact dans le résultat, et le
build échoue : aucune faute de frappe ne peut passer en production.

---

## Identité

| Clé | Rôle |
|---|---|
| `NOM_COMMERCIAL` | Nom affiché dans l'en-tête, le pied de page, les données structurées et l'objet des e-mails. |
| `BASELINE` | Phrase d'accroche sous le nom, et `og:image:alt`. |
| `DOMAINE` | Nom de domaine sans protocole. Utilisé dans les mentions légales. |
| `BASE_URL` | URL complète avec `https://`, **sans barre oblique finale**. Sert aux canoniques, à Open Graph, au sitemap et aux `@id` JSON-LD. |

> `DOMAINE` et `BASE_URL` doivent désigner le même domaine. Une divergence
> produirait des canoniques pointant ailleurs que le site.

---

## Contact

| Clé | Rôle |
|---|---|
| `TELEPHONE` | Numéro affiché, au format lisible. |
| `TELEPHONE_E164` | Le même au format international (`+33…`), pour les liens `tel:` et le balisage. |
| `EMAIL` | Adresse de contact publiée. |

Ce numéro est le **seul** du site. `scripts/check-seo.sh` échoue si un second
`tel:` apparaît quelque part : sur un site de dépannage, un numéro parasite
divise le suivi des appels et brouille la fiche Google Business Profile.

---

## Identité légale

| Clé | Rôle |
|---|---|
| `RAISON_SOCIALE` | Dénomination au registre. |
| `FORME_JURIDIQUE` | Entrepreneur individuel, SASU, SARL… |
| `CAPITAL` | Sans objet pour une entreprise individuelle. |
| `SIRET`, `SIREN`, `RCS`, `DATE_CREATION` | Mentions obligatoires. |
| `TVA_NUMERO` | Numéro intracommunautaire, s'il existe. |
| `MENTION_TVA` | Phrase affichée sur les pages tarifs, CGV et mentions légales. |
| `UNITE_PRIX` | `€` en franchise de TVA, `€ TTC` si assujetti. |
| `CODE_APE` | Code d'activité déclaré. |

Ces valeurs proviennent du registre national des entreprises et sont reprises à
l'identique du site de serrurerie exploité par la même entité : même
entreprise, mêmes mentions légales.

---

## Adresses

Deux adresses distinctes, à ne pas confondre.

| Clé | Rôle |
|---|---|
| `SIEGE_RUE`, `SIEGE_CP`, `SIEGE_VILLE` | Adresse **déclarée au registre**. Obligatoire dans les mentions légales, les CGV et la politique de confidentialité. |
| `ADRESSE_RUE`, `ADRESSE_CP`, `ADRESSE_VILLE`, `LATITUDE`, `LONGITUDE` | Adresse de l'**établissement** utilisée par le balisage `LocalBusiness`. |

En l'absence d'établissement réellement immatriculé dans la zone
d'intervention, les deux jeux de valeurs sont identiques : le balisage reprend
l'adresse réelle du siège. Renseigner une adresse fictive dans la zone serait
sanctionné par Google et trompeur pour le client.

Le site n'affiche jamais « agence à [ville] », seulement « intervention à
[ville] ».

---

## Assurances et médiation

| Clé | Rôle |
|---|---|
| `ASSUREUR_RCPRO`, `POLICE_RCPRO` | Responsabilité civile professionnelle — art. L.243-2 du code des assurances. |
| `ASSUREUR_DECENNALE` | Garantie décennale. |
| `MEDIATEUR_NOM`, `MEDIATEUR_URL` | Médiateur de la consommation — art. L.616-1 du code de la consommation. |

Ces valeurs sont entre crochets tant qu'elles ne sont pas fournies.
`scripts/check-seo.sh` les signale à chaque exécution, en les distinguant des
défauts techniques : elles relèvent de l'exploitant, pas du code.

---

## Disponibilité et horaires

| Clé | Rôle |
|---|---|
| `DISPONIBILITE` | Formule courte, affichée dans le bandeau d'urgence. |
| `HORAIRES_URGENCE` | Amplitude réelle du dépannage. Alimente aussi `openingHoursSpecification`. |
| `HORAIRES_BUREAU` | Créneau de traitement du formulaire et des devis. |
| `DELAI_REPONSE` | Délai annoncé après une demande écrite. |

> N'annoncez que la disponibilité **réellement assurée**. Une promesse « 24h/24 »
> non tenue est une pratique commerciale trompeuse (art. L.121-2 du code de la
> consommation), et elle fait chuter la note Google Business Profile.

---

## Zone d'intervention

| Clé | Rôle |
|---|---|
| `ZONE_INTERVENTION` | Liste complète des six départements, affichée sur toutes les pages. |
| `ZONE_COURTE` | Formule abrégée. |

Le périmètre est verrouillé à trois niveaux :

* `scripts/build.sh` **échoue** si un département hors zone apparaît dans une
  page construite ;
* `scripts/check-seo.sh` contrôle la présence des six départements sur
  l'accueil et l'existence des six pages départementales ;
* `static/envoi-demande.php` refuse une demande dont le département n'est pas
  dans la liste, et vérifie la cohérence avec le code postal saisi.

---

## Tarifs

| Clé | Rôle |
|---|---|
| `TAUX_HORAIRE` | Main-d'œuvre horaire. |
| `FRAIS_DEPLACEMENT` | Déplacement, annoncé au téléphone. |
| `MAJORATION_NUIT` | Majoration nuit, dimanche et jours fériés. |
| `FORFAIT_DEBOUCHAGE_SIMPLE`, `FORFAIT_DEBOUCHAGE_WC`, `FORFAIT_HYDROCURAGE`, `FORFAIT_INSPECTION_CAMERA`, `FORFAIT_POMPAGE` | Forfaits affichés sur `/tarifs`. |

L'arrêté du 24 janvier 2017 impose l'affichage des conditions tarifaires pour
le dépannage à domicile. **Ces montants doivent correspondre aux tarifs
réellement pratiqués.**

Les forfaits du site de serrurerie n'ont pas été transposés : ouvrir une porte
et hydrocurer un collecteur n'ont ni le même matériel, ni la même durée, ni la
même assurance. Tant que les valeurs restent entre crochets, la page `/tarifs`
explique les facteurs de prix et renvoie au devis, sans chiffre inventé.

---

## Formulaire de demande

| Clé | Rôle |
|---|---|
| `EMAIL_DEVIS` | Adresse qui **reçoit** les demandes. |
| `EMAIL_EXPEDITEUR` | Adresse qui **envoie** le message. Doit appartenir au domaine du site (SPF/DKIM), sinon le message part en indésirable. |
| `DEVIS_PHOTO_MAX_MO` | Poids maximal d'une photo jointe, en mégaoctets. |

Créez `EMAIL_EXPEDITEUR` dans hPanel avant la mise en ligne.

---

## Mesure d'audience et Google

| Clé | Valeur attendue | Effet si vide |
|---|---|---|
| `GA4_ID` | `G-XXXXXXXXXX` | aucun script tiers, aucun cookie, aucun bandeau |
| `GTM_ID` | `GTM-XXXXXXX` | idem. N'utilisez pas GA4 et GTM ensemble : le comptage serait double. |
| `GSC_CODE` | contenu de l'attribut `content` fourni par Search Console | aucune balise écrite |

Dès qu'un identifiant est renseigné, le bandeau de consentement apparaît et
rien n'est chargé avant acceptation explicite. C'est le comportement attendu
par la CNIL pour les cookies de mesure d'audience Google.

Pour Search Console, la vérification par fichier HTML ou par DNS est préférable
à la balise : elle ne pèse rien sur les pages.

---

## Réseaux sociaux

| Clé | Rôle |
|---|---|
| `URL_GOOGLE_BUSINESS`, `URL_FACEBOOK`, `URL_LINKEDIN` | Alimentent le champ `sameAs` des données structurées. |

Ne renseignez que les profils qui **existent réellement** : Google recoupe ces
liens, et un profil inexistant dégrade la confiance accordée à l'ensemble du
balisage.

---

## Indexation

| Clé | Valeur | Effet |
|---|---|---|
| `ROBOTS_POLICY` | `index` | `<meta name="robots" content="index, follow, …">` sur chaque page, `robots.txt` autorisant l'exploration et déclarant le sitemap. |
| | `noindex` | `noindex` sur chaque page **et** `robots.txt` en `Disallow: /`. |

Les deux ne peuvent pas diverger : c'est la même variable qui pilote la balise
et le fichier. `scripts/check-seo.sh` vérifie en outre qu'aucune page en
`noindex` ne figure au sitemap — une consigne contradictoire que Search Console
signalerait.

**En production, la valeur attendue est `index`.** Passez-la à `noindex`
uniquement pour une préproduction ou une recette.

Certaines pages forcent leur propre valeur par la clé `robots:` de leur bloc de
métadonnées : `404.html` et `merci.html` sont en `noindex` et hors sitemap, ce
qui est voulu.

---

## Ce qui n'est pas dans `config.sh`

* Le **contenu** des pages : dans `src/pages/`.
* Le **menu** et le **pied de page** : dans `src/partials/`.
* Les **redirections 301** : dans `static/.htaccess`, doublées dans
  `scripts/routeur-local.php` pour que l'aperçu local se comporte comme la
  production.
* Les **couleurs et la mise en page** : dans `static/assets/css/style.css`.
* Le **logo** : remplacez `logo-source/logo-original.webp` puis relancez
  `python3 scripts/preparer-logo.py`. Le script en tire le logo de l'en-tête,
  sa variante claire pour le pied de page, le favicon et les icônes
  d'application — il n'y a rien d'autre à changer.
