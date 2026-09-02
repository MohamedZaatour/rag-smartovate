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
