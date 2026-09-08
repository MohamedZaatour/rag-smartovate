# ============================================================
#  Tests de la vectorisation (US 1.2)
#  On remplace le vrai client Bedrock par un FAUX (mock) : aucun
#  appel AWS, aucun cout, aucun reseau.
# ============================================================

import io
import json

from ingestion import embeddings


class FauxBedrock:
    """Faux client Bedrock : renvoie toujours le meme vecteur bidon."""

    def invoke_model(self, modelId=None, body=None):
        corps = json.dumps({"embedding": [0.1, 0.2, 0.3]}).encode("utf-8")
        return {"body": io.BytesIO(corps)}   # imite le "flux" de la vraie reponse


def test_generer_embedding_extrait_le_vecteur():
    vecteur = embeddings.generer_embedding(FauxBedrock(), "un texte")
    assert vecteur == [0.1, 0.2, 0.3]


def test_vectoriser_chunks_ajoute_embedding_a_chaque_chunk():
    chunks = [{"texte": "bonjour"}, {"texte": "monde"}]
    resultat = embeddings.vectoriser_chunks(FauxBedrock(), chunks)
    assert all("embedding" in c for c in resultat)
    assert resultat[0]["embedding"] == [0.1, 0.2, 0.3]
