# ============================================================
#  Tests de l'orchestrateur (US 3.2 - brique 3)
#  La logique la plus critique : le SEUIL de score (garde-fou).
#  On mocke retrieval ET generation -> aucun appel AWS.
#  On controle le score des chunks pour tester les deux chemins.
# ============================================================

from rag import pipeline


def test_sous_le_seuil_ne_appelle_pas_claude(monkeypatch):
    """Score trop faible -> reponse d'absence SANS appeler Claude."""
    monkeypatch.setenv("SCORE_MIN", "0.5")   # seuil fixe pour le test

    # Un chunk dont le meilleur score (0.3) est SOUS le seuil.
    faux_chunks = [{"score": 0.3, "texte": "x", "source": "s3://b/doc.pdf",
                    "page": 1, "chunk_index": 0}]
    monkeypatch.setattr(pipeline, "rechercher_chunks", lambda question, k=5: faux_chunks)

    # Espion : si generer_reponse est appele, on le saura.
    appels = {"claude": False}

    def espion_generer(prompt):
        appels["claude"] = True
        return {"reponse": "NE DEVRAIT PAS ARRIVER", "tokens": {}, "arret": "end_turn"}

    monkeypatch.setattr(pipeline, "generer_reponse", espion_generer)

    res = pipeline.repondre("une question hors sujet")

    assert res["appel_llm"] is False
    assert res["reponse"] == pipeline.MESSAGE_ABSENCE
    assert res["sources"] == []
    assert appels["claude"] is False        # Claude n'a PAS ete appele


def test_au_dessus_du_seuil_appelle_claude(monkeypatch):
    """Score suffisant -> Claude est appele, sources construites."""
    monkeypatch.setenv("SCORE_MIN", "0.5")

    faux_chunks = [
        {"score": 0.63, "texte": "OpenSearch Serverless.",
         "source": "s3://b/exemple_cahier_des_charges.pdf", "page": 2, "chunk_index": 1},
        {"score": 0.59, "texte": "Index k-NN.",
         "source": "s3://b/exemple_cahier_des_charges.pdf", "page": 4, "chunk_index": 3},
    ]
    monkeypatch.setattr(pipeline, "rechercher_chunks", lambda question, k=5: faux_chunks)
    monkeypatch.setattr(pipeline, "generer_reponse", lambda prompt: {
        "reponse": "Reponse redigee.", "tokens": {"totalTokens": 50}, "arret": "end_turn",
    })

    res = pipeline.repondre("Quelle base vectorielle ?")

    assert res["appel_llm"] is True
    assert res["reponse"] == "Reponse redigee."
    # Les sources sont construites depuis les chunks (nom de fichier, pas d'URI S3).
    assert len(res["sources"]) == 2
    assert res["sources"][0]["source"] == "exemple_cahier_des_charges.pdf"
    assert res["sources"][0]["page"] == 2


def test_aucun_chunk_ne_appelle_pas_claude(monkeypatch):
    """Aucun chunk trouve -> reponse d'absence, sans appeler Claude."""
    monkeypatch.setenv("SCORE_MIN", "0.5")
    monkeypatch.setattr(pipeline, "rechercher_chunks", lambda question, k=5: [])

    appels = {"claude": False}

    def espion_generer(prompt):
        appels["claude"] = True

    monkeypatch.setattr(pipeline, "generer_reponse", espion_generer)

    res = pipeline.repondre("question")

    assert res["appel_llm"] is False
    assert res["reponse"] == pipeline.MESSAGE_ABSENCE
    assert appels["claude"] is False
