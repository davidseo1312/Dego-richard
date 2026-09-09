#!/usr/bin/env python3
"""
Transforme les six pages départementales en pages d'atterrissage locales.

    python3 scripts/landing-departements.py

Ce que le script ajoute à une page existante, sans rien lui retirer :

  1. un bloc « ce pour quoi on nous appelle » juste sous le héros, pour que le
     visiteur reconnaisse SA situation avant de lire quoi que ce soit ;
  2. deux cas de figure détaillés — problème, diagnostic, méthode, résultat —
     illustrés par une photographie différente d'un département à l'autre ;
  3. une liste de communes lisible, préfectures et sous-préfectures en tête ;
  4. l'emplacement des avis clients, encore vide faute d'avis vérifiés ;
  5. cinq appels à l'action de formes différentes, répartis dans la page.

Sur le clonage
--------------
Ces six pages partagent une ARCHITECTURE, pas un CONTENU. Tout ce qui est
écrit ici — symptômes, cas de figure, formulation des appels à l'action — est
propre à un département et renvoie à ce que la page dit déjà de son
territoire. Un texte qui ne tiendrait que par la substitution d'un nom de
département n'aurait aucune raison d'exister.

Sur les cas de figure
---------------------
Ils décrivent une SÉQUENCE DE TRAVAIL, pas un chantier passé : ni date, ni
adresse, ni client, ni résultat chiffré. Tant qu'aucune intervention
documentée et vérifiable n'est fournie, rien ici ne prétend en être une. Le
jour où de vrais dossiers arrivent, le même balisage les accueille.

Idempotent : relancer le script sur une page déjà traitée ne fait rien.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGES = RACINE / "src" / "pages" / "departements"

TEL = '{{TELEPHONE}}'
TELE164 = '{{TELEPHONE_E164}}'

DEPARTEMENTS = {
    # ------------------------------------------------------------------ 22 --
    "cotes-d-armor": {
        "code": "22",
        "nom": "Côtes-d'Armor",
        "dans": "dans les Côtes-d'Armor",
        "zone": "22",
        "problemes": [
            ("WC bouché", "L'eau monte dans la cuvette et redescend lentement, ou pas du tout."),
            ("Évier de cuisine", "Les graisses se figent d'autant plus vite que l'eau du réseau est froide."),
            ("Douche et baignoire", "Le receveur met plusieurs minutes à se vider après chaque passage."),
            ("Regard extérieur en charge", "Le regard reste plein entre deux utilisations : le bouchon est en aval."),
            ("Racines de haie bocagère", "Talus et haies plantés au ras du réseau : les racines entrent par les joints."),
            ("Canalisation en grès", "Bourgs anciens : joints creusés, emboîtements décalés, dépôts qui s'accrochent."),
            ("Fosse toutes eaux", "Argoat : préfiltre colmaté, boues remontées, épandage qui ne draine plus."),
            ("Odeurs persistantes", "Siphon désamorcé ou ventilation primaire obstruée après une longue absence."),
        ],
        "cas": [
            {
                "photo": "WC",
                "titre": "WC bouché en maison raccordée à une fosse toutes eaux",
                "lieu": "Cas de figure — habitat individuel de l'Argoat",
                "probleme": "Le WC refoule et l'évacuation de la salle d'eau ralentit en même temps. "
                            "Deux appareils touchés : le bouchon n'est pas dans la cuvette.",
                "diagnostic": "Ouverture du regard de visite en amont de la fosse. S'il est plein, "
                              "la cause est en aval — préfiltre, fosse ou épandage — et non dans "
                              "l'appareil sanitaire.",
                "methode": "Débouchage mécanique de la conduite d'amenée, puis contrôle du niveau "
                           "dans la fosse. Selon l'état constaté, vidange et nettoyage du préfiltre.",
                "resultat": "L'écoulement redevient franc sur les deux appareils. Le compte rendu "
                            "indique si la fosse doit être suivie, et à quelle échéance.",
            },
            {
                "photo": "COLLECTIF",
                "titre": "Colonne d'immeuble encrassée dans l'agglomération briochine",
                "lieu": "Cas de figure — copropriété",
                "probleme": "Plusieurs logements d'une même colonne signalent un ralentissement "
                            "dans la même semaine. Le débouchage appartement par appartement ne "
                            "tient pas plus de quelques jours.",
                "diagnostic": "Inspection vidéo depuis le pied de colonne. Une paroi rugueuse et "
                              "un diamètre utile réduit désignent un encrassement de colonne, pas "
                              "un bouchon d'appareil.",
                "methode": "Hydrocurage à pression maîtrisée sur toute la hauteur, depuis le pied "
                           "de colonne. Le furet perce ; seule la pression décolle le dépôt.",
                "resultat": "Le diamètre utile est rétabli pour l'ensemble de la colonne. "
                            "L'intervention se traite avec le syndic, pas logement par logement.",
            },
        ],
        "principales": ["saint-brieuc", "lannion", "dinan"],
        "cta3_titre": "Une évacuation qui ne suit plus dans les Côtes-d'Armor&nbsp;?",
        "cta3_texte": "Décrivez le symptôme et votre commune : entre la baie, le Trégor et "
                      "l'Argoat, le délai réel n'est pas le même.",
        "cta2_titre": "Vous ne savez pas de quelle prestation vous relevez&nbsp;?",
        "cta2_texte": "C'est normal, et ce n'est pas à vous de le déterminer. Décrivez ce que "
                      "vous constatez, nous identifions la nature du problème.",
    },
    # ------------------------------------------------------------------ 29 --
    "finistere": {
        "code": "29",
        "nom": "Finistère",
        "dans": "dans le Finistère",
        "zone": "29",
        "problemes": [
            ("Colonne en fonte", "Centre de Brest : paroi piquée par la corrosion, dépôt qui s'accroche."),
            ("Bac à graisses saturé", "Restauration littorale : au-delà du quart de la hauteur utile, il ne retient plus."),
            ("Réseau en surcharge estivale", "Campings et hébergements : la section utile ne suit plus le pic de juillet."),
            ("WC bouché", "Le symptôme le plus courant, en location saisonnière comme à l'année."),
            ("Douche qui refoule", "L'eau remonte dans le receveur quand un autre appareil s'écoule."),
            ("Tampon de regard grippé", "Air marin : les ferrures se soudent par la corrosion."),
            ("Fosse et épandage", "Centre-Finistère : sols sur schiste, peu perméables, sensibles à la surcharge."),
            ("Extension mal raccordée", "Véranda ou salle d'eau ajoutée avec une pente insuffisante."),
        ],
        "cas": [
            {
                "photo": "CUISINE",
                "titre": "Cuisine de restaurant : évacuation qui ralentit en pleine saison",
                "lieu": "Cas de figure — établissement de bord de mer",
                "probleme": "L'évacuation du bac de plonge met de plus en plus de temps, et une "
                            "odeur apparaît en fin de service. Le service ne peut pas s'arrêter.",
                "diagnostic": "Contrôle de l'écoulement appareil par appareil, puis ouverture du "
                              "bac à graisses. L'épaisseur de la couche renseigne mieux que le "
                              "calendrier de vidange.",
                "methode": "Pompage du bac, nettoyage des parois et du panier, puis curage de la "
                           "conduite entre la plonge et le bac si le dépôt s'y est étendu.",
                "resultat": "L'écoulement retrouve son débit et l'odeur disparaît. Le premier "
                            "passage permet de caler le rythme de vidange sur le volume réel de couverts.",
            },
            {
                "photo": "DOUCHE",
                "titre": "Douche d'hébergement saisonnier qui ne se vide plus",
                "lieu": "Cas de figure — location de vacances en Cornouaille",
                "probleme": "Le receveur garde l'eau et déborde légèrement à chaque usage. "
                            "Le logement est occupé : l'intervention doit être courte et propre.",
                "diagnostic": "Dépose de la grille et contrôle de la bonde siphoïde. Si le siphon "
                              "est libre, la cause est plus loin — collecteur de l'étage ou "
                              "réseau saturé par l'affluence.",
                "methode": "Aspiration de l'eau stagnante pour travailler à sec, nettoyage de la "
                           "bonde, puis furet sur le collecteur si le siphon seul ne suffit pas.",
                "resultat": "Le receveur se vide franchement. Quand le réseau est en cause, un "
                            "curage hors saison est proposé plutôt qu'un dépannage répété en août.",
            },
        ],
        "principales": ["brest", "quimper", "morlaix"],
        "cta3_titre": "Un écoulement bloqué dans le Finistère&nbsp;?",
        "cta3_texte": "De Brest au Cap Sizun, le délai dépend beaucoup du secteur et de la "
                      "saison. Précisez votre commune, nous annonçons un créneau réaliste.",
        "cta2_titre": "Particulier, camping, restaurant ou copropriété&nbsp;?",
        "cta2_texte": "Le matériel et l'organisation ne sont pas les mêmes. Dites-nous le "
                      "contexte, nous adaptons l'intervention.",
    },
    # ------------------------------------------------------------------ 35 --
    "ille-et-vilaine": {
        "code": "35",
        "nom": "Ille-et-Vilaine",
        "dans": "en Ille-et-Vilaine",
        "zone": "35",
        "problemes": [
            ("Lingettes en colonne", "Rennes : la cause la plus fréquente des bouchons de chute en collectif."),
            ("Studio étudiant", "Lavabo et douche encrassés par les cheveux et le savon, sans entretien du siphon."),
            ("WC bouché", "Chute commune : le refoulement se manifeste souvent à l'étage le plus bas."),
            ("Évier de cuisine", "Graisses figées dans le siphon, aggravées par une eau calcaire."),
            ("Tartre sur les évacuations", "Est du département : le dépôt calcaire réduit lentement la section."),
            ("Refoulement en secteur bas", "Redon et vallées : le réseau se met en charge lors des épisodes pluvieux."),
            ("Canalisation extérieure", "Racines et affaissements sur les raccordements de maison individuelle."),
            ("Odeurs en logement fermé", "Siphons désamorcés dans un logement laissé vide plusieurs semaines."),
        ],
        "cas": [
            {
                "photo": "COLLECTIF",
                "titre": "Chute commune bouchée par des lingettes",
                "lieu": "Cas de figure — immeuble rennais",
                "probleme": "Les WC des étages bas refoulent alors que ceux du haut fonctionnent. "
                            "Signe classique d'un bouchon dans la chute, pas dans un appareil.",
                "diagnostic": "Inspection vidéo depuis le regard de pied d'immeuble. Un amas "
                              "fibreux compacté se distingue immédiatement d'un dépôt graisseux : "
                              "il ne se dilue pas.",
                "methode": "Débouchage mécanique pour rétablir un passage, puis hydrocurage pour "
                           "retirer l'amas au lieu de le repousser plus bas dans le réseau.",
                "resultat": "L'écoulement redevient normal à tous les étages. Un affichage dans "
                            "les parties communes évite la récidive mieux que n'importe quel outil.",
            },
            {
                "photo": "SIPHON",
                "titre": "Lavabo de studio qui ne s'écoule plus",
                "lieu": "Cas de figure — parc locatif étudiant",
                "probleme": "L'eau stagne dans la vasque et met plusieurs minutes à descendre. "
                            "Le logement change d'occupant chaque année, le siphon n'a jamais été ouvert.",
                "diagnostic": "Contrôle visuel sous la vasque. Un culot de siphon plein de cheveux "
                              "agglomérés au savon se voit dès la dépose : inutile d'aller plus loin.",
                "methode": "Démontage du siphon, nettoyage complet du culot et du joint, "
                           "remontage avec contrôle d'étanchéité en eau.",
                "resultat": "L'écoulement est rétabli sans produit ni démontage de mobilier. "
                            "L'opération se refait en dix minutes à chaque changement de locataire.",
            },
        ],
        "principales": ["rennes", "saint-malo", "fougeres"],
        "cta3_titre": "Une évacuation bouchée en Ille-et-Vilaine&nbsp;?",
        "cta3_texte": "Précisez s'il s'agit d'un logement individuel ou d'un immeuble : "
                      "en collectif, l'intervention se traite avec le syndic ou le bailleur.",
        "cta2_titre": "Locataire, propriétaire, bailleur ou syndic&nbsp;?",
        "cta2_texte": "Dites-nous à quel titre vous appelez : cela détermine qui reçoit le devis "
                      "et qui donne l'accord avant l'intervention.",
    },
    # ------------------------------------------------------------------ 56 --
    "morbihan": {
        "code": "56",
        "nom": "Morbihan",
        "dans": "dans le Morbihan",
        "zone": "56",
        "problemes": [
            ("Remise en eau de résidence", "Odeurs et écoulement lent au retour, après des mois de fermeture."),
            ("Douche qui ne se vide plus", "Bonde siphoïde obstruée par les cheveux et le sable rapporté de la plage."),
            ("WC bouché", "Premier appareil touché lors d'une reprise d'usage après une longue absence."),
            ("Évier de cuisine", "Graisses figées, souvent après une période d'occupation intensive."),
            ("Réseau en surcharge estivale", "Golfe et presqu'îles : la population double, le réseau ne change pas."),
            ("Fosse en zone dispersée", "Intérieur du département : préfiltre colmaté, épandage saturé."),
            ("Regard extérieur", "Regard de visite en charge sur un raccordement de maison individuelle."),
            ("Siphon désamorcé", "Garde d'eau évaporée dans un logement inoccupé : l'odeur remonte du réseau."),
        ],
        "cas": [
            {
                "photo": "REGARD",
                "titre": "Remise en service d'une résidence secondaire",
                "lieu": "Cas de figure — littoral morbihannais",
                "probleme": "Au retour, l'eau s'écoule mal sur plusieurs appareils et une odeur "
                            "d'égout est présente dans toute la maison. Rien ne fonctionnait "
                            "depuis l'automne.",
                "diagnostic": "Ouverture du regard de visite en limite de propriété. Un regard "
                              "plein oriente vers le réseau extérieur ; un regard vide renvoie la "
                              "cause à l'intérieur, siphons compris.",
                "methode": "Inspection vidéo de la conduite depuis le regard, puis curage du "
                           "tronçon obstrué. Remise en eau de tous les siphons, ventilation "
                           "primaire contrôlée.",
                "resultat": "L'écoulement et la garde d'eau sont rétablis. Le compte rendu "
                            "indique ce qu'il faut faire avant la prochaine fermeture pour ne pas "
                            "recommencer.",
            },
            {
                "photo": "CUISINE",
                "titre": "Évier de cuisine bloqué après une période d'affluence",
                "lieu": "Cas de figure — location de vacances",
                "probleme": "L'évier ne se vide plus entre deux locations. Le créneau de ménage "
                            "est court : l'intervention doit tenir dans la journée de rotation.",
                "diagnostic": "Contrôle de l'écoulement robinet ouvert, puis dépose du siphon. "
                              "Un bouchon graisseux au-delà du siphon ne se voit qu'au furet.",
                "methode": "Nettoyage du siphon, puis furet sur la dérivation. Curage court si le "
                           "dépôt s'étend sur la conduite plutôt que de se concentrer en un point.",
                "resultat": "L'évier se vide à plein débit avant l'arrivée suivante. Un rappel "
                            "écrit sur les graisses est laissé pour les occupants.",
            },
        ],
        "principales": ["lorient", "vannes", "pontivy"],
        "cta3_titre": "Un problème d'écoulement dans le Morbihan&nbsp;?",
        "cta3_texte": "Résidence principale, maison de vacances ou location : dites-nous si le "
                      "logement est occupé, cela change l'organisation de l'intervention.",
        "cta2_titre": "Vous ouvrez une maison restée fermée&nbsp;?",
        "cta2_texte": "C'est le moment où presque tout se déclare d'un coup. Décrivez ce que "
                      "vous constatez, nous dirons ce qui relève d'un dépannage et ce qui relève "
                      "d'un entretien.",
    },
    # ------------------------------------------------------------------ 44 --
    "loire-atlantique": {
        "code": "44",
        "nom": "Loire-Atlantique",
        "dans": "en Loire-Atlantique",
        "zone": "44",
        "problemes": [
            ("Poste de relevage en défaut", "Sous-sol ou cave : la pompe s'arrête, le niveau monte."),
            ("Refoulement en secteur bas", "Estuaire, Brière, marais : le réseau se met en charge et l'écoulement s'inverse."),
            ("WC bouché", "Le symptôme le plus courant, en appartement comme en maison."),
            ("Évier de cuisine", "Graisses figées dans le siphon ou la dérivation."),
            ("Colonne d'immeuble", "Nantes : réseaux de plusieurs générations sur un même bâtiment."),
            ("Cave inondée", "Eaux usées qui remontent par le sol quand le réseau est saturé."),
            ("Réseau saisonnier", "Côte de Jade : forte variation d'occupation entre l'hiver et l'été."),
            ("Canalisation extérieure", "Racines et affaissements sur les raccordements de pavillon."),
        ],
        "cas": [
            {
                "photo": "COLLECTIF",
                "titre": "Poste de relevage arrêté dans un sous-sol",
                "lieu": "Cas de figure — immeuble avec niveau enterré",
                "probleme": "Le niveau monte dans la cuve et les évacuations du niveau bas "
                            "refoulent. Tant que la pompe ne repart pas, rien ne s'évacue.",
                "diagnostic": "Contrôle du flotteur, du clapet anti-retour et de l'état de la "
                              "cuve. Une pompe arrêtée par un chiffon dans la roue ne se distingue "
                              "d'une panne électrique qu'à l'ouverture.",
                "methode": "Pompage de la cuve pour travailler au sec, dégagement de la roue et "
                           "nettoyage des parois, puis essai en charge avant de refermer.",
                "resultat": "Le poste repart et les évacuations du niveau bas suivent. Ce qui a "
                            "bloqué la roue est montré et consigné : c'est ce qui évite la récidive.",
            },
            {
                "photo": "URGENCE",
                "titre": "Refoulement dans une maison de secteur bas",
                "lieu": "Cas de figure — vallée ou zone de marais",
                "probleme": "L'eau remonte par la douche et le WC pendant un épisode pluvieux. "
                            "Le phénomène cesse en partie quand la pluie s'arrête.",
                "diagnostic": "Vérification de la concomitance avec la pluie, puis contrôle du "
                              "regard et du clapet anti-retour s'il en existe un. Un réseau en "
                              "charge et un bouchon ne se traitent pas de la même façon.",
                "methode": "Aspiration de l'eau répandue, mise hors d'eau des pièces touchées, "
                           "puis curage du raccordement. Le clapet anti-retour est contrôlé, et "
                           "signalé s'il manque.",
                "resultat": "L'écoulement est rétabli et les pièces sont assainies. Quand le "
                            "réseau public est en cause, le constat écrit sert de base auprès du "
                            "gestionnaire.",
            },
        ],
        "principales": ["nantes", "saint-nazaire", "reze"],
        "cta3_titre": "Refoulement ou canalisation bouchée en Loire-Atlantique&nbsp;?",
        "cta3_texte": "Précisez si de l'eau est déjà répandue : cela change complètement "
                      "l'ordre des opérations à l'arrivée.",
        "cta2_titre": "Maison, appartement, cave ou local professionnel&nbsp;?",
        "cta2_texte": "Un niveau enterré ne se traite pas comme un rez-de-chaussée. Décrivez "
                      "les lieux, nous prévoyons le matériel en conséquence.",
    },
    # ------------------------------------------------------------------ 49 --
    "maine-et-loire": {
        "code": "49",
        "nom": "Maine-et-Loire",
        "dans": "en Maine-et-Loire",
        "zone": "49",
        "problemes": [
            ("Tartre sur les évacuations", "Eau dure : le dépôt calcaire réduit lentement la section utile."),
            ("Évier de cuisine", "Graisses et calcaire se combinent en un dépôt particulièrement dur."),
            ("WC bouché", "Cuvette entartrée : la section du siphon intégré diminue avec les années."),
            ("Lavabo et douche", "Cheveux, savon et calcaire agglomérés dans le culot du siphon."),
            ("Centre ancien", "Angers, Saumur : réseaux anciens, emboîtements décalés, joints creusés."),
            ("Caves et troglodytes", "Saumurois : niveaux enterrés et évacuations relevées."),
            ("Rejets agroalimentaires", "Choletais et Mauges : eaux chargées, bacs à graisses très sollicités."),
            ("Canalisation extérieure", "Racines et affaissements sur les raccordements de maison."),
        ],
        "cas": [
            {
                "photo": "EVIER",
                "titre": "Évacuation entartrée qui se rebouche tous les deux mois",
                "lieu": "Cas de figure — logement alimenté en eau dure",
                "probleme": "L'évier se rebouche régulièrement malgré des nettoyages de siphon "
                            "répétés. Le débouchage tient quelques semaines, jamais plus.",
                "diagnostic": "Inspection de la dérivation. Une section réduite sur toute la "
                              "longueur, et non un bouchon localisé, signe un dépôt calcaire "
                              "combiné aux graisses.",
                "methode": "Curage de la dérivation sur toute sa longueur plutôt que perçage du "
                           "point le plus dur : un dépôt réparti ne se traite pas en un point.",
                "resultat": "Le débit initial est rétabli et l'intervalle entre incidents "
                            "s'allonge nettement. Un entretien annuel est proposé, sans obligation.",
            },
            {
                "photo": "WC",
                "titre": "WC bouché dans un immeuble de centre ancien",
                "lieu": "Cas de figure — centre-ville angevin",
                "probleme": "La cuvette se vide très lentement depuis plusieurs semaines, "
                            "puis refoule. Le bâtiment est ancien, la chute d'origine.",
                "diagnostic": "Caméra dans la cuvette pour situer le bouchon : siphon intégré, "
                              "raccordement, ou chute. La distance parcourue avant l'obstacle "
                              "suffit à trancher.",
                "methode": "Furet à tête adaptée lorsque le bouchon est proche ; hydrocurage "
                           "depuis le regard de pied lorsque c'est la chute qui est encrassée. "
                           "La cuvette n'est déposée qu'en dernier recours.",
                "resultat": "L'évacuation retrouve un écoulement franc. L'état de la chute est "
                            "documenté, ce qui permet à la copropriété de décider en connaissance "
                            "de cause.",
            },
        ],
        "principales": ["angers", "cholet", "saumur"],
        "cta3_titre": "Une canalisation bouchée en Maine-et-Loire&nbsp;?",
        "cta3_texte": "Si le problème revient régulièrement, dites-le : un incident qui se "
                      "répète ne se traite pas comme un incident isolé.",
        "cta2_titre": "Le problème revient-il régulièrement&nbsp;?",
        "cta2_texte": "Un bouchon qui réapparaît tous les deux mois n'est pas un bouchon : "
                      "c'est un réseau qui a perdu de la section. Le traitement est différent.",
    },
}

BOUTON_APPEL = (f'<a class="btn btn-call btn-large" href="tel:{TELE164}" '
                'data-track="appel" data-track-zone="%s">' + TEL + '</a>')
BOUTON_DEVIS = ('<a class="btn btn-devis btn-large" href="/devis" '
                'data-track="clic_devis" data-track-zone="%s">Demander une intervention</a>')
BOUTON_GHOST = ('<a class="btn btn-ghost btn-large" href="/devis" '
                'data-track="clic_devis" data-track-zone="%s">%s</a>')


def bloc_problemes(d: dict) -> str:
    items = "\n".join(
        f"      <li><strong>{t}</strong>{txt}</li>" for t, txt in d["problemes"])
    return f'''
<section class="alt">
  <div class="wrap">
    <div class="section-titre">
      <p class="sur-titre">Ce que l'on nous signale</p>
      <h2>Les situations pour lesquelles on nous appelle {d["dans"]}</h2>
      <p>
        Reconnaissez la vôtre : le symptôme oriente le diagnostic bien plus
        sûrement que le nom donné au problème.
      </p>
    </div>

    <ul class="problemes">
{items}
    </ul>
  </div>
</section>
'''


def bloc_cas(d: dict) -> str:
    blocs = []
    for i, c in enumerate(d["cas"]):
        inverse = " inverse" if i % 2 else ""
        blocs.append(f'''    <div class="cas{inverse}" data-reveal>
      <figure class="cas-visuel">
        {{{{PHOTO_{c["photo"]}_CARTE}}}}
        <figcaption>{{{{PHOTO_{c["photo"]}_LEGENDE}}}}.</figcaption>
      </figure>
      <div class="cas-corps">
        <p class="cas-lieu">{c["lieu"]}</p>
        <h3>{c["titre"]}</h3>
        <ul class="cas-etapes">
          <li><span class="cle-cas">Problème</span>{c["probleme"]}</li>
          <li><span class="cle-cas">Diagnostic</span>{c["diagnostic"]}</li>
          <li><span class="cle-cas">Méthode</span>{c["methode"]}</li>
          <li><span class="cle-cas">Résultat</span>{c["resultat"]}</li>
        </ul>
      </div>
    </div>''')
    corps = "\n\n".join(blocs)
    zone = f'cta3-{d["zone"]}'
    return f'''
<section>
  <div class="wrap">
    <div class="section-titre">
      <p class="sur-titre">Comment nous procédons</p>
      <h2>Deux situations courantes {d["dans"]}, du symptôme au résultat</h2>
      <p>
        Ces deux cas décrivent la séquence de travail — ce que l'on constate, ce
        que l'on cherche, l'outil retenu et ce qui est rétabli. Ce ne sont pas des
        chantiers datés : aucune intervention passée n'est présentée ici tant
        qu'elle n'est pas documentée et vérifiable.
      </p>
    </div>

{corps}

    <div class="cta-plein" style="margin-top:var(--e-7)">
      <h2>{d["cta3_titre"]}</h2>
      <p>{d["cta3_texte"]}</p>
      <div class="cta-actions">
        {BOUTON_APPEL % zone}
        <a class="btn btn-ghost btn-large" href="/devis" data-track="clic_devis" data-track-zone="{zone}">Demander une intervention</a>
      </div>
    </div>
  </div>
</section>
'''


def bloc_cta2(d: dict) -> str:
    zone = f'cta2-{d["zone"]}'
    return f'''
    <div class="cta-clair" style="margin-top:var(--e-7)">
      <div>
        <h2>{d["cta2_titre"]}</h2>
        <p>{d["cta2_texte"]}</p>
      </div>
      <div class="cta-actions">
        {BOUTON_DEVIS % zone}
        <a class="btn btn-ghost btn-large" href="tel:{TELE164}" data-track="appel" data-track-zone="{zone}">{TEL}</a>
      </div>
    </div>
'''


def bloc_cta4(d: dict) -> str:
    zone = f'cta4-{d["zone"]}'
    return f'''
<section>
  <div class="wrap">
    <div class="cta-clair">
      <div>
        <h2>Parler à quelqu'un plutôt que remplir un formulaire</h2>
        <p>
          Pour une évacuation déjà bloquée, l'appel reste le moyen le plus court :
          quelques questions suffisent à savoir quel matériel emporter.
        </p>
      </div>
      <div class="cta-actions">
        <a class="btn btn-call btn-large" href="tel:{TELE164}" data-track="appel" data-track-zone="{zone}">Appeler maintenant</a>
      </div>
    </div>
  </div>
</section>
'''


def villes(d: dict, liens: list) -> str:
    """Liste de communes, préfecture et sous-préfectures en tête."""
    principales = [l for l in liens if l[0].rsplit("/", 1)[1].replace("degorgement-", "")
                   in d["principales"]]
    autres = [l for l in liens if l not in principales]
    ordre = sorted(principales, key=lambda l: d["principales"].index(
        l[0].rsplit("/", 1)[1].replace("degorgement-", ""))) + autres
    items = []
    for href, nom in ordre:
        cls = ' class="principale"' if (href, nom) in principales else ""
        items.append(f'      <li{cls}><a href="{href}">{nom}</a></li>')
    return "\n".join(items)


def transformer(slug: str) -> str:
    d = DEPARTEMENTS[slug]
    f = PAGES / f"{slug}.html"
    s = f.read_text(encoding="utf-8")
    if 'class="problemes"' in s:
        return f"{slug} : déjà traité"

    # 1. Bloc « problèmes » juste après le héros.
    fin_hero = s.index("</section>\n", s.index('class="hero hero-interieur"')) + len("</section>\n")
    s = s[:fin_hero] + bloc_problemes(d) + s[fin_hero:]

    # 2. Séparer la section « prestations + communes » en deux sections : les
    #    prestations gardent le fond bleuté, les communes reçoivent le leur.
    marque = '    <h2 style="margin-top:2.2rem">Communes avec une page dédiée</h2>\n'
    i = s.index(marque)
    liens = re.findall(r'<li><a href="(/degorgement-[a-z-]+)">([^<]+)</a></li>',
                       s[i:s.index("</ul>", i)])
    fin_villes = s.index("</section>", i)
    reste_villes = s[s.index("</ul>", i) + len("</ul>\n"):fin_villes]

    s = (s[:i]
         + bloc_cta2(d)
         + "  </div>\n</section>\n"
         + bloc_cas(d)
         + f'''
<section class="alt">
  <div class="wrap">
    <div class="section-titre">
      <p class="sur-titre">Communes</p>
      <h2>Où nous intervenons {d["dans"]}</h2>
      <p>
        Les communes ci-dessous disposent d'une page dédiée. Le département est
        couvert en entier : l'absence d'une commune dans cette liste ne signifie
        pas que nous n'y intervenons pas.
      </p>
    </div>

    <ul class="villes-liste">
{villes(d, liens)}
    </ul>
'''
         + reste_villes.replace('<p style="margin-top:1rem">', '<p class="villes-autres">')
         + s[fin_villes:])

    # 3. Avis puis appel direct, avant la FAQ.
    marque_faq = s.index("<section>\n  <div class=\"wrap\">\n    <h2>Questions fréquentes")
    s = s[:marque_faq] + "{{SECTION_AVIS}}\n" + bloc_cta4(d) + s[marque_faq:]

    # 4. La FAQ passe sur fond bleuté : elle suit désormais une section blanche.
    s = s.replace('<section>\n  <div class="wrap">\n    <h2>Questions fréquentes',
                  '<section class="alt">\n  <div class="wrap">\n    <h2>Questions fréquentes', 1)

    # 5. Dernier appel à l'action : un devis, pas un appel de plus.
    s = re.sub(r'<a class="btn btn-ghost btn-large" href="/devis"([^>]*)>Demander un devis</a>',
               r'<a class="btn btn-ghost btn-large" href="/devis"\1>Obtenir un devis</a>', s)

    f.write_text(s, encoding="utf-8")
    return f"{slug} ({d['code']}) : 5 CTA, {len(d['problemes'])} symptômes, " \
           f"{len(d['cas'])} cas, {len(liens)} communes"


if __name__ == "__main__":
    for slug in DEPARTEMENTS:
        print("  ✓", transformer(slug))
    sys.exit(0)
