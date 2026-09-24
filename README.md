# Systeme RAG - Smartovate

Systeme de Retrieval-Augmented Generation (RAG) interne permettant d'interroger
la base de connaissances de l'entreprise en langage naturel.

**Stack :** Python, FastAPI, LangChain, Amazon Bedrock (Claude Haiku 4.5 + Titan Embeddings),
Amazon OpenSearch Serverless. Infrastructure en IaC via AWS CDK.

## Structure du projet

```
02-Developpement/
├── src/
│   ├── ingestion/     # Sprint 1 : extraction, nettoyage, chunking, embeddings
│   ├── indexation/    # Sprint 2 : index k-NN OpenSearch + indexation (bulk)
│   └── rag/           # Sprint 3 : recherche semantique + generation
├── infra/             # Sprint 2 : infrastructure AWS en CDK (OpenSearch Serverless)
├── data/
│   ├── raw/           # Documents bruts de test (PDF, Word) - local uniquement
│   └── processed/     # Sorties intermediaires
├── tests/             # Tests unitaires
├── requirements.txt   # Dependances Python
└── .gitignore
```

## Installation

```bash
conda create -n rag-smartovate python=3.11
conda activate rag-smartovate
pip install -r requirements.txt
```

### Infrastructure (CDK)

```bash
cd infra
pip install -r requirements.txt      # aws-cdk-lib, constructs, python-dotenv
cdk synth                            # apercu du plan CloudFormation
cdk deploy --profile smartovate      # deploiement sur AWS
```

> La configuration de l'infra (nom de collection, ARN du role) se trouve dans
> `infra/.env` (non versionne). Voir `infra/.env.example` pour le modele.

## Avancement

- [x] **Sprint 1 : Ingestion & traitement des donnees** (US 1.1 + US 1.2)
  - [x] US 1.1 : extraction & nettoyage du texte (PDF, Word) depuis S3
  - [x] US 1.2 : chunking + embeddings (Titan, dimension 1024)
- [x] **Sprint 2 : Base vectorielle OpenSearch** — TERMINÉ
  - [x] US 2.1 : provisionnement de la collection OpenSearch Serverless en CDK
  - [x] US 2.2 : creation de l'index + mapping k-NN (dimension 1024)
  - [x] US 2.3 : indexation des chunks vectorises (bulk insert)
  - > Correspondance cahier des charges : US 2.1 du cahier (config Serverless) = nos US 2.1 + 2.2 ; US 2.2 du cahier (indexation) = notre US 2.3. La recherche semantique est US 3.1 (Sprint 3).
- [ ] **Sprint 3 : Moteur RAG**
  - [x] US 3.1 : recherche semantique (retrieval k-NN) — question -> vecteur Titan -> Top-K chunks
  - [ ] US 3.2 : generation de la reponse (Bedrock / Claude Haiku 4.5) + garde-fous anti-hallucination
  - > Note modele : le cahier prevoyait Claude 3, classe "Legacy" par AWS (acces bloque). Substitution documentee vers Claude Haiku 4.5 (equivalent actif, meme role). ID externalise dans `.env`.
- [ ] Sprint 4 : Interface chatbot, deploiement & documentation

---
_Projet de stage - Mohamed Zaatour_
