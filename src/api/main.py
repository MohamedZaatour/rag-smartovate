# ============================================================
#  Sprint 4 / US 4.1 - API backend (FastAPI)
#  Role : EMBALLER le moteur RAG (repondre) derriere une URL HTTP.
#  L'API ne reinvente rien : elle recoit une question, appelle
#  repondre() (Sprint 3), et renvoie le resultat en JSON.
#  Lancement (depuis src/) :  uvicorn api.main:app --reload
#  Doc interactive :          http://localhost:8000/docs
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import Question, Reponse
from rag.pipeline import repondre   # le moteur complet du Sprint 3

app = FastAPI(title="Smartovate RAG API", version="1.0")

# --- CORS ---
# Utile SI un jour un client NAVIGATEUR (ex: React) appelle l'API.
# Avec Streamlit, l'appel part du serveur Python (via requests), donc
# CORS ne se declenche pas ; on le laisse pour les futurs clients web.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # en PROD : restreindre a l'URL du front
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Petit endpoint 'es-tu en vie ?' - tres utile au deploiement."""
    return {"status": "ok"}


@app.post("/ask", response_model=Reponse)
def ask(q: Question):
    """Recoit une question, interroge le moteur RAG, renvoie la reponse.

    response_model=Reponse => FastAPI garantit que la sortie a bien la
    forme attendue (reponse + sources + appel_llm) et la serialise en JSON.
    """
    return repondre(q.question, k=q.k)
