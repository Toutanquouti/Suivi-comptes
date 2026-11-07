# Carnet de comptes

Une application mobile pour piloter ton budget à la main : tu notes tes dépenses et tes revenus, tu fixes un objectif d'épargne, et l'appli te dit chaque jour combien il te reste à dépenser.

- **Vue 360** : le reste à dépenser du mois, une jauge avec la projection de fin de mois, tes enveloppes par catégorie et toutes tes opérations.
- **Bouton +** : saisie rapide, avec les opérations fréquentes en raccourcis.
- **Analyse** : semaine, mois, trimestre, année ou dates libres, comparées à la période précédente, à la moyenne des 3 dernières ou à l'an dernier. Ce qui a changé par catégorie, calendrier des dépenses, 12 derniers mois.
- **Bilan** : les indicateurs du mois avec leurs écarts M-1 et N-1, l'épargne mois par mois face à ton objectif, des conseils.
- **Tes catégories** : crée les tiennes (nom, icône, couleur) et des sous-catégories, depuis *Mon budget* → *Gérer mes catégories*, ou directement pendant une saisie avec le bouton **Nouvelle**. Une sous-catégorie est comptée dans sa catégorie principale, avec son détail dans la fiche de la catégorie.

L'appli fonctionne hors connexion. Il n'y a ni compte ni serveur : **tes données restent sur ton téléphone**. Le dépôt GitHub contient seulement le code, jamais tes dépenses.

---

## Mettre l'appli en ligne (une dizaine de minutes)

### 1. Crée le dépôt

1. Connecte-toi sur [github.com](https://github.com).
2. En haut à droite, touche **+** puis **New repository**.
3. Nom : `carnet-de-comptes`. Laisse **Public** coché (obligatoire pour GitHub Pages gratuit), puis **Create repository**.

### 2. Envoie les fichiers

1. Sur la page du dépôt vide, clique sur **uploading an existing file**.
2. Décompresse le zip et ouvre le dossier `carnet-de-comptes`.
3. Sélectionne **tous les fichiers du dossier** (pas le dossier lui-même, ni le zip) et glisse-les dans la page.
4. Clique sur **Commit changes**.

Tu dois voir à la racine du dépôt : `index.html`, `manifest.webmanifest`, `sw.js`, les 4 icônes `.png` et ce `README.md`.

### 3. Active GitHub Pages

1. Dans le dépôt : **Settings** → **Pages** (menu de gauche).
2. **Source** : *Deploy from a branch*. **Branch** : `main` et `/ (root)`, puis **Save**.
3. Attends 1 à 2 minutes et recharge la page. L'adresse de ton appli s'affiche en haut :
   `https://TON-PSEUDO.github.io/carnet-de-comptes/`

### 4. Installe-la sur ton téléphone

Installe-la **avant de commencer à saisir** : sur iPhone, l'appli installée garde ses données à part de Safari.

- **iPhone (Safari)** : ouvre l'adresse, touche le bouton **Partager** puis **Sur l'écran d'accueil**.
- **Android (Chrome)** : ouvre l'adresse, puis touche **Installer** dans la bannière, ou menu **⋮** → **Installer l'application**.

L'icône *Carnet* apparaît sur ton écran d'accueil. Sur Android, un appui long sur l'icône propose **Ajouter une opération**.

---

## Tes données

- Elles sont enregistrées dans l'appli, sur ce téléphone uniquement.
- **Sauvegarde** : *Mon budget* → *Tes données* → **Sauvegarder**. Range le fichier `.json` dans Fichiers, iCloud Drive ou Google Drive. L'appli te le rappelle une fois par mois.
- **Nouveau téléphone** : installe l'appli, puis *Mon budget* → **Restaurer ou importer** → choisis ta sauvegarde.
- **Attention sur iPhone** : supprimer l'icône de l'appli efface ses données. Fais une sauvegarde avant.
- **Export** : *Exporter en CSV* produit un tableau lisible dans Excel, Numbers ou Google Sheets.

### Reprendre les données de la version Claude

Dans la version Claude du carnet : *Mon budget* → **Exporter en CSV**. Puis, dans l'appli : *Mon budget* → **Restaurer ou importer** → choisis ce fichier CSV.

---

## Relier Tricount (facultatif)

Chaque heure, GitHub récupère tes tricounts avec [tricount-extractor](https://github.com/wenceslas-sanchez/tricount-extractor). Il garde seulement **ta part** de chaque dépense (60 € de resto à trois comptent pour 20 €) et ignore les remboursements entre amis. Ces données sont **chiffrées** avant d'être publiées, parce que le dépôt est public. Seule ton appli, avec ta phrase secrète, peut les lire.

1. **Ajoute les 3 secrets** dans le dépôt : **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
   - `TRICOUNT_IDS` : l'identifiant de chaque tricount, c'est-à-dire le code à la fin de son lien de partage. S'il y en a plusieurs, sépare-les par un espace.
   - `TRICOUNT_MOI` : ton nom, écrit exactement comme dans Tricount.
   - `TRICOUNT_PHRASE` : une phrase secrète de ton choix (8 caractères minimum). Garde-la, l'appli te la demandera.
2. **Lance une première fois** : onglet **Actions** → **Tricount** → **Run workflow**. Si GitHub demande d'activer les actions, accepte. Au bout d'une minute, un fichier `tricount.json.enc` apparaît dans le dépôt.
3. **Dans l'appli** : *Mon budget* → *Tricount* → saisis ta phrase secrète → **Synchroniser maintenant**.

Ensuite, tout est automatique : GitHub met à jour chaque heure, et l'appli récupère les nouveautés à chaque ouverture. Pour une mise à jour immédiate, relance **Run workflow**.

À savoir :
- Les dépenses Tricount portent la mention « Tricount » en commentaire. Ne les saisis pas aussi à la main, sinon elles compteraient deux fois.
- Tu peux corriger leur catégorie dans l'appli, mais la synchronisation suivante reprendra la version Tricount.
- tricount-extractor n'est pas un outil officiel de Tricount : si Tricount change son fonctionnement, l'action peut échouer (onglet **Actions**, croix rouge). Ton carnet garde alors les dernières données reçues.
- Si l'action échoue, son journal affiche le nom des colonnes trouvées, jamais tes montants ni tes noms. Envoie ce journal à Claude pour adapter le script.

## Mettre à jour l'appli

1. Dans le dépôt : **Add file** → **Upload files**, glisse le nouveau `index.html` (il remplace l'ancien), puis **Commit changes**.
2. Sur le téléphone, ferme et rouvre l'appli deux fois : la première ouverture télécharge la nouvelle version, la seconde l'affiche.

Tes données ne sont pas touchées par une mise à jour.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `index.html` | L'application complète (écrans, graphiques, calculs) |
| `manifest.webmanifest` | Nom, couleurs et icônes pour l'installation |
| `sw.js` | Fonctionnement hors connexion |
| `icon-192.png`, `icon-512.png`, `icon-maskable.png` | Icônes Android et navigateur |
| `apple-touch-icon.png` | Icône iPhone |
| `.github/workflows/tricount.yml` | Récupération automatique de Tricount, chaque heure |
| `outils/tricount_vers_carnet.py` | Calcul de ta part et chiffrement des données Tricount |
| `tricount.json.enc` | Créé par GitHub : tes dépenses Tricount, chiffrées |

**Envoi des dossiers `.github` et `outils`** : depuis un ordinateur, glisse-les avec les autres fichiers à l'étape 2. Le dossier `.github` est masqué par défaut : sur Mac, appuie sur Cmd+Maj+point dans le Finder pour l'afficher. Si l'envoi le refuse, crée le fichier à la main dans GitHub : **Add file** → **Create new file**, nomme-le `.github/workflows/tricount.yml` et colle son contenu.
