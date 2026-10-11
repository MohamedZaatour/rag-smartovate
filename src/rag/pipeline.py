# ============================================================
#  US 3.2 - Brique 3 : Orchestrateur du moteur RAG
#  UNE seule porte d'entree : repondre(question)
#  Enchaine : retrieval (US 3.1) -> seuil de score (garde-fou couche 4)
#             -> prompt (brique 1) -> generation (brique 2).
#  C'est le "contrat" qu'utiliseront l'API et le chatbot du Sprint 4.
#  Lancement (depuis src/) :  python -m rag.pipeline "ta question ?"
# ============================================================

import os
import time

from dotenv import load_dotenv

from rag.generation import generer_reponse
from rag.prompt import construire_prompt
from rag.retrieval import rechercher_chunks

# Message unique quand l'info n'est pas disponible (coherent avec le prompt).
MESSAGE_ABSENCE = "Je ne trouve pas cette information dans la base documentaire."

# Seuil de pertinence par defaut (surcharge par .env). En dessous, on ne
# derange meme pas Claude : reponse d'absence directe (zero cout, zero risque).
SCORE_MIN_DEFAUT = 0.5


def _sources_depuis_chunks(chunks):
    """Construit la liste des sources A PARTIR DES CHUNKS reels (et non du
    texte de Claude) -> les sources affichees sont garanties fiables."""
    sources = []
    for c in chunks:
        sources.append({
            "source": str(c.get("source", "")).split("/")[-1],
            "page": c.get("page"),
            "score": round(c.get("score", 0), 4),
        })
    return sources


def repondre(question, k=5):
    """Point d'entree UNIQUE du moteur RAG.

    Renvoie un dict : {reponse, sources, tokens, appel_llm, durees}.
    'durees' = temps (en secondes) de chaque etape -> pour reperer la lente.
    """
    load_dotenv()
    score_min = float(os.getenv("SCORE_MIN", SCORE_MIN_DEFAUT))
    durees = {}

    # [1] Recherche semantique (US 3.1)
    debut = time.perf_counter()
    chunks = rechercher_chunks(question, k=k)
    durees["recherche"] = round(time.perf_counter() - debut, 2)

    # [2] Garde-fou (couche 4) : le meilleur chunk est-il assez pertinent ?
    #     Les chunks sont deja tries -> le meilleur score est celui du 1er.
    meilleur_score = chunks[0]["score"] if chunks else 0
    if not chunks or meilleur_score < score_min:
        return {
            "reponse": MESSAGE_ABSENCE,
            "sources": [],
            "tokens": None,
            "appel_llm": False,     # Claude n'a PAS ete appele (economie + zero risque)
            "durees": durees,
        }

    # [3] Construction du prompt (brique 1)
    prompt = construire_prompt(question, chunks)

    # [4] Generation de la reponse (brique 2)
    debut = time.perf_counter()
    resultat = generer_reponse(prompt)
    durees["generation"] = round(time.perf_counter() - debut, 2)

    return {
        "reponse": resultat["reponse"],
        "sources": _sources_depuis_chunks(chunks),
        "tokens": resultat["tokens"],
        "appel_llm": True,
        "durees": durees,
    }


# --- Test : python -m rag.pipeline "ma question ?" ---
if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quelle base vectorielle est utilisee ?"

    print(f"Question : {question}")
    print("-" * 55)

    res = repondre(question)

    print("\nREPONSE :\n")
    print(res["reponse"])

    print("\n" + "-" * 55)
    print(f"Claude appele : {res['appel_llm']}")
    if res["sources"]:
        print("Sources :")
        for s in res["sources"]:
            print(f"   - {s['source']} p.{s['page']}  (score {s['score']})")
    if res["tokens"]:
        print(f"Tokens : {res['tokens']}")
    print(f"Durees : {res['durees']}")
