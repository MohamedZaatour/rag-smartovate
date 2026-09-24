# ============================================================
#  US 3.1 - Recherche semantique (Retrieval) --- la moitie "R" du RAG
#  Question (texte) -> vecteur (Titan) -> requete k-NN OpenSearch
#  -> Top-K chunks les plus proches (avec texte, source et score).
#  Lancement (depuis src/) :  python -m rag.retrieval "ta question ?"
# ============================================================

import os

from dotenv import load_dotenv

# On REUTILISE les briques deja construites et validees aux sprints precedents.
from indexation.client import creer_client_opensearch                     # Sprint 2
from ingestion.embeddings import creer_client_bedrock, generer_embedding  # Sprint 1

# Le "K" de Top-K : combien de chunks on rapporte par defaut.
K_PAR_DEFAUT = 5


def rechercher_chunks(question, k=K_PAR_DEFAUT):
    """Retrouve les k chunks les plus proches SEMANTIQUEMENT de la question.

    Renvoie une liste de dictionnaires, du plus pertinent au moins pertinent :
        {"score", "texte", "source", "page", "chunk_index"}
    """
    load_dotenv()

    # --- 1) Vectoriser la QUESTION, avec le MEME modele que les chunks ---
    #     Indispensable : question et chunks doivent vivre dans le meme espace
    #     vectoriel, sinon la notion de "distance" n'a aucun sens.
    client_bedrock = creer_client_bedrock(os.getenv("AWS_PROFILE"), os.getenv("AWS_REGION"))
    vecteur_question = generer_embedding(client_bedrock, question)

    # --- 2) Se connecter a la collection OpenSearch (client du Sprint 2) ---
    client_os = creer_client_opensearch(
        os.getenv("OPENSEARCH_ENDPOINT"),
        os.getenv("AWS_REGION"),
        os.getenv("AWS_PROFILE"),
    )
    nom_index = os.getenv("INDEX_NAME", "smartovate-chunks")

    # --- 3) Construire la requete k-NN (plus proches voisins) ---
    corps = {
        "size": k,                     # nombre de resultats souhaites
        "query": {
            "knn": {                   # type de recherche : k-NN vectoriel
                "embedding": {         # sur NOTRE champ vecteur
                    "vector": vecteur_question,
                    "k": k,
                }
            }
        },
        # On EXCLUT 'embedding' de la reponse : inutile de rapatrier 1024
        # nombres par chunk (plus leger, plus rapide, anti-timeout).
        "_source": {"excludes": ["embedding"]},
    }

    # --- 4) Envoyer la requete ; recuperer la liste des "hits" ---
    reponse = client_os.search(index=nom_index, body=corps)
    hits = reponse["hits"]["hits"]

    # --- 5) Mettre en forme un resultat propre (on jette la plomberie OpenSearch) ---
    resultats = []
    for h in hits:
        source = h["_source"]
        resultats.append({
            "score": h["_score"],            # + eleve = + proche de la question
            "texte": source.get("texte", ""),
            "source": source.get("source", ""),
            "page": source.get("page"),
            "chunk_index": source.get("chunk_index"),
        })
    return resultats


# --- Petit test manuel : python -m rag.retrieval "ma question ?" ---
if __name__ == "__main__":
    import sys

    # La question vient de la ligne de commande ; sinon une question par defaut.
    question = " ".join(sys.argv[1:]) or "Quelle base vectorielle est utilisee ?"

    print(f"Question : {question}")
    print("-" * 55)
    chunks = rechercher_chunks(question)

    if not chunks:
        print("Aucun resultat.")
    for i, c in enumerate(chunks, start=1):
        apercu = c["texte"][:160].replace("\n", " ")
        print(f"\n#{i}  score={c['score']:.4f}  source={c['source']}  page={c['page']}")
        print(f"    {apercu}...")
