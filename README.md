# Systeme RAG - Smartovate

Systeme de Retrieval-Augmented Generation (RAG) interne permettant d'interroger
la base de connaissances de l'entreprise en langage naturel.

**Stack :** Python, FastAPI, LangChain, Amazon Bedrock (Claude 3 + Titan Embeddings),
Amazon OpenSearch Serverless.

## Structure du projet

```
02-Developpement/
├── src/
│   └── ingestion/     # Sprint 1 : extraction, nettoyage, chunking, embeddings
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

## Avancement

- [x] Sprint 1 : Ingestion & traitement des donnees (US 1.1 + US 1.2)
- [ ] Sprint 2 : Base vectorielle OpenSearch
- [ ] Sprint 3 : Moteur RAG (retrieval + generation)
- [ ] Sprint 4 : Interface chatbot, deploiement & documentation

---
_Projet de stage - Mohamed Zaatour_
