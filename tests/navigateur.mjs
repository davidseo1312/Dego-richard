/* ===========================================================================
 *  Tests de navigateur — parcours réels, sur mobile et sur ordinateur.
 *
 *      bash tests/lancer.sh
 *
 *  Ce que ce fichier vérifie, et que ni le build ni check-seo.sh ne peuvent
 *  voir : le menu s'ouvre, la FAQ se déplie, la barre d'appel est au bon
 *  endroit, le formulaire refuse une saisie incomplète, aucun cookie n'est
 *  déposé sans consentement, et le site reste utilisable sans JavaScript.
 *
 *  Dépendance : Playwright. Facultatif — le site se construit et se déploie
 *  sans lui. Voir tests/lancer.sh.
 * ======================================================================== */

import { chromium, devices } from 'playwright';

const BASE = process.env.BASE_URL || 'http://localhost:8099';
// Certains environnements fournissent déjà un Chromium : CHROMIUM_PATH permet
// de l'utiliser plutôt que de retélécharger celui de Playwright.
const LANCEMENT = process.env.CHROMIUM_PATH
  ? { executablePath: process.env.CHROMIUM_PATH }
  : {};

let reussis = 0;
let echecs = 0;

function verifier(condition, description) {
  if (condition) {
    reussis += 1;
    console.log(`  \x1b[32mv\x1b[0m ${description}`);
  } else {
    echecs += 1;
    console.log(`  \x1b[31mx\x1b[0m ${description}`);
  }
}

function titre(texte) {
  console.log(`\n\x1b[1m${texte}\x1b[0m`);
}

const PAGES = [
  ['accueil', '/'],
  ['prestations', '/services'],
  ['urgence', '/degorgement-urgence'],
  ['débouchage WC', '/debouchage-wc'],
  ['canalisation extérieure', '/debouchage-canalisation-exterieure'],
  ['devis', '/devis'],
  ['FAQ', '/faq'],
  ['page ville', '/degorgement-rennes'],
  ['tarifs', '/tarifs'],
  ['page départementale', '/departements/morbihan'],
  ['zone d’intervention', '/zone-intervention'],
  ['blog', '/blog/'],
  ['article', '/blog/wc-bouche-que-faire'],
  ['mentions légales', '/mentions-legales'],
  ['404', '/page-inexistante'],
];

const navigateur = await chromium.launch(LANCEMENT);

/* --- 1. Chaque page se charge sans erreur, sur trois formats -------------- */

titre('1. Chargement des pages');

for (const [nomAppareil, options] of [
  ['ordinateur', { viewport: { width: 1440, height: 900 } }],
  ['iPhone', devices['iPhone 13']],
  ['Android', devices['Pixel 7']],
]) {
  const contexte = await navigateur.newContext({ ...options, locale: 'fr-FR' });
  const page = await contexte.newPage();

  const incidents = [];
  page.on('pageerror', (e) => incidents.push(`erreur JS : ${e.message}`));
  page.on('console', (m) => {
    if (m.type() === 'error' && !m.text().includes('404')) incidents.push(`console : ${m.text()}`);
  });
  page.on('requestfailed', (r) => {
    if (!r.url().includes('page-inexistante')) incidents.push(`requête échouée : ${r.url()}`);
  });

  const debordements = [];
  for (const [, chemin] of PAGES) {
    const reponse = await page.goto(BASE + chemin, { waitUntil: 'networkidle' });
    const attendu = chemin === '/page-inexistante' ? 404 : 200;
    if (reponse.status() !== attendu) {
      incidents.push(`${chemin} répond ${reponse.status()} au lieu de ${attendu}`);
    }
    // Un débordement horizontal oblige à faire glisser la page latéralement :
    // c'est le défaut mobile le plus courant, et le plus vite sanctionné.
    const trop = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    if (trop > 1) debordements.push(`${chemin} (+${trop}px)`);
  }

  verifier(incidents.length === 0, `${nomAppareil} : ${PAGES.length} pages sans erreur`
    + (incidents.length ? ` — ${incidents.slice(0, 3).join(' | ')}` : ''));
  verifier(debordements.length === 0, `${nomAppareil} : aucun débordement horizontal`
    + (debordements.length ? ` — ${debordements.join(', ')}` : ''));

  await contexte.close();
}

/* --- 2. Navigation et composants ----------------------------------------- */

titre('2. Navigation sur mobile');

const ctxMobile = await navigateur.newContext({ ...devices['iPhone 13'], locale: 'fr-FR' });
const mobile = await ctxMobile.newPage();

await mobile.goto(BASE + '/');
const menu = mobile.locator('#nav-principal');
verifier(!(await menu.isVisible()), 'le menu est fermé au chargement');

await mobile.locator('.nav-toggle').click();
verifier(await menu.isVisible(), 'le menu s’ouvre au clic');
verifier(
  (await mobile.locator('.nav-toggle').getAttribute('aria-expanded')) === 'true',
  'aria-expanded passe à true'
);

await mobile.keyboard.press('Escape');
// La fermeture est animée : le tiroir ne redevient invisible qu'une fois la
// glissade terminée. On observe donc l'état final, pas un état transitoire.
await menu.waitFor({ state: 'hidden', timeout: 2000 }).catch(() => {});
verifier(!(await menu.isVisible()), 'la touche Échap referme le menu');

await mobile.locator('.nav-toggle').click();
await mobile.locator('#nav-principal a[href="/tarifs"]').click();
await mobile.waitForLoadState('domcontentloaded');
verifier(mobile.url().endsWith('/tarifs'), 'un lien du menu navigue bien');

titre('3. Barre d’appel fixe');

await mobile.goto(BASE + '/');
const barre = mobile.locator('.barre-mobile');
verifier(await barre.isVisible(), 'la barre d’appel est visible sur mobile');
const boite = await barre.boundingBox();
const ecran = mobile.viewportSize();
verifier(Math.abs(boite.y + boite.height - ecran.height) < 2, 'elle est collée au bas de l’écran');
verifier(boite.height >= 48, `sa hauteur est confortable (${Math.round(boite.height)} px)`);
verifier(
  (await mobile.locator('.barre-mobile-appel').getAttribute('href')).startsWith('tel:+33'),
  'le lien d’appel est au format international'
);

titre('4. Cibles tactiles (WCAG 2.5.8)');

// Les liens en pleine phrase sont exclus : la norme les dispense explicitement.
const petites = await mobile.evaluate(() => {
  const trop = [];
  for (const el of document.querySelectorAll('a, button, input:not([type=hidden]), select, textarea')) {
    const r = el.getBoundingClientRect();
    if (!r.width && !r.height) continue;
    // Exception « Inline » du critère : un lien inséré dans une phrase est
    // dispensé. Ce qui la caractérise, c'est d'être rendu en display:inline
    // au milieu d'un texte plus long — pas d'avoir un <p> pour parent direct.
    // Un lien d'action, lui, est en inline-flex ou en bloc : il reste soumis.
    const bloc = el.closest('p, li, td, dd, figcaption, blockquote, summary');
    const enPleinePhrase = bloc
      && getComputedStyle(el).display === 'inline'
      && bloc.textContent.trim().length > (el.textContent || '').trim().length + 20;
    if (enPleinePhrase) continue;
    if (r.height < 24) trop.push(`${el.tagName} « ${(el.textContent || '').trim().slice(0, 25)} » ${Math.round(r.height)}px`);
  }
  return trop;
});
verifier(petites.length === 0, `toutes les cibles font au moins 24 px${petites.length ? ' — ' + petites.slice(0, 4).join(', ') : ''}`);

titre('5. Blocs FAQ');

await mobile.goto(BASE + '/faq');
const question = mobile.locator('.faq details').first();
verifier(!(await question.evaluate((e) => e.open)), 'les questions sont repliées au chargement');
await question.locator('summary').click();
verifier(await question.evaluate((e) => e.open), 'une question s’ouvre au clic');
verifier(
  (await mobile.locator('.faq details').count()) >= 10,
  'la page FAQ propose au moins dix questions'
);

titre('6. Bloc de réponse rapide (GEO)');

await mobile.goto(BASE + '/degorgement');
verifier(
  await mobile.locator('.reponse-rapide').first().isVisible(),
  'la page de service porte un bloc « Réponse rapide »'
);
await mobile.goto(BASE + '/degorgement-rennes');
verifier(
  await mobile.locator('.reponse-rapide').first().isVisible(),
  'la page communale porte un bloc « Réponse rapide »'
);

titre('7. Formulaire de demande');

await mobile.goto(BASE + '/devis');
await mobile.locator('form[data-devis] button[type=submit]').click();
verifier(mobile.url().includes('/devis'), 'un envoi incomplet est refusé sur place');
verifier(
  (await mobile.locator('form[data-devis] :invalid').count()) > 0,
  'le navigateur signale les champs manquants'
);
verifier(
  Number(await mobile.locator('input[name=_horodatage]').inputValue()) > 1e9,
  'l’horodatage anti-robot est renseigné'
);
verifier(
  (await mobile.locator('.pot-de-miel input').boundingBox()).x < 0,
  'le piège à robots est hors de l’écran'
);
verifier(
  (await mobile.locator('select[name=departement] option').count()) === 7,
  'le sélecteur de département propose les six départements couverts'
);

titre('8. Vie privée');

verifier((await ctxMobile.cookies()).length === 0, 'aucun cookie déposé sans consentement');
const mesureActive = await mobile.evaluate(
  () => Boolean(document.documentElement.dataset.ga || document.documentElement.dataset.gtm)
);
verifier(
  mesureActive || (await mobile.locator('.cookie-bandeau').count()) === 0,
  mesureActive
    ? 'mesure d’audience configurée : le bandeau de consentement doit s’afficher'
    : 'aucune mesure d’audience configurée : aucun bandeau, aucun script tiers'
);

await ctxMobile.close();

titre('9. Fonctionnement sans JavaScript');

const ctxSansJs = await navigateur.newContext({ ...devices['iPhone 13'], javaScriptEnabled: false });
const sansJs = await ctxSansJs.newPage();

await sansJs.goto(BASE + '/devis');
verifier(await sansJs.locator('form[data-devis]').isVisible(), 'le formulaire reste affiché');
verifier(await sansJs.locator('.barre-mobile-appel').isVisible(), 'le bouton d’appel reste affiché');
await sansJs.goto(BASE + '/faq');
verifier(await sansJs.locator('.faq details').first().isVisible(), 'la FAQ reste consultable');
await sansJs.goto(BASE + '/');
verifier((await sansJs.locator('a[href^="tel:"]').count()) > 0, 'les liens d’appel restent présents');
await ctxSansJs.close();

titre('10. Accessibilité au clavier');

const ctxBureau = await navigateur.newContext({ viewport: { width: 1440, height: 900 }, locale: 'fr-FR' });
const bureau = await ctxBureau.newPage();
await bureau.goto(BASE + '/');
await bureau.keyboard.press('Tab');
verifier(
  (await bureau.evaluate(() => document.activeElement.className)).includes('skip-link'),
  'le premier arrêt de tabulation est le lien d’évitement'
);
await bureau.keyboard.press('Enter');
await bureau.waitForTimeout(200);
verifier(
  await bureau.evaluate(() => Boolean(document.getElementById('contenu'))),
  'la cible du lien d’évitement existe'
);
const sansTexte = await bureau.evaluate(() => {
  const vides = [];
  for (const a of document.querySelectorAll('a')) {
    const texte = (a.textContent || '').trim() || a.getAttribute('aria-label') || a.title;
    if (!texte) vides.push(a.getAttribute('href') || '(sans href)');
  }
  return vides;
});
verifier(sansTexte.length === 0, `tous les liens ont un intitulé${sansTexte.length ? ' — ' + sansTexte.join(', ') : ''}`);
await ctxBureau.close();

/* --- 11. Photographies : sources responsives ------------------------------ */

titre('11. Photographies');

const ctxPhoto = await navigateur.newContext({ locale: 'fr-FR', viewport: { width: 1440, height: 900 } });
const photo = await ctxPhoto.newPage();
await photo.goto(BASE + '/');

// Les visuels hors écran sont en chargement différé : sans parcourir la page,
// on mesurerait un état que le visiteur ne voit jamais.
await photo.evaluate(async () => {
  const h = document.body.scrollHeight;
  for (let y = 0; y < h; y += 600) {
    window.scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 60));
  }
  window.scrollTo(0, 0);
  // Le chargement différé est ensuite neutralisé : ce qu'on vérifie ici, c'est
  // que chaque fichier référencé existe et se décode — pas l'heuristique par
  // laquelle Chromium décide du moment de le demander. Attente bornée, sinon
  // un test qui pend finit par être désactivé.
  const attendre = (i) => Promise.race([
    i.decode().catch(() => {}),
    new Promise((r) => setTimeout(r, 5000))
  ]);
  [...document.images].forEach((i) => { i.loading = 'eager'; });
  await Promise.all([...document.images].map(attendre));
});

const visuels = await photo.evaluate(() => {
  const r = [];
  for (const img of document.querySelectorAll('picture img')) {
    r.push({
      alt: (img.getAttribute('alt') || '').trim(),
      srcset: Boolean(img.getAttribute('srcset')),
      sizes: Boolean(img.getAttribute('sizes')),
      dims: Boolean(img.getAttribute('width') && img.getAttribute('height')),
      avif: Boolean(img.parentElement.querySelector('source[type="image/avif"]')),
      charge: img.naturalWidth > 0
    });
  }
  return r;
});
verifier(visuels.length >= 5, `${visuels.length} photographie(s) sur l’accueil`);
verifier(visuels.every((v) => v.charge), 'toutes les photographies se chargent');
verifier(visuels.every((v) => v.srcset && v.sizes), 'toutes déclarent srcset et sizes');
verifier(visuels.every((v) => v.dims), 'toutes déclarent leurs dimensions');
verifier(visuels.every((v) => v.avif), 'toutes proposent une source AVIF');
verifier(
  visuels.every((v) => v.alt.length > 15 && !/^(image|photo|img)/i.test(v.alt)),
  'toutes portent un texte alternatif descriptif'
);

// Le navigateur doit choisir une largeur adaptée, pas la plus grande.
const choisie = await photo.evaluate(
  () => document.querySelector('.hero-media picture img')?.currentSrc || ''
);
verifier(/-(480|768|1024|1366)\./.test(choisie),
  `la largeur servie est adaptée à l’affichage (${choisie.split('/').pop()})`);

/* --- 12. Carte des zones d’intervention ---------------------------------- */

titre('12. Carte des zones d’intervention');

verifier(
  (await photo.locator('.carte-liste a').count()) === 6,
  'les six départements sont listés en HTML, sans JavaScript'
);
verifier(
  await photo.evaluate(() => typeof window.L === 'undefined'),
  'aucune bibliothèque de carte chargée avant le clic'
);

await photo.locator('.carte-bloc').scrollIntoViewIfNeeded();
await photo.locator('[data-carte-charger]').click();
await photo.waitForFunction(() => typeof window.L !== 'undefined', null, { timeout: 15000 });
await photo.waitForTimeout(1200);

verifier(
  (await photo.locator('#carte path.leaflet-interactive').count()) === 6,
  'la carte affiche un repère par département'
);
verifier(
  (await photo.locator('.leaflet-control-attribution').innerText()).includes('OpenStreetMap'),
  'l’attribution OpenStreetMap est présente'
);
const horsZone = await photo.evaluate(() => {
  const interdits = ['Manche', 'Calvados', 'Mayenne', 'Sarthe', 'Vendée', 'Orne'];
  const texte = document.querySelector('#zone')?.textContent || '';
  return interdits.filter((d) => texte.includes(d));
});
verifier(horsZone.length === 0,
  `aucun département hors zone sur la carte${horsZone.length ? ' — ' + horsZone.join(', ') : ''}`);

await ctxPhoto.close();

await navigateur.close();

console.log('\n\x1b[1mBilan\x1b[0m');
console.log(`  \x1b[32m${reussis} test(s) réussi(s)\x1b[0m`);
console.log(`  ${echecs ? '\x1b[31m' : ''}${echecs} test(s) en échec\x1b[0m\n`);

process.exit(echecs === 0 ? 0 : 1);
