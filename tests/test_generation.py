# ============================================================
#  Tests de la generation (US 3.2 - brique 2)
#  On remplace (mock) le client Bedrock : sa methode 'converse'
#  renvoie une fausse reponse. Aucun appel a Claude, aucun cout.
# ============================================================

from rag import generation


class FauxClientBedrock:
    """Doublure du client Bedrock : 'converse' renvoie une reponse
    preparee, avec la meme structure que la vraie API Converse."""

    def converse(self, modelId=None, system=None, messages=None, inferenceConfig=None):
        return {
            "output": {"message": {"content": [{"text": "Reponse de test."}]}},
            "usage": {"inputTokens": 100, "outputTokens": 20, "totalTokens": 120},
            "stopReason": "end_turn",
        }


def test_generer_reponse_extrait_les_bons_champs(monkeypatch):
    """generer_reponse lit correctement la reponse Converse."""
    monkeypatch.setattr(generation, "creer_client_bedrock", lambda *a, **k: FauxClientBedrock())

    prompt = {"systeme": "des consignes", "utilisateur": "contexte + question"}
    res = generation.generer_reponse(prompt)

    assert res["reponse"] == "Reponse de test."
    assert res["arret"] == "end_turn"
    assert res["tokens"]["totalTokens"] == 120


def test_prompt_bien_place_dans_converse(monkeypatch):
    """Les consignes vont dans 'system', le contexte dans 'messages',
    et la temperature vaut bien 0 (anti-hallucination)."""
    captures = {}

    class ClientCapteur:
        def converse(self, modelId=None, system=None, messages=None, inferenceConfig=None):
            captures["system"] = system
            captures["messages"] = messages
            captures["config"] = inferenceConfig
            return {
                "output": {"message": {"content": [{"text": "ok"}]}},
                "usage": {"totalTokens": 1},
                "stopReason": "end_turn",
            }

    monkeypatch.setattr(generation, "creer_client_bedrock", lambda *a, **k: ClientCapteur())

    prompt = {"systeme": "MES CONSIGNES", "utilisateur": "MON CONTEXTE"}
    generation.generer_reponse(prompt)

    # Les consignes -> parametre 'system'
    assert captures["system"] == [{"text": "MES CONSIGNES"}]
    # Le contexte -> 'messages', role "user"
    assert captures["messages"][0]["role"] == "user"
    assert captures["messages"][0]["content"][0]["text"] == "MON CONTEXTE"
    # Temperature = 0 (fidelite, anti-hallucination)
    assert captures["config"]["temperature"] == 0
