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

/* Les redirections 301 sont LUES dans le .htaccess, pas recopiées ici.
 *
 * Elles l'étaient, et les deux listes ont divergé : le .htaccess a fini par
 * contenir « /services -> /services », une boucle infinie qui rendait la page
 * des prestations inaccessible en production, pendant que cette liste-ci,
 * restée saine, laissait l'aperçu local fonctionner. Un bug invisible chez
 * soi et fatal en ligne : exactement ce qu'une seconde source de vérité
 * produit. */
$redirections = [];
$htaccess = __DIR__ . '/../static/.htaccess';
if (is_file($htaccess)) {
    foreach (file($htaccess) as $ligne) {
        if (preg_match('#^RewriteRule\s+\^([a-z0-9/-]+)/\?\$\s+(/\S*)\s+\[R=301#i',
                       $ligne, $m)) {
            $redirections['/' . $m[1]] = $m[2];
        }
    }
}

$sansSlash = rtrim($chemin, '/');
if ($sansSlash !== '' && isset($redirections[$sansSlash])) {
    header('Location: ' . $redirections[$sansSlash], true, 301);
    exit;
}

/* /page/ -> /page, sauf si c'est un vrai dossier (/blog/).
 * Le .htaccess le fait en production ; sans cette regle ici, l'aperçu local
 * servait /tarifs/ en 200 et laissait croire à deux adresses valides pour la
 * même page — le doublon que la redirection est censée supprimer. */
if ($chemin !== '/' && substr($chemin, -1) === '/'
    && !is_dir($racine . rtrim($chemin, '/'))) {
    header('Location: ' . rtrim($chemin, '/'), true, 301);
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
