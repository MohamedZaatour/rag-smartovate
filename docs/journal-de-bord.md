# Journal de bord — Stage Système RAG Smartovate

## Jour 1 — Mise en place de l'environnement & US 1.1 (Extraction du texte)

_Date : 30 août 2026_

---

### 1. L'atelier mis en place

- **Environnement conda `rag-smartovate` (Python 3.11)** : une « bulle » isolée pour le projet, sans conflit avec le reste de la machine.
- **VSCode + extensions** : Python, Pylance, Jupyter, Ruff (qualité de code), AWS Toolkit, GitLens, etc.
- **Structure du projet** dans `02-Developpement/` : `src/`, `data/` (raw + processed), `tests/`.
- **Fichiers de config** : `requirements.txt` (dépendances figées), `.gitignore` (protège les secrets), `README.md`.
- **Bibliothèques installées** : `pymupdf` (PDF), `python-docx` (Word), `boto3` (AWS), `python-dotenv` (config).

### 2. US 1.1 — Extraction du texte  ✅ (terminée en local)

Construite pas à pas, en 5 marches :

1. Ouvrir un PDF et afficher son texte brut.
2. Ranger le code dans une **fonction** réutilisable.
3. **Nettoyer** le texte (regex : espaces, sauts de ligne, caractères invisibles).
4. Ajouter les **métadonnées** (nom du fichier, type, date) via un **dictionnaire**.
5. Gérer aussi le **Word**, avec un **aiguilleur** qui choisit l'extracteur selon l'extension.

**Critères d'acceptation :**

| Critère | État |
|---|---|
| Lire des fichiers PDF et DOCX | ✅ Fait |
| Texte nettoyé | ✅ Fait |
| Métadonnées conservées | ✅ Fait |
| Source = bucket Amazon S3 | ⏳ À brancher (attend les accès AWS) |

**Fichier produit :** `src/ingestion/extract.py`

### 3. Concepts appris aujourd'hui (mémo à relire)

- **Environnement virtuel (conda)** : une bulle isolée de bibliothèques, une par projet.
- **Terminal / Anaconda Prompt** : où l'on tape des commandes ; l'Anaconda Prompt est « branché » sur conda.
- **Execution Policy (PowerShell)** : sécurité Windows qui bloque les scripts ; réglée en `RemoteSigned`.
- **pip & requirements.txt** : installateur de bibliothèques + liste de courses reproductible. Une lib peut en tirer d'autres (**dépendances**).
- **Fonction** : `def`, un **paramètre** (entrée), `return` (rend un résultat) ≠ `print` (affiche seulement). Le **décalage** (indentation) définit le bloc.
- **Dictionnaire** : des paires `"clé": valeur` pour regrouper des infos (ex. texte + métadonnées).
- **Boucle `for`** et **liste** : répéter une action sur chaque élément.
- **`if / elif / else`** : tester des conditions ; `.endswith(".pdf")`, `.lower()`.
- **Expressions régulières (`re`)** : décrire des motifs. `[ ]` = un caractère parmi ; `+` = un ou plusieurs ; `{3,}` = 3 ou plus ; `\n` = saut de ligne.
- **Encodage des caractères** : chaque caractère a un code (ASCII) ; les codes 0–31 sont des « caractères de contrôle » invisibles (sauf tab, saut de ligne, retour chariot).
- **Gestion d'erreurs** : `raise ValueError(...)` pour échouer proprement et tôt.
- **Dates** : règle d'or « **stocker en UTC, afficher en local** » ; toujours préciser le fuseau.
- **Linter (Ruff)** : un relecteur automatique. Différence **warning** (ça marche mais…) vs **erreur** (ça casse). Astuce : `Shift+Alt+O` range les imports. Convention : 2 espaces avant un commentaire `#`.
- **Piège** : le nom installé (pip) ≠ le nom importé (code) — ex. `pymupdf` → `import pymupdf`, `python-docx` → `import docx`, `python-dotenv` → `import dotenv`.

### 4. Prochaines étapes

- [ ] **Sauvegarder avec Git** (premier commit) — livrable exigé par le cahier des charges.
- [ ] **US 1.2** : découpage (chunking) + vectorisation (embeddings).
- [ ] **Brancher la lecture depuis S3** quand les accès AWS seront prêts.

### 5. À demander à l'encadrant Smartovate (AWS)

- Un utilisateur **IAM** avec accès **S3, Bedrock et OpenSearch**.
- La **région AWS** de travail (ex. `us-east-1`).
- Le **nom du bucket S3** où seront déposés les documents.
- L'**activation de l'accès aux modèles Bedrock** (Claude 3 + Titan Embeddings) dans la console.

---

_« From zero to hero » — étape 1 franchie. 🚀_

## Jour 2 — US 1.2 : Découpage & Vectorisation (Chunking & Embedding)

_Date : 8 septembre 2026_

---

### 1. US 1.2 — terminée ✅ (chaîne complète, testée en réel)

**Objectif :** transformer le texte extrait (US 1.1) en **chunks vectorisés**, prêts à être indexés dans OpenSearch.

Construite en 3 briques + un orchestrateur :

1. **`chunking.py`** — découpe chaque page en morceaux (« chunks ») de ~500 tokens avec 10 % de chevauchement (overlap), par une **fenêtre glissante**. Chaque chunk garde ses métadonnées (source, n° de page). L'overlap est calculé automatiquement (10 % de la taille).
2. **`embeddings.py`** — envoie chaque chunk à **Amazon Titan Text Embeddings V2** via Bedrock (`invoke_model`) et récupère un **vecteur de 1024 dimensions**.
3. **`pipeline.py`** — l'orchestrateur : pour chaque document du bucket S3, enchaîne **extraction → chunking → embeddings**.

**Test réel réussi :** 2 documents (cahier des charges PDF → 6 chunks ; note Word → 1 chunk) → **7 chunks vectorisés** (dimension 1024), 0 échec.

**Tests automatiques :** 15 tests pytest au vert (extraction + chunking + embeddings), avec des **mocks** pour ne pas appeler AWS.

**Revue de code de fin de sprint :** fuite de fichier temporaire corrigée (`try/finally`), pagination S3 ajoutée, et **retry automatique** sur les appels Titan (anticipe les timeouts).

### 2. Concepts appris aujourd'hui

- **Chunk / chunking** : découper un document en petits passages focalisés — l'unité de recherche du RAG.
- **Overlap (chevauchement)** : recopier la fin d'un chunk au début du suivant pour ne pas couper une idée en deux. Ici 10 % de la taille.
- **Token** : l'unité de découpage des modèles de langage ; comptée avec **tiktoken**.
- **Embedding / vecteur** : une liste de nombres représentant le **sens** d'un texte ; deux sens proches → deux vecteurs proches. C'est la base de la recherche sémantique.
- **Bedrock / Titan** : appeler un modèle d'IA d'AWS via `invoke_model` (client `bedrock-runtime`).
- **JSON** : `json.dumps` (emballer Python → JSON) et `json.loads` (déballer JSON → Python) pour dialoguer avec Titan.
- **Générateur (`yield`)** : rendre les éléments un par un, à la demande.
- **Chargement paresseux (lazy)** : charger une ressource coûteuse au premier usage, pas à l'import.
- **Package & imports qualifiés** : `from ingestion.xxx import ...`, lancé avec `python -m ingestion.xxx`.
- **Mock** : remplacer une dépendance (le client Titan) par un faux objet pour tester **sans réseau ni coût**.
- **Retry / backoff** : boto3 réessaie tout seul en cas d'erreur passagère (via `Config`).

### 3. Prochaines étapes

- [ ] **Sprint 2 — Base vectorielle OpenSearch** : créer l'index (mapping avec un champ `knn_vector` de dimension 1024) et y **indexer** les chunks vectorisés.
- [ ] Appel de suivi avec l'encadrant (M. Abdelkhalek).

---

_« From zero to hero » — Sprint 1 (Ingestion) bouclé. 🚀_

## Jour 3 — Sprint 2 / US 2.1 : Provisionnement de la base vectorielle (IaC)

_Date : 14 septembre 2026_

---

### 1. US 2.1 — Infrastructure OpenSearch en CDK ✅ (déployée sur AWS)

**Objectif :** créer, en Infrastructure as Code (AWS CDK Python), la collection OpenSearch Serverless qui hébergera les chunks vectorisés du Sprint 1.

Construite en 4 « briques », dans un dossier `infra/` séparé du code applicatif :

1. **Encryption policy** — chiffrement des données au repos, avec la clé gérée par AWS (`AWSOwnedKey`).
2. **Network policy** — accès réseau **public** (le code tourne hors d'AWS), pour la collection et son dashboard.
3. **Data access policy** — autorise le rôle **DataScientist** à lire/écrire (`aoss:ReadDocument` / `aoss:WriteDocument`) et à gérer les index. Répond au critère du cahier des charges.
4. **La collection** `smartovate-rag-mohamed` (type `VECTORSEARCH`), avec des **dépendances explicites** pour se créer APRÈS les 3 policies.

**Config externalisée :** les valeurs sensibles (nom de collection, ARN du rôle) sont sorties du code dans un fichier `infra/.env` (ignoré par Git), avec un `infra/.env.example` versionné comme modèle.

**Déploiement réel réussi :** `cdk bootstrap` (déjà en place) puis `cdk deploy` → les 4 ressources créées dans le bon ordre, sans erreur. Collection vérifiée **`ACTIVE`**.

**Endpoint de la collection** (à utiliser dès l'US 2.2) :
`https://xxxxxxxxxxxx.us-west-2.aoss.amazonaws.com`

**Critères d'acceptation (cahier des charges) :**

| Critère | État |
|---|---|
| Infrastructure définie via AWS CDK ou Terraform | ✅ Fait (CDK) |
| Index k-NN à la dimension Titan (1024) | ⏳ US 2.2 |
| Data Access Policies (lecture/écriture) configurées | ✅ Fait |

### 2. Concepts appris aujourd'hui (mémo à relire)

- **IaC (Infrastructure as Code)** : décrire son infra en code (versionné, reproductible) au lieu de cliquer dans la console.
- **AWS CDK** : écrire l'infra en Python, qui génère un plan **CloudFormation**. Cycle : `synth` (aperçu) → `bootstrap` (préparer le terrain, une fois) → `deploy` (construire) → `destroy` (nettoyer).
- **App / Stack / Construct** : l'app contient des stacks (unités de déploiement) qui contiennent des constructs (briques de ressources). Constructs **L1** (`Cfn...`) = correspondance directe avec CloudFormation.
- **OpenSearch Serverless** : AWS gère les serveurs ; on crée une **collection** (le conteneur) sans dimensionner de cluster.
- **Collection vs Index vs Document** : l'armoire (collection) contient des tiroirs (index) qui contiennent des fiches (documents = chunks). Armoire créée en CDK, tiroirs créés plus tard en Python.
- **Chiffrement au repos** : brouiller les données sur le disque ; illisible sans la clé.
- **Réseau vs Identité** : la network policy = la porte (par où on arrive) ; la data access policy = le badge (qui a le droit de faire quoi). Deux contrôles séparés.
- **IAM vs Data access policy** : IAM (`aoss:*`) = badge d'employé général ; data access policy = autorisation locale, gérée par OpenSearch, sur une collection précise. **Les deux sont nécessaires.**
- **ARN** : l'adresse unique et officielle d'une ressource AWS. Le rôle SSO a la forme `role/AWSReservedSSO_DataScientist_...`.
- **`.env` / `python-dotenv`** : sortir la config sensible du code ; `load_dotenv()` charge le fichier, `os.environ[...]` lit les valeurs. `.env` ignoré par Git, `.env.example` versionné.
- **Dépendances CDK (`add_resource_dependency`)** : forcer l'ordre de création (les policies avant la collection).
- **Bootstrap** : outillage technique réutilisable du CDK (bucket S3 + rôles), à ne pas confondre avec le bucket S3 des documents (Sprint 1).

### 3. Prochaines étapes

- [ ] **US 2.2** : créer l'index dans la collection, avec le **mapping k-NN** (champ `knn_vector` dimension 1024), en Python via le client `opensearch-py`.
- [ ] **US 2.3** : indexer les chunks vectorisés (bulk insert).
- [ ] **US 2.4** : tester la recherche sémantique (k-NN).

---

_« From zero to hero » — première infrastructure cloud déployée. 🚀_