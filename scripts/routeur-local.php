<?php
/* ===========================================================================
 *  Routeur pour le serveur de développement PHP.
 *
 *      bash scripts/apercu.sh
 *
 *  Il reproduit les règles du .htaccess de production : URLs sans extension,
 *  redirections 301 des variantes d'adresses, page 404 personnalisée. Sans
 *  lui, l'aperçu local ne ressemblerait pas au site en ligne.
 *
 *  Ce fichier ne part JAMAIS en production : il vit dans scripts/, pas dans
 *  static/, et n'est donc pas copié dans public/.
 * ======================================================================== */

$racine = __DIR__ . '/../public';
$chemin = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?? '/';
$chemin = rawurldecode($chemin);

// Les mêmes redirections 301 que le .htaccess.
$redirections = [
    '/urgence'                      => '/degorgement-urgence',
    '/degorgement-urgent'           => '/degorgement-urgence',
    '/debouchage'                   => '/debouchage-canalisation',
    '/canalisation-bouchee'         => '/debouchage-canalisation',
    '/wc-bouche'                    => '/debouchage-wc',
    '/toilettes-bouchees'           => '/debouchage-toilettes',
    '/evier-bouche'                 => '/debouchage-evier',
    '/lavabo-bouche'                => '/debouchage-lavabo',
    '/douche-bouchee'               => '/debouchage-douche',
    '/baignoire-bouchee'            => '/debouchage-baignoire',
    '/hydrocurage'                  => '/curage-canalisation',
    '/camera-canalisation'          => '/inspection-camera-canalisation',
    '/prestations'                  => '/services',
    '/zones-d-intervention'         => '/zone-intervention',
    '/zones'                        => '/zone-intervention',
    '/devis-degorgement'            => '/devis',
    '/tarif'                        => '/tarifs',
    '/politique-de-confidentialite' => '/politique-confidentialite',
];

$sansSlash = rtrim($chemin, '/');
if ($sansSlash !== '' && isset($redirections[$sansSlash])) {
    header('Location: ' . $redirections[$sansSlash], true, 301);
    exit;
}

// /page.html -> /page
if (preg_match('#^(.*)\.html$#', $chemin, $m)) {
    $cible = ($m[1] === '/index') ? '/' : preg_replace('#/index$#', '/', $m[1]);
    header('Location: ' . $cible, true, 301);
    exit;
}

$fichier = $racine . $chemin;

// Fichier réel : servi tel quel (assets, sitemap, robots…).
if (is_file($fichier)) {
    return false;   // le serveur intégré s'en charge, en-têtes compris
}

// Dossier : on sert son index.
if (is_dir($fichier) && is_file(rtrim($fichier, '/') . '/index.html')) {
    readfile(rtrim($fichier, '/') . '/index.html');
    return true;
}

// URL sans extension : on cherche le .html correspondant.
$candidat = $racine . rtrim($chemin, '/') . '.html';
if ($chemin !== '/' && is_file($candidat)) {
    readfile($candidat);
    return true;
}

if ($chemin === '/' && is_file($racine . '/index.html')) {
    readfile($racine . '/index.html');
    return true;
}

http_response_code(404);
if (is_file($racine . '/404.html')) {
    readfile($racine . '/404.html');
}
return true;
