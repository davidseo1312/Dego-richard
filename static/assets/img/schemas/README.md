# Bibliothèque de visuels

Fichiers produits par `scripts/generer-visuels.py`. **Ne pas les retoucher
à la main** : le script est la source, une retouche serait perdue au
prochain rendu.

## Origine et licence

Ces images sont des **illustrations originales**, décrites en SVG dans le
script puis rendues en WebP par Chromium. Elles ne proviennent d'aucune
banque d'images : aucun filigrane, aucun logo tiers, aucune licence à
respecter au-delà de celle du dépôt.

Deux familles seulement, pour que l'ensemble se tienne :

1. **la coupe technique** — le réseau vu en section, comme sur un plan
   d'exécution (terrain, ouvrage, canalisation, pente, annotations) ;
2. **l'intérieur de canalisation** — la vue du moniteur d'inspection,
   avec point de fuite calculé et lame d'eau suivant la perspective.

## Remplacer une illustration par une photographie

Déposer un fichier WebP de **mêmes nom et dimensions** dans ce dossier
suffit : le HTML référence les fichiers par leur nom et porte déjà
`width`, `height`, `loading`, `decoding` et `alt`. Vérifier seulement que
la photographie retenue est libre de droits pour un usage commercial et
que le texte alternatif la décrit toujours correctement.

## Contenu

| Fichier | Dimensions | Poids | Texte alternatif |
|---|---|---|---|
| `hero-debouchage-canalisation.webp` | 1120×840 | 38 Ko | Coupe d'un réseau d'assainissement domestique : canalisation enterrée reliant la maison au regard de visite, buse d'hydrocurage en action sur un bouchon |
| `materiel-degorgement.webp` | 960×720 | 24 Ko | Matériel professionnel de dégorgement : enrouleur haute pression, flexible et caméra d'inspection de canalisation |
| `debouchage-wc.webp` | 960×720 | 18 Ko | Coupe d'un WC montrant la garde d'eau du siphon et l'emplacement d'un bouchon |
| `debouchage-evier.webp` | 960×720 | 14 Ko | Coupe d'un évier et de son siphon en S obstrué par des graisses figées |
| `debouchage-douche.webp` | 960×720 | 14 Ko | Coupe d'un receveur de douche dont la bonde siphoïde est obstruée par des cheveux |
| `debouchage-baignoire.webp` | 960×720 | 12 Ko | Coupe d'une baignoire remplie d'eau stagnante et de son siphon de vidage |
| `debouchage-cuisine.webp` | 960×720 | 23 Ko | Coupe d'une installation de cuisine : évier, siphon et bac à graisses raccordés au réseau |
| `debouchage-canalisation.webp` | 1120×700 | 27 Ko | Coupe d'une canalisation enterrée obstruée, buse rotative haute pression progressant vers le bouchon |
| `inspection-camera-canalisation.webp` | 1120×700 | 24 Ko | Vue depuis l'intérieur d'une canalisation inspectée par caméra motorisée, paroi éclairée et lame d'eau au radier |
| `curage-canalisation.webp` | 1120×700 | 25 Ko | Vue depuis l'intérieur d'une canalisation en cours de curage haute pression, dépôt décollé de la paroi |
| `pompage-canalisation.webp` | 960×720 | 24 Ko | Coupe d'un regard de visite rempli, flexible d'aspiration plongé jusqu'au fond pour le pompage |
| `assainissement.webp` | 1120×700 | 25 Ko | Coupe d'une installation d'assainissement individuel : maison, fosse toutes eaux à deux compartiments, ventilation et départ vers l'épandage |
| `debouchage-professionnel.webp` | 960×720 | 28 Ko | Coupe d'une installation de cuisine professionnelle raccordée à un bac à graisses enterré |
| `canalisation-exterieure.webp` | 960×720 | 26 Ko | Coupe d'une canalisation extérieure enterrée traversée par des racines d'arbre, avec son regard de visite |
| `urgence-degorgement.webp` | 1120×700 | 20 Ko | Vue intérieure d'une canalisation en refoulement : conduite pleine et bouchon bloquant l'écoulement |
