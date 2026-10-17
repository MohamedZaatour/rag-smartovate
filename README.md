# Systeme RAG - Smartovate

Systeme de Retrieval-Augmented Generation (RAG) interne permettant d'interroger
la base de connaissances de l'entreprise en langage naturel.

**Stack :** Python, FastAPI, Streamlit, Amazon Bedrock (Claude Haiku 4.5 + Titan Embeddings),
Amazon OpenSearch Serverless (acces direct via boto3 + opensearch-py, sans framework de type LangChain).
Conteneurisation Docker, deploiement sur **Amazon ECS (Fargate)**. Infrastructure en IaC via **AWS CDK** (Python).

## Structure du projet

```
02-Developpement/
├── src/
│   ├── ingestion/     # Sprint 1 : extraction, nettoyage, chunking, embeddings
│   ├── indexation/    # Sprint 2 : index k-NN OpenSearch + indexation (bulk)
│   ├── rag/           # Sprint 3 : recherche semantique + generation
│   ├── api/           # Sprint 4 : API backend FastAPI (/ask, /health)
│   ├── frontend/      # Sprint 4 : interface chatbot Streamlit
│   └── .streamlit/    # Sprint 4 : theme de l'interface
├── infra/             # Infrastructure AWS en CDK :
│   │                  #   - SmartovateRagStack    : OpenSearch Serverless (Sprint 2)
│   │                  #   - SmartovateRagEcsStack : application sur ECS Fargate + ALB (Sprint 4)
├── data/
│   ├── raw/           # Documents bruts de test (PDF, Word) - local uniquement
│   └── processed/     # Sorties intermediaires
├── tests/             # Tests unitaires
├── Dockerfile         # Image unique : API (privee) + interface Streamlit (publique)
├── .dockerignore      # Fichiers exclus de l'image (secrets, donnees, infra, tests)
├── .env.example       # Modele de configuration de l'application
├── requirements.txt   # Dependances Python (versions figees)
└── .gitignore
```

## Installation

```bash
conda create -n rag-smartovate python=3.11
conda activate rag-smartovate
pip install -r requirements.txt
```

## Lancer le chatbot en local

Prerequis : environnement `rag-smartovate` active, fichier `.env` rempli
(voir `.env.example`) et session AWS ouverte.

```bash
aws sso login --profile smartovate

# Terminal 1 - l'API (depuis src/)
uvicorn api.main:app --reload        # doc interactive : http://localhost:8000/docs

# Terminal 2 - l'interface (depuis src/)
streamlit run frontend/app.py        # ouvre http://localhost:8501
```

> La 1re question apres le demarrage de l'API est plus lente (creation des clients AWS) ;
> les suivantes repondent en quelques secondes.

## Lancer avec Docker (local)

Prerequis : Docker Desktop lance, fichier `.env.docker` = copie de `.env` **sans la ligne
`AWS_PROFILE`** (le conteneur n'a pas de dossier `.aws`).

```powershell
# depuis 02-Developpement/
docker build -t rag-smartovate:1.0 .

# dans un terminal DEDIE (les variables ci-dessous masquent le profil SSO)
aws sso login --profile smartovate
aws configure export-credentials --profile smartovate --format powershell | Invoke-Expression
docker run -d --rm --name rag -p 8501:8501 --env-file .env.docker `
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN rag-smartovate:1.0
```

Interface : http://localhost:8501 - logs : `docker logs rag` - arret : `docker stop rag`.

> Les cles copiees dans le conteneur sont **temporaires** : apres leur expiration (erreur 500),
> refaire `export-credentials` puis relancer le conteneur. En production, le role IAM de la tache
> fournit des identifiants renouveles automatiquement.

## Deploiement sur AWS (CDK + ECS Fargate)

### Architecture

```
Navigateur --HTTP:80--> ALB (acces limite aux IP de ALLOWED_IPS)
                          |
                          v  port 8501 (uniquement depuis l'ALB)
                   Tache Fargate 0,5 vCPU / 1 Go  (task role : Bedrock + OpenSearch, sans cle)
                     |- Streamlit 0.0.0.0:8501
                     '- API FastAPI 127.0.0.1:8000 --> Bedrock (Titan + Claude) / OpenSearch Serverless
VPC dedie (2 zones, sous-reseaux publics, sans NAT) - image dans ECR - logs dans CloudWatch
```

### Prerequis (une seule fois)

- Docker Desktop lance (CDK construit l'image), Node.js **22 ou 24 LTS**, CLI CDK (`npm install -g aws-cdk`).
- Dependances de l'infra : `pip install -r infra/requirements.txt` (aws-cdk-lib, constructs, python-dotenv).
- `infra/.env` rempli a partir de `infra/.env.example` (collection, ARN du role SSO **avec son chemin**,
  `ALLOWED_IPS`). Trouver son IP : `(Invoke-RestMethod https://checkip.amazonaws.com).Trim()`.
- `.env.docker` present a la racine : ce sont les variables transmises au conteneur.
- **Bootstrap CDK dedie** (le qualificatif `smartmoh` est declare dans `infra/cdk.json`) :

```powershell
# hors du dossier infra/
cdk bootstrap aws://<compte>/us-west-2 --profile smartovate --qualifier smartmoh --toolkit-stack-name CDKToolkit-Mohamed
```

### Deployer (depuis infra/)

```powershell
aws sso login --profile smartovate
cdk diff SmartovateRagStack --profile smartovate        # verifier avant de deployer
cdk deploy SmartovateRagStack --profile smartovate      # base vectorielle OpenSearch
cdk deploy SmartovateRagEcsStack --profile smartovate   # application sur ECS Fargate (~5 min)
```

- L'adresse du chatbot s'affiche a la fin (`ServiceURL`), ou dans la console :
  CloudFormation > `SmartovateRagEcsStack` > Outputs.
- La data access policy OpenSearch autorise le role SSO **et** le task role du conteneur
  (`smartovate-rag-mohamed-task-role`). Apres un premier deploiement, attendre ~1 min
  (propagation OpenSearch) avant de tester.

### Diagnostiquer

```powershell
aws logs describe-log-groups --log-group-name-prefix SmartovateRagEcsStack --region us-west-2 --profile smartovate --query "logGroups[].logGroupName" --output text
aws logs tail <nom-du-groupe> --since 15m --region us-west-2 --profile smartovate
```

| Symptome dans le navigateur | Cause probable |
|---|---|
| La page tourne puis "delai depasse" | IP non autorisee (ou IP changee) : mettre a jour `ALLOWED_IPS` puis `cdk deploy` |
| 502 / 503 | aucune tache saine : evenements du service ECS + logs |
| Page OK, erreur a la question | permissions (task role, data access policy OpenSearch) : voir les logs |

### Arreter (cout)

L'ALB et la tache Fargate sont factures a l'heure (~1,2 $/jour), meme sans visiteur.

```powershell
cdk destroy SmartovateRagEcsStack --profile smartovate
```

> **Ne jamais detruire `SmartovateRagStack`** : elle contient la base vectorielle OpenSearch.
> L'application se redeploie en ~5 min avec `cdk deploy SmartovateRagEcsStack`.

## Tests

```bash
pytest          # depuis 02-Developpement/ - aucun appel AWS (doublures)
```

## Avancement

- [x] **Sprint 1 : Ingestion & traitement des donnees** (US 1.1 + US 1.2)
  - [x] US 1.1 : extraction & nettoyage du texte (PDF, Word) depuis S3
  - [x] US 1.2 : chunking + embeddings (Titan, dimension 1024)
- [x] **Sprint 2 : Base vectorielle OpenSearch** — TERMINÉ
  - [x] US 2.1 : provisionnement de la collection OpenSearch Serverless en CDK
  - [x] US 2.2 : creation de l'index + mapping k-NN (dimension 1024)
  - [x] US 2.3 : indexation des chunks vectorises (bulk insert)
  - > Correspondance cahier des charges : US 2.1 du cahier (config Serverless) = nos US 2.1 + 2.2 ; US 2.2 du cahier (indexation) = notre US 2.3. La recherche semantique est US 3.1 (Sprint 3).
- [x] **Sprint 3 : Moteur RAG** — code termine (US 3.1 + US 3.2)
  - [x] US 3.1 : recherche semantique (retrieval k-NN) — question -> vecteur Titan -> Top-K chunks
  - [x] US 3.2 : generation de la reponse (Claude Haiku 4.5) + garde-fous anti-hallucination (seuil + consignes + sources)
  - [x] Tests automatises (pytest) : 26 tests verts (15 Sprint 1 + 11 Sprint 3) — 27 depuis le Sprint 4
  - > Note modele : le cahier prevoyait Claude 3, classe "Legacy" par AWS (acces bloque). Substitution documentee vers Claude Haiku 4.5 (equivalent actif, meme role). ID externalise dans `.env`.
- [ ] **Sprint 4 : Interface chatbot, deploiement & documentation** — en cours
  - [x] US 4.1 : API FastAPI (`/ask`, `/health`) + interface chatbot Streamlit
    (historique de session, conversations, sources affichees)
  - [x] Performance : clients AWS reutilises (`lru_cache`) -> 2 a 5 s par question
  - [x] Garde-fou : sources masquees quand l'information n'est pas dans la base
  - [x] US 4.2 : conteneurisation Docker (image unique API + interface)
  - [x] US 4.2 : deploiement sur Amazon ECS Fargate en CDK (ALB, task role dedie, acces limite par IP)
    - > Plateforme : App Runner ecarte (pas de WebSockets, indispensables a Streamlit) -> ECS Fargate, conforme au cahier.
  - [x] US 4.2 : README (installation, Docker, deploiement)
  - [ ] US 4.2 : passe PEP8 (ruff)

---
_Projet de stage - Mohamed Zaatour_
