# ============================================================
#  Tests de la recherche semantique (US 3.1)
#  On remplace (mock) l'embedding Titan ET le client OpenSearch :
#  aucun appel AWS, aucun reseau. On verifie que rechercher_chunks
#  TRANSFORME correctement la reponse d'OpenSearch.
# ============================================================

from rag import retrieval


class FauxClientOpenSearch:
    """Doublure du client OpenSearch : sa methode 'search' renvoie une
    reponse preparee d'avance, comme le ferait le vrai service."""

    def search(self, index=None, body=None):
        return {
            "hits": {
                "hits": [
                    {"_score": 0.63, "_source": {
                        "texte": "OpenSearch Serverless est la base vectorielle.",
                        "source": "s3://bucket/exemple_cahier_des_charges.pdf",
                        "page": 2, "chunk_index": 1,
                    }},
                    {"_score": 0.59, "_source": {
                        "texte": "Index k-NN dimension 1024.",
                        "source": "s3://bucket/exemple_cahier_des_charges.pdf",
                        "page": 4, "chunk_index": 3,
                    }},
                ]
            }
        }


def test_rechercher_chunks_transforme_la_reponse(monkeypatch):
    # On branche nos doublures A LA PLACE des vraies fonctions,
    # dans le module retrieval (la ou elles sont utilisees).
    monkeypatch.setattr(retrieval, "creer_client_bedrock", lambda *a, **k: None)
    monkeypatch.setattr(retrieval, "generer_embedding", lambda client, texte: [0.1] * 1024)
    monkeypatch.setattr(retrieval, "creer_client_opensearch", lambda *a, **k: FauxClientOpenSearch())

    resultats = retrieval.rechercher_chunks("Quelle base vectorielle ?", k=5)

    # 2 chunks renvoyes, dans l'ordre de la reponse.
    assert len(resultats) == 2
    # Chaque resultat a bien la structure "propre" attendue.
    attendu = {"score", "texte", "source", "page", "chunk_index"}
    assert set(resultats[0].keys()) == attendu
    # Le 1er chunk = le meilleur score, valeurs bien recopiees.
    assert resultats[0]["score"] == 0.63
    assert resultats[0]["page"] == 2
    assert resultats[0]["texte"].startswith("OpenSearch Serverless")
    # Le champ 'embedding' (1024 nombres) n'est PAS rapatrie.
    assert "embedding" not in resultats[0]


def test_k_est_bien_transmis_a_opensearch(monkeypatch):
    """La requete envoyee a OpenSearch demande bien k resultats."""
    captures = {}

    class ClientCapteur:
        def search(self, index=None, body=None):
            captures["body"] = body      # on memorise la requete envoyee
            return {"hits": {"hits": []}}

    monkeypatch.setattr(retrieval, "creer_client_bedrock", lambda *a, **k: None)
    monkeypatch.setattr(retrieval, "generer_embedding", lambda client, texte: [0.1] * 1024)
    monkeypatch.setattr(retrieval, "creer_client_opensearch", lambda *a, **k: ClientCapteur())

    retrieval.rechercher_chunks("une question", k=3)

    assert captures["body"]["size"] == 3
    assert captures["body"]["query"]["knn"]["embedding"]["k"] == 3
