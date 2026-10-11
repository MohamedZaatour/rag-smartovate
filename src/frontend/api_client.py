# ============================================================
#  Sprint 4 / US 4.1 - Client de l'API (cote interface)
#  - poser_question : envoie une question a /ask
#  - api_en_ligne   : verifie que l'API repond (/health)
# ============================================================

import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")


def poser_question(question, k=5, timeout=120):
    """Envoie la question a l'API (POST /ask) et renvoie le resultat (dict).

    timeout=120 : marge pour la recherche + la generation (Claude).
    Erreurs possibles (gerees par l'interface) :
      - requests.Timeout         -> l'API met trop de temps a repondre
      - requests.ConnectionError -> l'API est injoignable (uvicorn arrete)
      - requests.HTTPError       -> l'API a repondu par une erreur (ex. 500)
    """
    reponse = requests.post(
        f"{API_URL}/ask",
        json={"question": question, "k": k},
        timeout=timeout,
    )
    reponse.raise_for_status()
    return reponse.json()


def api_en_ligne(timeout=3):
    """Renvoie True si l'API repond sur /health, False sinon."""
    try:
        reponse = requests.get(f"{API_URL}/health", timeout=timeout)
        return reponse.status_code == 200
    except requests.RequestException:
        return False


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Quelle base vectorielle est utilisee ?"
    resultat = poser_question(q)
    print("REPONSE  :", resultat["reponse"])
    print("APPEL LLM:", resultat["appel_llm"])
    for s in resultat["sources"]:
        print(f"   - {s['source']}  p.{s['page']}  (score {s['score']})")
