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

---

## 🏁 Clôture officielle du Sprint 2 (24/09/2026)

### Alignement avec le cahier des charges

Le cahier des charges découpe le Sprint 2 (« Mise en place de la Base Vectorielle ») en **2 US** :
- **US 2.1 — Configuration d'Amazon OpenSearch Serverless** (infra IaC + index k-NN dimension Titan + Data Access Policies).
- **US 2.2 — Indexation des documents vectorisés** (bulk insert).

Notre découpe (plus fine) y correspond exactement :

| Cahier des charges | Notre découpe |
|---|---|
| US 2.1 — Config Serverless (infra + index k-NN + policies) | US 2.1 (collection/policies) + US 2.2 (index + mapping) |
| US 2.2 — Indexation (bulk) | US 2.3 |

La **recherche sémantique (retrieval)** appartient au **Sprint 3 (US 3.1)**, pas au Sprint 2.

### Bilan du Sprint 2 — livré

- **Base vectorielle opérationnelle** : collection OpenSearch Serverless `smartovate-rag-mohamed` (type VECTORSEARCH), provisionnée en **AWS CDK** (encryption + network + data access policies).
- **Index k-NN** `smartovate-chunks` : champ `embedding` en `knn_vector`, **dimension 1024**, métrique **cosinus** (nmslib / HNSW) + 5 champs de métadonnées.
- **Indexation en masse** : pipeline Sprint 1 → *full re-index* → **bulk insert** (`helpers.bulk`). **7 documents** indexés et vérifiés.
- **Code** : module `src/indexation/` (`client.py`, `create_index.py`, `verify_index.py`, `bulk_index.py`), documenté et versionné sur GitHub.

### Pièges rencontrés & résolus (matière pour le rapport)

- **US 2.2** — `403` à la création d'index : l'ARN du rôle SSO manquait son **chemin** (`aws-reserved/sso.amazonaws.com/...`) dans la data access policy. Notions clés : **plan de contrôle vs plan de données**, et `es:` vs `aoss:`.
- **US 2.3** — bucket S3 supprimé par le ménage du compte sandbox (`NoSuchBucket`) → recréation + re-sync ; et compteur à 0 après indexation → **refresh AOSS** (cohérence à terme) → vérification par **polling**.

### Prochaine étape — Sprint 3 (Moteur RAG)

- [ ] **US 3.1** : recherche sémantique (retrieval k-NN) — question → vecteur Titan → Top-K chunks.
- [ ] **US 3.2** : génération de la réponse (Bedrock / Claude 3) avec citations et garde-fou anti-hallucination.

---

## Sprint 3 — Étape 0 (prérequis) + US 3.1 : Recherche sémantique (24/09/2026)

### 1. Étape 0 — Vérifications avant de coder

Principe : inspecter le terrain avant d'écrire le moteur RAG.

- **Base vectorielle vérifiée** : `verify_index` confirme l'index `smartovate-chunks` (knn_vector, dim 1024, cosinus) et **7 documents**. Un timeout réseau passager a été levé par un simple réessai (la collection était bien `ACTIVE` — vérifié via `batch-get-collection`).
- **Accès à Claude sur Bedrock prouvé** : nouveau module `src/rag/` + `smoke_test_claude.py` (API **Converse**). Appel réussi, `usage` = 54 tokens.
- **Décision de modèle (matière rapport)** : le cahier prévoyait **Claude 3 Haiku**, mais AWS l'a classé **Legacy** et en bloque l'accès (règle des 30 jours d'inactivité). Substitution **documentée** vers son équivalent actif **Claude Haiku 4.5** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`), même rôle (rapide, économique). ID externalisé dans `.env` (`BEDROCK_LLM_MODEL_ID`, `BEDROCK_LLM_REGION`).

### 2. US 3.1 — Recherche sémantique (Retrieval)

Module `src/rag/retrieval.py` — fonction `rechercher_chunks(question, k=5)` :
1. vectorise la question avec **le même** modèle Titan que les chunks (même espace vectoriel = distances valides) ;
2. envoie une requête **k-NN** à OpenSearch sur le champ `embedding` (avec `_source` excluant `embedding` pour alléger la réponse) ;
3. renvoie les Top-K chunks nettoyés `{score, texte, source, page, chunk_index}`, déjà triés du plus proche au moins proche.

Testé sur 3 questions → passages pertinents remontés.

### 3. Concepts appris

- **Smoke test** : test minimal « est-ce que ça s'allume ? » avant de tester le détail.
- **Foundation model vs inference profile** : le modèle (cerveau) vs l'aiguilleur qui route la requête. Claude s'appelle via un inference profile (préfixe `us.`).
- **`us.` vs `global.`** : routage limité aux USA vs mondial → on garde `us.` (cohérence + maîtrise géographique).
- **API Converse** : format **unifié** de Bedrock ; réponse toujours structurée pareil, renvoie l'`usage` (tokens → coûts).
- **Modèle « Legacy »** : modèle en fin de vie, gelé par AWS.
- **Score k-NN OpenSearch** : score transformé (plus haut = plus proche), **pas un pourcentage** ; resserré ici car corpus minuscule et homogène (1 seul document).
- **Retrieval vs Génération** : le retrieval trouve les chunks bruts ; la génération (US 3.2) rédige la réponse claire et sourcée.

### 4. Prochaine étape

- [ ] **US 3.2** : génération de la réponse avec Claude (prompt = consignes + contexte + question) + garde-fous anti-hallucination (seuil de score, consignes « contexte uniquement / je ne sais pas », sources vérifiées).

---

## Sprint 3 — US 3.2 : Generation de la reponse (28/09/2026)

### 1. Objectif et resultat

Transformer les chunks bruts (US 3.1) en une reponse redigee, claire et sourcee, avec garde-fous anti-hallucination. **US 3.2 terminee**, testee de bout en bout sur les 2 cas (question pertinente + question hors sujet).

### 2. Code produit (module src/rag/, 3 briques)

- **prompt.py** (brique 1) : `construire_prompt(question, chunks)` -> dict {systeme, utilisateur}. Consignes strictes + contexte balise (<document source= page=>) + question. 100% texte, testable sans AWS.
- **generation.py** (brique 2) : `generer_reponse(prompt)` -> appelle Claude via l'API **Converse** (system + messages, temperature=0, maxTokens=800). Renvoie {reponse, tokens, arret}.
- **pipeline.py** (brique 3) : `repondre(question)` -> **orchestrateur**, porte d'entree UNIQUE du moteur RAG. Enchaine retrieval -> seuil -> prompt -> generation. Renvoie {reponse, sources, tokens, appel_llm}.

### 3. Decisions & concepts

- **Modele** : Claude Haiku 4.5 via inference profile `us.`, appele en **Converse** (format unifie Bedrock ; system separe des messages ; renvoie l'usage tokens).
- **Anti-hallucination = defense en profondeur (4 couches)** :
  1. temperature = 0 (fidelite, pas d'invention) ;
  2. consignes du prompt (contexte uniquement / sinon "Je ne trouve pas" / cite ses sources) ;
  3. sources construites a partir des **chunks reels** (pas du texte de Claude) ;
  4. seuil de score `SCORE_MIN` (.env, defaut 0.5) : sous le seuil, reponse d'absence SANS appeler Claude (economie + zero risque).
- **Score OpenSearch** : score transforme du cosinus (0.5 ~ aucun rapport, ->1 = proche), ce n'est PAS un pourcentage.

### 4. Tests reels

- « Quelle base vectorielle est utilisee ? » -> "Amazon OpenSearch Serverless" + [Source : ..., p.2] ; appel_llm=True.
- « Quelle est la capitale de l'Australie ? » -> "Je ne trouve pas cette information..." ; meilleur score 0.5275 (>= 0.5) donc le seuil (couche 4) n'a pas bloque -> c'est la couche 2 (prompt) qui a refuse. Illustration concrete de la defense en profondeur.
- Observation (rapport) : sur ce corpus minuscule et homogene, le seuil 0.5 ne coupe pas la question hors sujet (0.5275) ; a calibrer sur la vraie base (un seuil ~0.55 la couperait ici, au risque de faux refus -> valider sur donnees reelles).

### 5. Prochaine etape — cloture du Sprint 3

- [ ] Tests automatises (pytest, avec mocks : prompt sans AWS, retrieval/generation mockes).
- [ ] Doc finale + support de presentation du Sprint 3.
- [ ] (option) amorcer l'API FastAPI (transition vers le Sprint 4).

---

## Sprint 3 — Pistes d'amelioration & limites connues (28/09/2026)

Section "recul critique" pour le rapport / la soutenance : ce que le systeme fait
bien et comment le faire evoluer. Aucun de ces points n'est un bug -> ce sont des
choix assumes ou des ameliorations a calibrer sur la vraie base documentaire.

### Garde-fou & pertinence
- **Seuil global vs filtrage par chunk** : le garde-fou actuel teste seulement le
  MEILLEUR score (decision globale "faut-il repondre ?"). Les chunks faibles partent
  quand meme a Claude. Evolution possible : filtrer chunk par chunk (garder les
  chunks dont score >= SCORE_MIN ; s'il n'en reste aucun -> "Je ne trouve pas").
  Cela ferait le go/no-go ET le nettoyage du contexte en une logique.
  A calibrer sur corpus reel : sur le corpus de test, tous les scores sont entre
  0.5 et 0.63 -> un filtrage par chunk jetterait des passages utiles.
- **Calibration de SCORE_MIN** : fixe a 0.5 provisoirement. Sur corpus homogene, ne
  coupe pas toujours le hors-sujet (ex. 0.5275) -> c'est la couche 2 (consignes du
  prompt) qui rattrape. A re-regler sur la vraie base (scores mieux etales).
- **Reranking (avance)** : re-classer les Top-K avec un modele plus precis
  (cross-encoder) avant de les envoyer a Claude, pour affiner l'ordre et la pertinence.

### Generation
- **maxTokens = 800** : si stopReason = "max_tokens", la reponse a ete coupee ->
  surveiller et augmenter au besoin pour les questions complexes.
- **Cout** : le contexte (les chunks envoyes) domine les tokens d'entree. Leviers si
  le cout devient un enjeu : reduire k, ou reduire la taille des chunks.

### Corpus de test
- Corpus minuscule (2 documents, 7 chunks) et homogene -> scores resserres,
  evaluation du retrieval peu representative. A refaire sur la vraie base Smartovate.

### Vers le Sprint 4
- **Historique multi-tours** : Converse accepte une liste de messages
  (user/assistant) -> le chatbot pourra se souvenir des questions precedentes.

---

## Sprint 3 — Tests automatises (30/09/2026)

### 1. Objectif
Filet de securite (non-regression) : rejouer toute la logique du moteur RAG en
UNE commande (pytest), sans appeler AWS. **26 tests verts** (15 anciens + 11 nouveaux),
executes en ~1.7 s.

### 2. Concept cle : le mock (doublure)
Les fonctions du Sprint 3 appellent AWS (Titan, OpenSearch, Claude). Les appeler dans
les tests serait lent, payant, dependant du reseau/SSO et non reproductible. On remplace
donc AWS par une DOUBLURE (mock) qui imite ses reponses. Outil pytest : `monkeypatch`
(remplace temporairement une fonction, LA OU elle est utilisee). Deux usages du mock :
(a) DONNER une fausse reponse (tester ce que le code lit) ; (b) ESPIONNER l'appel
(tester ce que le code envoie).

### 3. Fichiers de tests (module rag/)
- **test_prompt.py** (4) : structure du prompt ; balises source/page ; nom de fichier
  sans URI S3 ; question presente. Aucun mock (pur texte).
- **test_retrieval.py** (2) : transformation de la reponse OpenSearch en chunks propres ;
  k bien transmis a la requete (espion).
- **test_generation.py** (2) : extraction des champs de la reponse Converse ; prompt bien
  place (system/messages) + temperature=0 (espion).
- **test_pipeline.py** (3) : SOUS le seuil -> pas d'appel Claude (garde-fou couche 4) ;
  AU-DESSUS -> Claude appele + sources construites ; aucun chunk -> reponse d'absence.

### 4. Resultat
`python -m pytest -v` -> **26 passed**. Le code du Sprint 3 est termine ET couvert par des tests.

### 5. Prochaine etape
- [ ] Bilan / cloture du Sprint 3 (journal) + support de presentation (.pptx).

---

## Sprint 4 — US 4.1 : API backend FastAPI (06/10/2026)

### 1. Objectif et résultat
« Emballer » le moteur RAG du Sprint 3 derrière une **URL HTTP**, pour qu'une interface
(Streamlit aujourd'hui, React demain) puisse l'interroger. L'API ne réinvente rien :
elle reçoit une question, appelle `repondre()` et renvoie le résultat en JSON.
**API fonctionnelle**, testée via la documentation interactive Swagger (`/docs`).

### 2. Code produit (module `src/api/`)
- **models.py** : contrats d'échange Pydantic — `Question` (question, k=5),
  `Source` (source, page, score), `Reponse` (reponse, sources, appel_llm).
- **main.py** :
  - `GET /health` → `{"status": "ok"}` (« es-tu en vie ? », utile au déploiement) ;
  - `POST /ask` → appelle `repondre()` ; `response_model=Reponse` garantit la forme de la sortie ;
  - middleware **CORS** (utile seulement pour un futur client navigateur type React).
- Lancement (depuis `src/`) : `uvicorn api.main:app --reload`.

### 3. Concepts appris
- **API / endpoint** : une « porte » HTTP (méthode + chemin) qui expose une fonction.
- **Pydantic** : valide automatiquement les données entrantes/sortantes (erreur 422 si invalide).
- **uvicorn** : le serveur (ASGI) qui fait tourner l'application FastAPI.
- **Décorateur** (`@app.get`, `@app.post`) : associe une fonction Python à une route.
- **CORS** : règle de sécurité des **navigateurs** ; ne concerne pas Streamlit (appel serveur → serveur).
- **Codes HTTP** : 200 OK, 404 route inexistante (ex. `/` ou `/favicon.ico`), 422 données invalides, 500 erreur serveur.

---

## Sprint 4 — US 4.1 : Interface chatbot Streamlit (09/10/2026)

### 1. Objectif et résultat
Interface web conversationnelle connectée à l'API, conforme au cahier (US 4.1) :
historique de la session, réponse de l'IA et sources affichées. **Interface terminée et validée.**

### 2. Code produit (module `src/frontend/` + `src/.streamlit/`)
- **api_client.py** : `poser_question()` (POST `/ask`) et `api_en_ligne()` (GET `/health`).
  L'URL de l'API vient de `.env` (`API_URL`) → changera au déploiement sans toucher au code.
- **app.py** : interface complète —
  - barre latérale : « Nouvelle conversation » + conversations récentes ;
  - en-tête « Smartovate AI Assistant » + badge d'état de l'API ;
  - écran d'accueil avec 3 suggestions de questions ;
  - bulles utilisateur (droite) / assistant (gauche), rendu Markdown (tableaux, code, listes) ;
  - bloc repliable « Sources utilisées » (document, page, score) ;
  - indicateur de chargement pendant l'appel.
- **.streamlit/config.toml** : thème clair (palette navy / gris clair / accent turquoise).
- Lancement (depuis `src/`) : `streamlit run frontend/app.py` (l'API doit tourner en parallèle).

### 3. Concepts appris
- **Modèle d'exécution Streamlit** : le script entier est **réexécuté** à chaque interaction.
- **`st.session_state`** : la mémoire qui survit aux réexécutions (historique, conversations).
- **`st.rerun()`** : relancer le script après le traitement pour rafraîchir toute la page.
- **Personnalisation CSS** via les `data-testid` des composants Streamlit.

### 4. Pièges rencontrés & résolus
- Titre de conversation « Nouvelle conversation » en double et cartes d'accueil persistantes :
  la barre latérale était dessinée **avant** la mise à jour du titre → lire la saisie **tôt**,
  traiter, puis `st.rerun()`.
- `ModuleNotFoundError: markdown` → `pip install markdown` dans l'environnement `rag-smartovate`.

---

## Sprint 4 — Diagnostic de la lenteur du chatbot + garde-fou des sources (11/10/2026)

### 1. Le symptôme
Le chatbot affichait « délai dépassé » : une question prenait de **30 à 180 s** via l'API,
alors que le même moteur répondait en quelques secondes en ligne de commande.
Lien avec le cahier des charges : **Bug 2 « Lenteur / Timeouts »** (Sprint 4).

### 2. La démarche : mesurer avant de corriger
| Étape | Outil | Ce qu'on a appris |
|---|---|---|
| 1 | Messages d'erreur distincts dans l'interface | c'est un **délai dépassé**, pas une API arrêtée |
| 2 | Logs dans l'API (`question recue` / `reponse prete en`) | une question = **91,5 s** |
| 3 | `faulthandler` (pile d'appels affichée toutes les 20 s) | le programme attend en **ouvrant les connexions réseau** (DNS, TCP), pas pendant le travail d'AWS |
| 4 | Test sans `--reload` | fausse piste (écarts dus au hasard) |
| 5 | Script de test réseau (temporaire) | certaines adresses AWS **ne répondent jamais** (abandon après ~21 s) sur la connexion utilisée |
| 6 | Changement de réseau | toutes les connexions < 0,5 s → **cause n°1 confirmée** |
| 7 | Chronomètre par étape (`durees`) | la **recherche** prend encore ~6,5 s au lieu de ~1 s |
| 8 | `@lru_cache` sur les clients AWS | recherche à **0,8 s** → **cause n°2 corrigée** |

### 3. Les deux causes
1. **Réseau** : pertes de paquets entre la connexion internet locale et AWS (Oregon).
   Pas un problème de code ; n'existera pas une fois l'API déployée dans AWS (App Runner).
2. **Code** : les clients AWS (sessions, identifiants SSO, connexions HTTPS) étaient **recréés
   à chaque question**. Sans impact dans les scripts des Sprints 1–3 (exécutés une fois),
   mais coûteux dans une API qui reste allumée.

### 4. Corrections apportées
- `rag/retrieval.py` : `_clients()` décorée par `@lru_cache` → clients Bedrock + OpenSearch créés
  **une seule fois** puis réutilisés. Idem `_client_claude()` dans `rag/generation.py`.
- `rag/pipeline.py` : `repondre()` renvoie `durees` (temps de recherche / génération) ;
  l'API l'affiche dans ses logs (utile aussi en production).
- `api/main.py` : diagnostic temporaire (`faulthandler`) retiré après résolution.
- **Résultat** : de 91–180 s à **2–5 s** par question. Seule la 1re question après le
  démarrage reste plus lente (**démarrage à froid** : création des clients).

### 5. Régression détectée par les tests (et corrigée)
Le cache gardait la **doublure** (faux client) du test précédent → 2 tests en échec.
Correction : `tests/conftest.py` avec une fixture `autouse` qui appelle `cache_clear()`
avant et après chaque test. Leçon : **toujours relancer toute la suite (`pytest`) avant un commit.**

### 6. Garde-fou : masquer les sources quand Claude ne trouve pas
- Constat : « Qui a gagné la coupe du monde en 2026 ? » → Claude répond correctement
  « Je ne trouve pas… » (**pas d'hallucination** : le prompt, couche 2, a fait son travail),
  mais l'interface affichait « Sources utilisées (5) » → trompeur.
- Pourquoi le seuil n'a pas filtré : score OpenSearch = 1 / (2 − cosinus) → **0,5 = cosinus 0
  = aucun rapport**. `SCORE_MIN=0.5` ne bloque donc quasiment rien.
- Option écartée : calibrer le seuil avec une liste de questions de test → dépend des documents
  de la base (à refaire à chaque changement de corpus).
- Option retenue (indépendante des documents) : `_est_absence()` dans `pipeline.py` — si la réponse
  **commence par** la phrase d'absence, `sources = []`. `appel_llm` reste `True`.
  ⚠️ `MESSAGE_ABSENCE` doit rester identique à la phrase imposée dans `prompt.py`.
- Nouveau test : `test_claude_ne_trouve_pas_masque_les_sources` → **27 tests verts**.

### 7. Concepts appris
- **`faulthandler`** : « photo » de la pile d'appels d'un programme bloqué.
- **DNS** (nom → adresse IP), **connexion TCP**, délai d'abandon Windows (~21 s), **perte de paquets**.
- **`uvicorn --reload`** : un processus surveillant + un processus « ouvrier » relancé à chaque
  modification ; pratique en développement, jamais en production.
- **`time.perf_counter()`** : chronomètre précis pour mesurer chaque étape.
- **`@lru_cache`** : mémorise le résultat d'une fonction ; **démarrage à froid**.
- **Fixture pytest** (`conftest.py`, `autouse=True`) : code exécuté autour de chaque test.
- **Défense en profondeur** : quand une couche laisse passer (seuil), la suivante rattrape (prompt).

### 8. Prochaine étape
- [ ] **US 4.2** : Docker (concepts puis Dockerfile), déploiement sur App Runner, README complet, PEP8.

---

## Sprint 4 — US 4.2 (1/2) : Conteneurisation Docker (12–14/10/2026)

### 1. Objectif et résultat
Emballer toute l'application (API + interface) dans une **image Docker** reproductible : première
étape du déploiement demandé par le cahier (US 4.2). **Image construite et validée en local** :
interface sur `localhost:8501`, 3 questions répondues (`POST /ask 200`), API invisible de l'extérieur
(`localhost:8000/docs` → connexion refusée, comme voulu).

### 2. Fichiers produits
- `requirements.txt` : versions figées en `==` (reproductibilité) — commit `2148afa`.
- `Dockerfile` : base `python:3.11-slim`, dépendances d'abord (étape gardée en cache), puis `src/` ;
  le `CMD` lance l'API en arrière-plan sur `127.0.0.1:8000` et Streamlit au premier plan sur
  `0.0.0.0:8501` — commit `ce978b6`.
- `.dockerignore` : exclut les secrets (`.env`, `.env.docker`), `.git`, `data/`, `docs/`, `infra/`, `tests/`.
- `.env.docker` (non versionné) : copie de `.env` **sans `AWS_PROFILE`** — commits `d7e0843`, `64e2af0`.

### 3. Décisions
- **Un seul conteneur** (API + Streamlit) : plus simple à déployer pour un PoC.
  Deux conteneurs = piste d'évolution (isolation, moindre privilège, redémarrage indépendant).
- **API privée** (`127.0.0.1`) / **Streamlit public** (`0.0.0.0`) : seule l'interface est exposée.
- **Pas d'`AWS_PROFILE` dans le conteneur** : sans dossier `.aws`, la variable provoque `ProfileNotFound` ;
  absente, boto3 suit sa chaîne d'identifiants (variables d'environnement en local, rôle IAM en production).

### 4. Mesures
| Mesure | Valeur |
|---|---|
| Taille de l'image | 1,05 Go sur disque / 251 Mo compressée |
| Build initial / rebuild grâce au cache | 98 s / 0,8 s |
| Recherche : 1re question (à froid) / suivantes | 4,3 s / 1,7 s |
| RAM du conteneur au repos (`docker stats`) | 124 MiB (sur 15 Go disponibles) |

### 5. Concepts appris
- **Image** (le modèle figé) vs **conteneur** (l'image en marche) ; **Dockerfile** (la recette).
- **Couches et cache** : l'ordre des instructions décide de ce qui est reconstruit.
- **Contexte de build** et **`.dockerignore`** (ne jamais envoyer de secret dans une image).
- **`127.0.0.1` vs `0.0.0.0`**, ports (`-p`), variables (`--env-file`, `-e`), `-d`, `--rm`, `--name`.
- `docker ps / logs / stop / stats`, codes de sortie.
- **RAM ≠ taille de l'image** : l'image est sur le disque, seule la partie utilisée est chargée en mémoire.

### 6. Pièges rencontrés & résolus
- `ProfileNotFound` à la 1re question avec `AWS_PROFILE=smartovate` ou `AWS_PROFILE=` (vide)
  → **supprimer la ligne**, ne pas la laisser vide.
- 16/10 : erreur 500 malgré `aws sso login` → le conteneur garde une **copie** des clés temporaires,
  qui expirent. Il faut réexporter les clés (`aws configure export-credentials --profile smartovate
  --format powershell | Invoke-Expression`) puis relancer le conteneur, dans un **terminal dédié**
  (ces variables masquent le profil SSO pour uvicorn en local). En production, le **task role** supprime ce problème.

---

## Sprint 4 — US 4.2 (2/2) : Déploiement sur Amazon ECS Fargate (14–17/10/2026)

### 1. Objectif et résultat
Mettre l'application en ligne dans AWS, entièrement décrite en code (CDK), conformément au cahier
(« déployée sur Amazon ECS »). **Déployée le 17/10/2026** : le chatbot répond via l'URL publique de
l'ALB, avec une réponse sourcée de Claude servie entièrement depuis AWS (5 sources, scores 0,55–0,63).

### 2. Choix de la plateforme
| Option | Verdict | Raison |
|---|---|---|
| App Runner | ❌ | fermé aux nouveaux clients et **ne supporte pas les WebSockets entrants** (Streamlit en dépend) |
| ECS Express Mode | ❌ | CDK uniquement en L1, ressources gérées hors CloudFormation |
| EC2 + `docker run` | ❌ (plan B) | non conforme au cahier (« ECS »), maintenance du serveur à notre charge |
| **ECS sur Fargate, construct CDK L3 `ApplicationLoadBalancedFargateService`** | ✅ | conforme, aucun serveur à gérer, tout en CloudFormation, ALB compatible WebSocket |

### 3. Architecture déployée
```
Navigateur --HTTP:80--> ALB (vigile : IP autorisées uniquement)
                          |
                          v  port 8501 (vigile : uniquement depuis l'ALB)
                   Tâche Fargate 0,5 vCPU / 1 Go
                     |- Streamlit 0.0.0.0:8501
                     '- API FastAPI 127.0.0.1:8000 --task role--> Bedrock (Titan + Claude) / OpenSearch
VPC dédié 10.0.0.0/16 · 2 zones · sous-réseaux publics · 0 NAT · image dans ECR · logs CloudWatch
```

### 4. Code produit (`infra/`)
- `infra/infra/ecs_stack.py` (nouvelle pile `SmartovateRagEcsStack`, 8 blocs commentés) : configuration
  (`ALLOWED_IPS`, variables lues dans `.env.docker`) ; VPC ; cluster ; **task role**
  `smartovate-rag-mohamed-task-role` (Bedrock + OpenSearch sur des ressources précises) ; groupe de
  sécurité + ALB ; service Fargate (image construite par CDK, disjoncteur, déploiement sans coupure) ;
  health check `/_stcore/health` ; sortie `TaskRoleArn`.
- `infra/infra/infra_stack.py` : la data access policy OpenSearch autorise aussi le task role
  (nom importé depuis `ecs_stack.py` : une seule source de vérité).
- `infra/cdk.json` (bootstrap dédié `smartmoh`), `infra/app.py` (déclaration de la pile),
  `infra/.env.example` (nouveau), `infra/cdk.context.json`.
- Commits : `bb659d7`, `12410af`, `9e65598`, `1d69118`.

### 5. Démarche
1. **8 notions expliquées avant tout code** : ECR, Fargate, task definition / tâche / service / cluster,
   execution role vs task role, VPC / sous-réseaux / NAT, groupes de sécurité, ALB / target group /
   health check, bootstrap / assets.
2. **Diagnostic en lecture seule** du compte (bootstrap, piles existantes) avant toute modification.
3. **Pile écrite bloc par bloc**, puis `cdk synth` et vérification du modèle généré
   (aucun secret dans le contexte de l'image, aucune NAT, règles réseau attendues).
4. `cdk deploy` : 30 ressources en ~5 min ; CloudFormation attend que la tâche soit déclarée saine.
5. Test, lecture des logs CloudWatch, correction, nouveau test.

### 6. Pièges rencontrés & résolus (matière pour le rapport)
| # | Symptôme | Cause | Résolution |
|---|---|---|---|
| 1 | `cdk deploy` impossible depuis le Sprint 2 | bucket du bootstrap CDK **partagé** supprimé par le sandbox (dérive) ; d'autres projets dépendent de ce bootstrap | **bootstrap dédié** `--qualifier smartmoh` (pile `CDKToolkit-Mohamed`), branché dans `cdk.json` |
| 2 | avertissement « not tested with node v26 » | Node 26 (non LTS) installé dans l'env conda | `conda install -c conda-forge "nodejs=24"` |
| 3 | `ENOTEMPTY ... jsii-kernel` en fin de commande | nettoyage d'un dossier temporaire sous Windows | sans conséquence, ignoré |
| 4 | `Invalid request provided` + rollback au redéploiement de la pile OpenSearch | OpenSearch refuse une policy **identique** à l'existante | réalignement fait lors de la modification réelle suivante |
| 5 | `Early validation failed : smartovate-rag-task-role already exists` | rôle du même nom laissé par un projet précédent | noms suffixés `-mohamed` (rôle, cluster, service) ; aucune ressource créée grâce à la validation anticipée |
| 6 | page OK mais question → erreur 500 | **403 OpenSearch** lu dans CloudWatch (`aws logs tail`) : task role absent de la data access policy (double verrou IAM + policy) | task role ajouté à la policy (`infra_stack.py`) → réponse sourcée |

### 7. Concepts appris
- **ECS** (orchestrateur) et **Fargate** (exécution sans serveur à gérer) ; task definition, tâche,
  service, cluster ; disjoncteur de déploiement et déploiement sans coupure (100 % / 200 %).
- **Execution role** (préparer la tâche : ECR, logs) vs **task role** (le code : Bedrock, OpenSearch) ;
  identifiants fournis et renouvelés automatiquement ; **moindre privilège**.
- **VPC**, sous-réseaux publics / privés, Internet Gateway, NAT Gateway (coût), zones de disponibilité.
- **Groupes de sécurité** : liste blanche, *stateful*, source = autre groupe ; `/32` vs `0.0.0.0/0`.
- **ALB**, listener, target group, health check ; lire les symptômes (délai dépassé = vigile,
  502/503 = aucune cible saine, erreur à la question = permissions).
- **CDK** : bootstrap, qualificatif, assets et empreinte, `cdk synth / diff / deploy / destroy` ;
  **CloudFormation** : change set, rollback, validation anticipée, dérive (*drift*).
- **CloudWatch Logs** : `aws logs tail`, lire un traceback de bas en haut.

### 8. Coût, limites et pistes
- Coût estimé ~1,2 $/jour (ALB + Fargate) tant que la pile existe → `cdk destroy SmartovateRagEcsStack`
  après les tests ; redéploiement en ~5 min grâce à l'infrastructure en code.
- Limites : HTTP sans HTTPS ; le health check ne teste que Streamlit (pas l'API en arrière-plan) ;
  historique perdu si la tâche est remplacée (pas de base de données) ; tâches en sous-réseaux publics
  (choix de coût).
- Pistes : HTTPS (nom de domaine + certificat ACM), sous-réseaux privés + NAT ou VPC endpoints,
  ALB interne + VPN (outil interne), 2 conteneurs, health check couvrant l'API, alerte budget AWS.

### 9. Prochaine étape
- [ ] Captures pour le rapport (console ECS, target group, CloudWatch, CloudFormation), puis `cdk destroy`.
- [ ] Passe `ruff` / PEP8, rapport final de stage, support de présentation.
