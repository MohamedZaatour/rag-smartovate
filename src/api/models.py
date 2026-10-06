# ============================================================
#  Sprint 4 / US 4.1 - Schemas Pydantic de l'API
#  Pydantic decrit la FORME des donnees : FastAPI valide alors
#  automatiquement ce qui entre (la question) et ce qui sort
#  (la reponse), sans aucun "if" de verification a ecrire.
# ============================================================

from pydantic import BaseModel


class Question(BaseModel):
    """Ce que le client ENVOIE sur /ask."""
    question: str          # obligatoire : le texte de la question
    k: int = 5             # optionnel : nombre de chunks a recuperer (defaut 5)


class Source(BaseModel):
    """Une source citee (construite a partir des chunks reels)."""
    source: str
    page: int | None = None
    score: float | None = None


class Reponse(BaseModel):
    """Ce que l'API RENVOIE : la structure exacte attendue par le front."""
    reponse: str
    sources: list[Source] = []
    appel_llm: bool
