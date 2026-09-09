/* ==========================================================================
   Dégorgement Richard — scripts du site.

   Aucune dépendance, aucun framework, aucune requête réseau au chargement.
   Le fichier reste sous 5 Ko afin de ne pas peser sur le temps d'affichage.

   Cinq responsabilités, et rien d'autre :
     1. le menu mobile ;
     2. les micro-interactions (en-tête collant, apparition au défilement) ;
     3. le consentement aux cookies de mesure d'audience ;
     4. le suivi des conversions, uniquement après consentement ;
     5. le confort du formulaire de devis.

   Tout le site fonctionne sans JavaScript : navigation, formulaire de devis,
   liens d'appel. Ce fichier n'ajoute que du confort et de la mesure.
   ========================================================================== */
(function () {
  'use strict';

  var racine = document.documentElement;

  /* --- 1. Menu mobile ----------------------------------------------------- */

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('nav-principal');
  var voile = null;
  var dernierFocus = null;

  function basculerMenu(ouvrir) {
    if (!toggle || !nav) { return; }

    nav.setAttribute('data-ouvert', String(ouvrir));
    toggle.setAttribute('aria-expanded', String(ouvrir));

    var libelle = toggle.querySelector('.visually-hidden');
    if (libelle) { libelle.textContent = ouvrir ? 'Fermer le menu' : 'Ouvrir le menu'; }

    // Le fond ne doit pas défiler derrière le tiroir : sur iOS, un fond qui
    // bouge donne l'impression que le menu a « sauté ».
    document.body.setAttribute('data-menu', ouvrir ? 'ouvert' : 'ferme');

    if (voile) { voile.setAttribute('data-visible', String(ouvrir)); }

    if (ouvrir) {
      dernierFocus = document.activeElement;
      var premier = nav.querySelector('a, button');
      if (premier) { premier.focus(); }
    } else if (dernierFocus) {
      dernierFocus.focus();
      dernierFocus = null;
    }
  }

  if (toggle && nav) {
    // Le voile est créé en JavaScript : sans script, le menu ne s'ouvre pas,
    // donc un voile inerte n'aurait rien à masquer.
    voile = document.createElement('div');
    voile.className = 'voile';
    voile.setAttribute('data-visible', 'false');
    voile.setAttribute('aria-hidden', 'true');
    document.body.appendChild(voile);
    voile.addEventListener('click', function () { basculerMenu(false); });

    toggle.addEventListener('click', function () {
      basculerMenu(nav.getAttribute('data-ouvert') !== 'true');
    });

    // Suivre un lien depuis le tiroir doit le refermer : sinon il reste
    // ouvert par-dessus la page d'arrivée lors d'un retour arrière.
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a') && nav.getAttribute('data-ouvert') === 'true') {
        basculerMenu(false);
      }
    });

    // Échap referme le menu : sans cela, le focus reste piégé au clavier.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.getAttribute('data-ouvert') === 'true') {
        basculerMenu(false);
      }
    });

    // Le tiroir n'existe qu'en dessous de 1080 px. Repasser au-dessus alors
    // qu'il est ouvert laisserait le corps de page bloqué en non-défilable.
    var large = window.matchMedia('(min-width: 1080px)');
    var surChangement = function (e) {
      if (e.matches && nav.getAttribute('data-ouvert') === 'true') { basculerMenu(false); }
    };
    if (large.addEventListener) { large.addEventListener('change', surChangement); }
    else if (large.addListener) { large.addListener(surChangement); }
  }

  /* --- 1 bis. Lien de navigation correspondant à la page courante ---------- */

  var chemin = location.pathname.replace(/\/$/, '') || '/';
  Array.prototype.forEach.call(
    document.querySelectorAll('.nav a[href]'),
    function (lien) {
      var href = lien.getAttribute('href').replace(/\/$/, '') || '/';
      if (href === chemin) { lien.setAttribute('aria-current', 'page'); }
    }
  );

  /* --- 1 ter. Micro-interactions ------------------------------------------
     Deux effets, tous deux purement décoratifs : une ombre sur l'en-tête dès
     que la page défile, et une apparition en fondu des blocs qui entrent dans
     le champ. Le contenu est visible sans JavaScript, et l'apparition est
     désactivée si le visiteur a demandé moins d'animations.
     ------------------------------------------------------------------------ */

  var entete = document.querySelector('.site-header');
  if (entete) {
    var majOmbre = function () {
      entete.classList.toggle('est-colle', window.scrollY > 8);
    };
    majOmbre();
    window.addEventListener('scroll', majOmbre, { passive: true });
  }

  var mouvementReduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var aReveler = document.querySelectorAll('[data-reveal]');

  function toutReveler() {
    Array.prototype.forEach.call(aReveler, function (el) { el.classList.add('est-visible'); });
  }

  // Filet de sécurité : passé trois secondes, tout est visible quoi qu'il
  // arrive. Un contenu commercial ne peut pas dépendre d'un observateur.
  setTimeout(toutReveler, 3000);

  if (mouvementReduit || !('IntersectionObserver' in window)) {
    toutReveler();
  } else if (aReveler.length) {
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (!entree.isIntersecting) { return; }
        entree.target.classList.add('est-visible');
        observateur.unobserve(entree.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    Array.prototype.forEach.call(aReveler, function (el, i) {
      // Un décalage très court entre éléments voisins évite l'effet « tout
      // arrive d'un bloc », sans jamais faire attendre le lecteur.
      el.style.transitionDelay = Math.min(i % 6, 5) * 55 + 'ms';
      observateur.observe(el);
    });
  }

  /* --- 1 quater. Carte des zones d'intervention ---------------------------
     Leaflet et les tuiles OpenStreetMap ne sont chargés qu'après un clic
     explicite. Les tuiles viennent d'un tiers, qui verrait sinon l'adresse IP
     de chaque visiteur sans que personne l'ait demandé ; et la bibliothèque
     pèse à elle seule plus lourd que le reste de la page. La liste des
     départements, elle, est dans le HTML dès le départ : c'est elle qui porte
     l'information, la carte ne fait que l'illustrer.
     ------------------------------------------------------------------------ */

  // Préfectures des six départements couverts. La couverture porte sur
  // l'ensemble de chaque département ; ces points ne sont que des repères.
  var PREFECTURES = [
    { nom: "Saint-Brieuc",  dep: "Côtes-d'Armor (22)",   url: '/departements/cotes-d-armor',     lat: 48.5136, lon: -2.7653 },
    { nom: 'Quimper',       dep: 'Finistère (29)',       url: '/departements/finistere',         lat: 47.9960, lon: -4.0970 },
    { nom: 'Rennes',        dep: 'Ille-et-Vilaine (35)', url: '/departements/ille-et-vilaine',   lat: 48.1173, lon: -1.6778 },
    { nom: 'Vannes',        dep: 'Morbihan (56)',        url: '/departements/morbihan',          lat: 47.6582, lon: -2.7608 },
    { nom: 'Nantes',        dep: 'Loire-Atlantique (44)', url: '/departements/loire-atlantique', lat: 47.2184, lon: -1.5536 },
    { nom: 'Angers',        dep: 'Maine-et-Loire (49)',  url: '/departements/maine-et-loire',    lat: 47.4784, lon: -0.5632 }
  ];

  var boutonCarte = document.querySelector('[data-carte-charger]');

  function chargerRessource(balise, attributs) {
    return new Promise(function (resoudre, rejeter) {
      var el = document.createElement(balise);
      Object.keys(attributs).forEach(function (k) { el[k] = attributs[k]; });
      el.onload = resoudre;
      el.onerror = function () { rejeter(new Error('chargement impossible')); };
      document.head.appendChild(el);
    });
  }

  function dessinerCarte() {
    var toile = document.getElementById('carte');
    if (!toile || !window.L) { return; }

    toile.innerHTML = '';
    toile.setAttribute('data-actif', 'true');

    var carte = L.map(toile, { scrollWheelZoom: false, attributionControl: true });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 12, minZoom: 6,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(carte);

    var points = [];
    PREFECTURES.forEach(function (p) {
      points.push([p.lat, p.lon]);
      L.circleMarker([p.lat, p.lon], {
        radius: 11, weight: 3,
        color: '#0369a1', fillColor: '#38bdf8', fillOpacity: 0.85
      }).addTo(carte).bindPopup(
        '<strong>' + p.dep + '</strong><br>Préfecture : ' + p.nom +
        '<br><a href="' + p.url + '">Voir la page du département</a>'
      // Étiquette permanente : la carte doit rester lisible sans cliquer,
      // et sans dépendre des tuiles — si elles ne chargent pas, les six
      // départements restent identifiables.
      ).bindTooltip(p.dep.replace(/ \(.*/, ''), {
        permanent: true, direction: 'right', offset: [10, 0],
        className: 'carte-etiquette'
      });
    });
    carte.fitBounds(points, { padding: [36, 36] });
  }

  if (boutonCarte) {
    boutonCarte.addEventListener('click', function () {
      boutonCarte.disabled = true;
      boutonCarte.textContent = 'Chargement…';
      Promise.all([
        chargerRessource('link', { rel: 'stylesheet', href: '/assets/vendor/leaflet/leaflet.css' }),
        chargerRessource('script', { src: '/assets/vendor/leaflet/leaflet.js', defer: true })
      ]).then(dessinerCarte).catch(function () {
        // Échec du chargement : la liste des départements reste affichée à
        // côté, le visiteur n'a donc rien perdu. On le dit plutôt que de
        // laisser un bouton inerte.
        boutonCarte.disabled = false;
        boutonCarte.textContent = 'Carte indisponible — réessayer';
      });
    });
  }

  /* --- 2. Année du copyright ---------------------------------------------- */

  var annee = document.getElementById('annee');
  if (annee) { annee.textContent = String(new Date().getFullYear()); }

  /* --- 3. Consentement et mesure d'audience -------------------------------
     La CNIL impose un consentement préalable pour les cookies de mesure
     d'audience Google. Aucun script tiers n'est chargé, et aucun événement
     n'est transmis, tant que le visiteur n'a pas accepté explicitement.

     Les identifiants viennent de src/config.sh (GA4_ID, GTM_ID) et sont
     déposés sur la balise <html> au build. Vides, tout ce bloc est inerte.
     ------------------------------------------------------------------------ */

  var GA_ID  = racine.getAttribute('data-ga')  || '';
  var GTM_ID = racine.getAttribute('data-gtm') || '';
  var MESURE_ACTIVE = Boolean(GA_ID || GTM_ID);
  var CLE = 'consentement-mesure-audience';

  var consentement = false;
  var fileAttente = [];   // événements survenus avant la réponse au bandeau

  function memoriser(valeur) {
    try { localStorage.setItem(CLE, valeur); } catch (e) { /* stockage indisponible */ }
  }

  function lireChoix() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }

  function chargerMesure() {
    if (window.__mesureChargee) { return; }
    window.__mesureChargee = true;

    window.dataLayer = window.dataLayer || [];

    if (GTM_ID) {
      window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
      injecter('https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(GTM_ID));
    }

    if (GA_ID) {
      injecter('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID));
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', GA_ID, { anonymize_ip: true });
    }
  }

  function injecter(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  /* Envoi d'un événement de conversion.
     Avant consentement, l'événement est mis de côté : s'il accepte ensuite,
     la conversion n'est pas perdue ; s'il refuse, la file est vidée sans
     jamais rien émettre. */
  function suivre(nom, parametres) {
    if (!MESURE_ACTIVE) { return; }
    if (!consentement) {
      if (fileAttente.length < 20) { fileAttente.push([nom, parametres]); }
      return;
    }
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: nom }, parametres || {}));
    if (typeof window.gtag === 'function') {
      window.gtag('event', nom, parametres || {});
    }
  }

  function accepter() {
    consentement = true;
    chargerMesure();
    fileAttente.forEach(function (e) { suivre(e[0], e[1]); });
    fileAttente = [];
  }

  var choix = lireChoix();
  if (choix === 'accepte') {
    accepter();
  } else if (choix !== 'refuse' && MESURE_ACTIVE) {
    afficherBandeau();
  }

  function afficherBandeau() {
    var bandeau = document.createElement('div');
    bandeau.className = 'cookie-bandeau';
    bandeau.setAttribute('role', 'dialog');
    bandeau.setAttribute('aria-label', 'Consentement aux cookies de mesure d’audience');
    bandeau.innerHTML =
      '<div class="cookie-inner">' +
        '<p>Nous utilisons un outil de mesure d’audience pour comprendre comment le site est consulté. ' +
        'Ces cookies ne sont déposés qu’avec votre accord et ne servent pas à de la publicité. ' +
        '<a href="/politique-confidentialite">En savoir plus</a></p>' +
        '<div class="cookie-actions">' +
          '<button type="button" class="btn btn-ghost" data-action="refuser">Refuser</button>' +
          '<button type="button" class="btn btn-call" data-action="accepter">Accepter</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(bandeau);

    bandeau.addEventListener('click', function (e) {
      var action = e.target.getAttribute('data-action');
      if (!action) { return; }
      if (action === 'accepter') {
        memoriser('accepte');
        accepter();
      } else {
        memoriser('refuse');
        fileAttente = [];
      }
      bandeau.remove();
    });
  }

  /* --- 4. Suivi des conversions -------------------------------------------
     Les éléments porteurs de data-track sont suivis sans code spécifique par
     page. La zone (en-tête, héros, barre mobile…) permet de savoir QUEL appel
     à l'action convertit, information décisive pour arbitrer la mise en page.
     ------------------------------------------------------------------------ */

  document.addEventListener('click', function (e) {
    var cible = e.target.closest('[data-track]');
    if (!cible) { return; }
    suivre(cible.getAttribute('data-track'), {
      zone: cible.getAttribute('data-track-zone') || 'inconnue',
      page: location.pathname
    });
  });

  // Les liens d'appel et de courriel sont suivis même sans data-track :
  // ce sont les deux conversions principales du site.
  document.addEventListener('click', function (e) {
    var lien = e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!lien || lien.hasAttribute('data-track')) { return; }
    suivre(lien.getAttribute('href').indexOf('tel:') === 0 ? 'appel' : 'clic_email', {
      zone: 'lien-texte',
      page: location.pathname
    });
  });

  // Conversion « devis envoyé » : signalée par la page de remerciement, donc
  // uniquement lorsque le serveur a réellement accepté et transmis la demande.
  if (document.body.getAttribute('data-conversion')) {
    suivre(document.body.getAttribute('data-conversion'), { page: location.pathname });
  }

  /* --- 5. Formulaire de devis ---------------------------------------------
     Le formulaire est entièrement validé côté serveur : ce bloc n'ajoute que
     le confort d'un message immédiat et l'horodatage anti-robot. Le retirer
     ne casserait rien.
     ------------------------------------------------------------------------ */

  var form = document.querySelector('form[data-devis]');
  if (form) {
    var horodatage = form.querySelector('input[name="_horodatage"]');
    if (horodatage) { horodatage.value = String(Math.floor(Date.now() / 1000)); }

    form.addEventListener('submit', function () {
      var bouton = form.querySelector('button[type="submit"]');
      if (bouton && form.checkValidity()) {
        bouton.disabled = true;
        bouton.textContent = 'Envoi en cours…';
        // Réactivation si l'utilisateur revient en arrière depuis le cache.
        setTimeout(function () {
          bouton.disabled = false;
          bouton.textContent = 'Envoyer ma demande';
        }, 8000);
      }
    });
  }
})();
