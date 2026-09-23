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
---

## Sprint 2 — US 2.2 : Index + mapping k-NN (21/09/2026)

### 1. Objectif et résultat

Créer, **en Python** (client `opensearch-py`, pas en CDK), l'index dans la collection, avec un champ `knn_vector` de dimension 1024 (métrique **cosinus**) + les champs de métadonnées, puis vérifier le mapping. **✅ Fait et vérifié.**

**Code produit (`src/indexation/`) :**
- `client.py` — fabrique un client `opensearch-py` authentifié en **SigV4** (service **`aoss`**). Réutilisable pour toute la suite du Sprint 2.
- `create_index.py` — définit le mapping (`CORPS_INDEX`) et crée l'index de façon **idempotente**.
- `verify_index.py` — relit le mapping et effectue un contrôle automatique (knn_vector, 1024, cosinus).

**Mapping retenu :** champ `embedding` en `knn_vector`, `dimension: 1024`, `method: hnsw`, `engine: nmslib`, `space_type: cosinesimil` (= cosinus), `parameters: {m: 16, ef_construction: 512}` ; métadonnées `texte` (text), `source` (keyword), `page` / `chunk_index` / `nb_tokens` (integer).

### 2. Le gros bug de la journée : `403 authorization_exception` à la création de l'index

**Symptôme :** la connexion et le test d'existence passaient, mais `indices.create` renvoyait `403 ... User does not have permissions for the requested resource`.

**Démarche de diagnostic (élimination une à une) :**
1. Signataire = `aoss` (pas `es`) → OK.
2. Data access policy → couvrait bien `collection/...` ET `index/.../*` avec `aoss:CreateIndex` → OK.
3. Network policy publique → OK.
4. IAM du rôle → inline policy `Action:"*" Resource:"*"` (droit total) → `aoss:APIAccessAll` déjà présent → IAM hors de cause.
5. Endpoint ↔ collection → correspondaient bien → OK.
6. **ARN du rôle** → le vrai ARN du rôle SSO contient un **chemin** (`.../aws-reserved/sso.amazonaws.com/us-west-2/...`) que le `Principal` de la data access policy **n'avait pas**.

**Cause racine :** dans la data access policy, le `Principal` était l'ARN du rôle **sans le chemin**. AOSS résout l'appelant vers son vrai rôle (avec chemin) et ne trouve pas de correspondance → 403. Pour un rôle SSO, il faut **l'ARN réel complet, avec le chemin**.

**Correction :**
- `infra/.env` → `DATA_ACCESS_ROLE_ARN` corrigé avec le chemin complet.
- La data access policy déployée a été mise à jour via `aws opensearchserverless update-access-policy` (le `cdk deploy` était bloqué par un bucket de bootstrap manquant — voir hygiène ci-dessous).
- Après ~1 min de propagation : **création de l'index réussie**.

### 3. Concepts appris

- **Plan de contrôle vs plan de données** : créer l'index / écrire / chercher relève du *plan de données* (exige `aoss:APIAccessAll` côté IAM), distinct des actions de *contrôle* (créer la collection, les policies).
- **`es:` vs `aoss:`** : deux services AWS distincts (OpenSearch managé vs Serverless), aux permissions étanches. `es:*` ne donne aucun droit sur Serverless.
- **ARN d'un rôle SSO** : il porte un chemin `aws-reserved/sso.amazonaws.com/<région>/` ; c'est l'ARN **complet** (avec chemin) qu'attend une data access policy AOSS.
- **HNSW** : algorithme de recherche vectorielle approximative (graphe multi-couches « autoroutes → rues ») ; réglages `m` (voisins/nœud) et `ef_construction` (qualité à la construction).
- **`update-access-policy`** : met à jour la data access policy en exigeant sa `policyVersion` courante (verrouillage optimiste).

### 4. Points d'hygiène à régler plus tard

- **Bucket de bootstrap CDK manquant** : `cdk deploy` échoue (`No bucket named cdk-hnb659fds-assets-...`) alors que `cdk bootstrap` dit « no changes ». Le bucket de staging a été supprimé hors CDK ; à recréer (re-bootstrap forcé) pour réaligner l'IaC.
- **Drift CDK ↔ réalité** : la data access policy a été corrigée via CLI, pas via CDK. `infra/.env` est déjà aligné ; au prochain `cdk deploy` réussi, vérifier que CloudFormation se réaligne sans conflit de version.
- **Fichiers temporaires à supprimer** : `aoss-apiaccess-policy.json`, `updated-data-access-policy.json` (racine du projet) et `pol.json` (dossier utilisateur).

### 5. Prochaine étape

- [ ] **US 2.3** : indexer les chunks vectorisés du Sprint 1 dans l'index (bulk insert).

---

## Sprint 2 — US 2.3 : Indexation des chunks (bulk insert) (23/09/2026)

### 1. Objectif et résultat

Indexer les chunks vectorisés du Sprint 1 dans l'index k-NN `smartovate-chunks`, **en masse (bulk)**. **✅ Fait : 7 documents indexés et vérifiés.**

**Code produit :**
- `src/indexation/bulk_index.py` — flux complet : (1) produire les chunks via le pipeline du Sprint 1, (2) réinitialiser l'index (repartir à vide), (3) insérer en masse via `opensearchpy.helpers.bulk`, (4) vérifier le nombre de documents.
- `src/indexation/verify_index.py` — enrichi : compte désormais les documents présents.

### 2. Concepts appris

- **Indexation en masse (bulk)** : regrouper N documents dans **une seule requête** plutôt qu'un appel par document → rapide, moins d'allers-retours, anti-timeout. Helper `helpers.bulk` : `chunk_size` (batching), `max_retries` + `initial_backoff` (réessais avec attente croissante = *backoff*), `raise_on_error=False` (on collecte les erreurs au lieu de tout arrêter).
- **Pas d'`_id` personnalisé sur VECTORSEARCH** : AOSS interdit les identifiants de documents choisis sur ce type de collection (« Document ID is not supported »). Impossible donc de dédupliquer par `_id` → stratégie **« full re-index »** : supprimer + recréer l'index vide avant chaque indexation complète, pour éviter les doublons. S3 reste la **source de vérité** (l'index est jetable et reconstructible).
- **Cohérence à terme / refresh AOSS** : un document inséré est écrit tout de suite mais ne devient **comptable/cherchable** qu'après le *refresh* (délai de quelques secondes à dizaines de secondes, géré par AOSS). → vérification par **polling** (interroger le compteur en boucle jusqu'au bon total), au lieu d'un `sleep` fixe.

### 3. Pièges rencontrés & résolus

- **Bucket S3 disparu** (`NoSuchBucket`) : le bucket `smartovate-rag-documents-mohamed` avait été supprimé par le ménage du compte sandbox (comme le bucket de bootstrap CDK à l'US 2.2). Corrigé en le recréant (`aws s3 mb`) puis en re-synchronisant les documents locaux (`aws s3 sync data/raw`). Les documents d'origine étaient conservés en local — la source de vérité était intacte.
- **Compteur à 0 juste après l'indexation** : les 7 documents étaient bien insérés (bulk : 7 succès, 0 erreur), mais le comptage immédiat renvoyait 0 à cause du refresh AOSS. Corrigé en rendant la vérification **patiente** (polling avec délai, jusqu'à ~90 s).

### 4. Prochaine étape

- [ ] **US 2.4** : recherche sémantique (k-NN) sur l'index rempli.
