# ============================================================
#  Image Docker - Systeme RAG Smartovate (US 4.2)
#  Un seul conteneur : API FastAPI (privee) + interface Streamlit (publique)
# ============================================================

# 1. Point de depart : Linux minimal + Python 3.11 (meme version que l'env conda)
FROM python:3.11-slim

# 2. Afficher les messages Python immediatement (logs visibles tout de suite, rien de perdu en cas de plantage)
ENV PYTHONUNBUFFERED=1

# 3. Dossier de travail dans l'image (equivalent de "cd /app")
WORKDIR /app

# 4. D'ABORD les dependances : elles changent rarement -> etape gardee en cache par Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. ENSUITE le code : il change souvent -> seule cette etape est refaite apres une modification
COPY src/ ./src/

# 6. Se placer dans src/ (imports "rag.xxx", "api.xxx" + theme .streamlit/config.toml)
WORKDIR /app/src

# 7. Documentation : l'appli est servie sur le port 8501 (Streamlit). L'API (8000) reste interne.
EXPOSE 8501

# 8. Au DEMARRAGE du conteneur (docker run), pas pendant docker build :
#    - l'API en arriere-plan (&), ecoute sur 127.0.0.1 -> privee, seul Streamlit peut l'appeler
#    - Streamlit au premier plan (exec), ecoute sur 0.0.0.0 -> accessible de l'exterieur
#    - headless : pas d'ouverture de navigateur (il n'y a pas d'ecran dans un conteneur)
CMD ["sh", "-c", "uvicorn api.main:app --host 127.0.0.1 --port 8000 & exec streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true"]
