# Déploiement sur Hostinger — marche à suivre complète

Ce document décrit, étape par étape, la mise en ligne du site sur un
hébergement mutualisé Hostinger. Il suppose que vous disposez d'un accès
hPanel et d'un accès au dépôt GitHub.

Objectif :

```
GitHub (branche source) → GitHub Actions → branche deploy → Hostinger → public_html/index.html → HTTP 200
```

Aucun 403 Forbidden. Aucun `index.html` manquant. Aucun `deploy/public/`.
Aucun `public_html/public/`.

---

## Avant de commencer

Vérifiez que vous avez :

* un accès **hPanel** au domaine concerné ;
* les droits d'écriture sur le dépôt GitHub `davidseo1312/Dego-richard` ;
* un nom de domaine pointant vers l'hébergement (propagation DNS terminée) ;
* les informations légales listées dans la section « Avant la mise en ligne »
  du [README](../README.md) — sans elles, le site est techniquement déployable
  mais juridiquement incomplet.

---

## Ce qu'il faut comprendre en premier

Le déploiement Git d'Hostinger, sur une offre mutualisée, **clone un dépôt dans
un dossier**. C'est tout. Il n'exécute :

* ni `npm install` ni `npm run build` ;
* ni script shell ;
* ni hook `post-receive`.

Conséquence directe : si le dépôt cloné place la page d'accueil dans un
sous-dossier — par exemple `public/index.html` —, la racine web ne contient
aucun `index.html`. Apache cherche un fichier d'index, n'en trouve pas, et
comme `Options -Indexes` interdit l'affichage du contenu du dossier, il répond
**403 Forbidden**.

C'est exactement le 403 rencontré sur le projet précédent, et c'est pour cela
que ce projet publie une branche `deploy` dont **la racine est le site**.

| Branche | Contenu | À déployer ? |
|---|---|---|
| branche source (`claude/plumbing-site-brittany-eoxa6x`) | sources, scripts, documentation. Aucun `public/` versionné. | **Non** |
| `deploy` | uniquement le site construit, `index.html` au premier niveau | **Oui** |

---

## Étape 1 — Certificat SSL

**hPanel → Sécurité → SSL.** Installez le certificat gratuit sur le domaine et
attendez qu'il passe à « Actif ».

Activez ensuite la redirection HTTPS d'Hostinger, ou laissez faire le
`.htaccess` du site, qui redirige déjà en 301 vers HTTPS. Les deux ensemble ne
posent pas de problème : la règle du `.htaccess` teste à la fois `%{HTTPS}` et
`%{HTTP:X-Forwarded-Proto}`, ce qui couvre le reverse proxy d'Hostinger.

N'activez **pas** HSTS tant que le certificat n'est pas stable : la directive
est mémorisée deux ans par le navigateur. Elle est présente mais commentée dans
`static/.htaccess`.

---

## Étape 2 — Boîte e-mail d'expédition

Le formulaire envoie les demandes depuis l'adresse `EMAIL_EXPEDITEUR` définie
dans `src/config.sh`. Sur un mutualisé, cette adresse **doit appartenir au
domaine du site**, sinon le message est rejeté ou classé en indésirable par les
contrôles SPF et DKIM.

**hPanel → Emails → Comptes e-mail → Créer.** Créez au minimum :

* `site@votre-domaine.fr` — expéditeur technique (`EMAIL_EXPEDITEUR`) ;
* `contact@votre-domaine.fr` — destinataire des demandes (`EMAIL_DEVIS`).

Reportez ces adresses dans `src/config.sh`, puis reconstruisez.

---

## Étape 3 — Vérifier que la branche `deploy` existe

Elle est créée automatiquement par le premier passage réussi du workflow.

1. Sur GitHub, onglet **Actions**.
2. Le workflow *Build et publication vers Hostinger* doit être vert.
3. Onglet **Code**, sélecteur de branche : `deploy` doit apparaître.
4. Ouvrez-la : vous devez voir `index.html`, `.htaccess`, `robots.txt`,
   `sitemap.xml`, `404.html`, `envoi-demande.php`, `assets/`, `blog/`,
   `departements/` **à la racine** — et **aucun** dossier `public/`.

Si la branche n'existe pas encore, lancez le workflow manuellement :
**Actions → Build et publication vers Hostinger → Run workflow**.

Si vous préférez construire depuis votre poste :

```bash
bash scripts/audit.sh          # doit être entièrement vert
cd public
git init -b deploy
git remote add origin https://github.com/davidseo1312/Dego-richard.git
git add -A && git commit -m "Publication du site"
git push -u origin deploy
```

Notez le `cd public` : c'est **le contenu** de `public/` qui devient la racine
de la branche, jamais le dossier lui-même.

---

## Étape 4 — Connecter Hostinger au dépôt

**hPanel → Sites → votre domaine → Avancé → Git.**

| Champ | Valeur |
|---|---|
| *Repository* | `https://github.com/davidseo1312/Dego-richard.git` |
| *Branch* | **`deploy`** |
| *Directory* | `public_html` (ou vide si le champ correspond déjà à la racine web) |

Puis **Create**, et **Deploy**.

> ⚠ **Ne mettez jamais `public_html/public`.** Le dossier de destination est la
> racine web ; la branche `deploy` contient déjà le site à son premier niveau.

Si le dépôt est privé, utilisez l'URL SSH affichée par Hostinger et déposez la
clé publique qu'il vous donne dans **GitHub → Settings → Deploy keys**.

### Déploiement automatique

hPanel affiche une **Webhook URL** dans la même page. Copiez-la, puis :

**GitHub → Settings → Webhooks → Add webhook**

| Champ | Valeur |
|---|---|
| *Payload URL* | l'URL copiée dans hPanel |
| *Content type* | `application/json` |
| *Which events* | `Just the push event` |

Chaque publication sur `deploy` déclenche alors la mise à jour du site.

---

## Étape 5 — Vérifications sur le site en ligne

```bash
D=https://degorgement-richard.fr

curl -I $D/                          # 200
curl -I $D/degorgement                # 200
curl -I $D/degorgement-urgence        # 200
curl -I $D/debouchage-canalisation    # 200
curl -I $D/debouchage-wc              # 200
curl -I $D/departements/morbihan      # 200
curl -I $D/degorgement-rennes         # 200
curl -I $D/blog/                      # 200
curl -I $D/mentions-legales           # 200
curl -I $D/politique-confidentialite  # 200
curl -I $D/robots.txt                 # 200
curl -I $D/sitemap.xml                # 200
curl -I $D/page-inexistante           # 404 — surtout pas 403
curl -I $D/.git/config                # 403 — attendu
curl -I $D/index.html                 # 301 vers /
curl -I http://degorgement-richard.fr # 301 vers https://
```

Contrôlez également, dans un navigateur :

* le numéro de téléphone dans l'en-tête, cliquable sur mobile ;
* la barre d'appel fixe en bas d'écran sur smartphone ;
* l'envoi d'une demande de test par le formulaire, et sa réception ;
* la page `/merci` après envoi.

---

## Étape 6 — Repli : compte FTP

Si le déploiement Git est indisponible sur votre offre.

**hPanel → Fichiers → Comptes FTP → Créer un compte FTP.** Notez l'hôte,
l'utilisateur et le mot de passe. Ne les mettez **jamais** dans le dépôt :
copiez `.env.exemple` en `.env`, qui est ignoré par Git.

---

## Étape 7 — Repli : envoi FTP

```bash
bash scripts/audit.sh    # doit être entièrement vert

lftp -u "$FTP_UTILISATEUR,$FTP_MOTDEPASSE" "$FTP_HOTE" <<'FTP'
mirror --reverse --delete --verbose --exclude-glob .git* public/ /public_html/
bye
FTP
```

Le `--reverse` envoie, le `--delete` retire du serveur ce qui n'est plus dans
`public/`. Le contenu de `public/` arrive bien **à la racine** de
`public_html/`.

Vérifiez ensuite les permissions :

```bash
lftp -u "$FTP_UTILISATEUR,$FTP_MOTDEPASSE" "$FTP_HOTE" -e \
  'find -d 1 /public_html; bye'
```

Dossiers `755`, fichiers `644`. Jamais `777`.

---

## Repli : dépôt manuel

**hPanel → Fichiers → Gestionnaire de fichiers.**

1. Ouvrez `public_html/` et videz-le (sauf un éventuel dossier `.well-known`).
2. Compressez le **contenu** de `public/` : `cd public && zip -r ../site.zip .`
   — le point compte, il évite d'emballer le dossier lui-même.
3. Téléversez `site.zip` dans `public_html/`, puis **Extract**.
4. Supprimez `site.zip`.
5. Vérifiez que `index.html` est bien au premier niveau de `public_html/`.

---

## Dépannage

### Le site renvoie 403 Forbidden

Dans l'ordre :

1. **Regardez la racine web.** `public_html/index.html` doit exister. Si vous
   voyez `public_html/public/index.html`, le champ *Directory* du déploiement
   Git est mal réglé, ou vous avez téléversé le dossier au lieu de son contenu.
   Corrigez le réglage — ne déplacez pas les fichiers à la main, le prochain
   déploiement recréerait le problème.
2. **Vérifiez la branche déployée.** Ce doit être `deploy`. La branche source ne contient
   aucun `public/` versionné : la racine web serait vide.
3. **Permissions.** Dossiers `755`, fichiers `644`.
4. **`.htaccess`.** Aucune de ses directives ne refuse une page du site ; les
   seuls refus portent sur `/.git`, `/.github`, `/src`, `/scripts`, `/tests`,
   `/docs` et des extensions sensibles.

### Toutes les URLs sans extension renvoient 404

Le `.htaccess` n'est pas pris en compte ou `mod_rewrite` est absent.

1. Vérifiez que le fichier est bien présent à la racine web — il commence par
   un point, activez l'affichage des fichiers cachés dans le gestionnaire.
2. Vérifiez qu'il n'a pas été renommé en `htaccess.txt` au téléversement.
3. Contactez le support si `mod_rewrite` n'est pas actif : le site fonctionnera
   quand même avec les URLs en `.html`, mais les liens internes du site
   pointent vers les URLs sans extension.

### Toutes les pages renvoient 500

Quelques offres mutualisées interdisent la directive `Options` en `.htaccess`,
et Apache répond alors « Options not allowed here ». Commentez la ligne :

```apache
# Options -MultiViews -Indexes
```

Le site fonctionne sans elle.

### Le formulaire affiche « le serveur de messagerie n'a pas pu transmettre »

1. La boîte `EMAIL_EXPEDITEUR` existe-t-elle réellement dans hPanel ?
2. Appartient-elle bien au domaine du site ?
3. La fonction `mail()` est-elle active ? **hPanel → Avancé → Configuration
   PHP**.
4. Consultez les journaux : **hPanel → Fichiers → Journaux d'erreurs**.

### Le message part mais arrive en indésirable

L'expéditeur n'appartient pas au domaine, ou les enregistrements SPF et DKIM ne
sont pas publiés. **hPanel → Emails → Configuration DNS** : activez SPF et DKIM
pour le domaine.

### Une page répond 404 alors qu'elle existe

Regardez d'abord les **redirections** du `.htaccess`. Une règle qui renvoie
vers sa propre adresse boucle indéfiniment ; selon le serveur, le visiteur
reçoit une erreur de redirection ou, sur LiteSpeed, la page 404. C'est arrivé
sur `/services`, et le site local n'en montrait rien : le serveur de
développement PHP n'applique pas le `.htaccess`.

Deux garde-fous ont été posés depuis :

* `scripts/routeur-local.php` **lit** les redirections dans le `.htaccess` au
  lieu d'en tenir une copie. C'est la divergence entre les deux listes qui
  rendait le défaut invisible en local.
* `scripts/test-http.sh` et `scripts/check-indexation.py` suivent chaque
  redirection déclarée et vérifient qu'elle aboutit à un 200 **en un seul
  saut**. Vérifier le code 301 ne suffisait pas : une boucle répond 301 elle
  aussi.

`tests/navigateur.mjs` clique en plus sur les six entrées du menu et vérifie
qu'aucune ne mène à une 404 — c'est par là que le défaut s'était manifesté.

---

### Une modification n'apparaît pas en ligne

1. Le workflow GitHub est-il vert ?
2. La branche `deploy` a-t-elle bien été mise à jour (dernier commit) ?
3. Hostinger a-t-il redéployé ? Relancez *Deploy* dans hPanel.
4. Essayez dans une fenêtre de navigation privée. Si la modification apparaît
   là et pas ailleurs, c'est le cache du navigateur.

**Sur le cache, et pourquoi ce n'est normalement plus un problème.** Le
`.htaccess` sert les feuilles de style, les scripts et les icônes avec
`Cache-Control: immutable, max-age=1 an`. C'est le bon réglage pour la
vitesse, mais `immutable` signifie littéralement « ne me redemande pas » : un
visiteur déjà venu garde son ancienne copie pendant un an, sans même
revalider. Une refonte complète peut ainsi rester invisible pour tous ceux qui
connaissent déjà le site.

Le build résout cela en donnant à chaque fichier un numéro de version tiré de
son propre contenu :

```html
<link rel="stylesheet" href="/assets/css/style.css?v=c3ea0a87">
<script src="/assets/js/site.js?v=4491cc3a" defer></script>
<link rel="icon" href="/assets/img/favicon.svg?v=efe59b56">
```

Le contenu change, l'empreinte change, l'URL change, le navigateur redemande.
Le HTML, lui, est servi en `must-revalidate` : il est toujours à jour, donc il
pointe toujours vers la bonne version. Rien à vider, rien à purger.

`scripts/check-seo.sh` vérifie à chaque audit que ces trois fichiers portent
bien un jeton, et qu'il est le même sur les 111 pages.

---

## Après la première mise en ligne

1. **Search Console.** Ajoutez la propriété, vérifiez-la par fichier HTML ou
   par DNS, puis soumettez `https://votre-domaine.fr/sitemap.xml`.
2. **Fiche Google Business Profile.** Renseignez ensuite `URL_GOOGLE_BUSINESS`
   dans `src/config.sh` : elle alimente le champ `sameAs` des données
   structurées, que Google recoupe.
3. **Vérifiez `ROBOTS_POLICY`.** Il doit valoir `index` en production. En
   `noindex`, `robots.txt` interdit toute exploration et le site ne sera pas
   référencé.
4. **Testez le formulaire en conditions réelles**, depuis un téléphone, avec
   une photo jointe.

---

## Mises à jour ultérieures

```bash
# modifier src/config.sh ou src/pages/…
bash scripts/audit.sh          # doit être entièrement vert
git add -A && git commit -m "…" && git push
```

Le workflow reconstruit, contrôle et republie `deploy`. Hostinger récupère la
mise à jour par le webhook, ou sur un clic de *Deploy* dans hPanel.
