# ============================================================
#  US 3.2 - Brique 2 : Generation de la reponse (Claude via Converse)
#  Prend le prompt (systeme + utilisateur), appelle Claude, et renvoie
#  la reponse redigee + le decompte de tokens.
#  ATTENTION : cette brique APPELLE AWS (session SSO requise, petit cout).
#  Lancement (depuis src/) :  python -m rag.generation "ta question ?"
# ============================================================

import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Briques deja construites (US 3.1 + brique 1)
from rag.prompt import construire_prompt
from rag.retrieval import rechercher_chunks

# --- Reglages de generation ---
TEMPERATURE = 0     # 0 = fidele, aucune fantaisie -> anti-hallucination
MAX_TOKENS = 800    # longueur max de la reponse (maitrise cout + concision)

# boto3 reessaie en cas d'erreur passagere (backoff). read_timeout plus long
# que par defaut : GENERER du texte prend plus de temps qu'un embedding.
_CONFIG = Config(
    retries={"max_attempts": 4, "mode": "standard"},
    connect_timeout=10,
    read_timeout=60,
)


def creer_client_bedrock(profil=None, region=None):
    """Client bedrock-runtime (celui qui appelle les modeles)."""
    session = boto3.Session(profile_name=profil, region_name=region)
    return session.client("bedrock-runtime", config=_CONFIG)


def generer_reponse(prompt, model_id=None, profil=None, region=None):
    """Envoie le prompt a Claude (API Converse) et renvoie sa reponse.

    - prompt : dict {"systeme", "utilisateur"} produit par construire_prompt.
    Renvoie un dict : {"reponse", "tokens", "arret"}.
    """
    load_dotenv()
    model_id = model_id or os.getenv("BEDROCK_LLM_MODEL_ID")
    region = region or os.getenv("BEDROCK_LLM_REGION") or os.getenv("AWS_REGION")
    profil = profil or os.getenv("AWS_PROFILE")

    client = creer_client_bedrock(profil, region)

    # --- L'appel Converse ---
    #   system   <- les consignes (brique 1)
    #   messages <- le contexte + la question (brique 1)
    reponse = client.converse(
        modelId=model_id,
        system=[{"text": prompt["systeme"]}],
        messages=[
            {"role": "user", "content": [{"text": prompt["utilisateur"]}]}
        ],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": TEMPERATURE},
    )

    # La reponse Converse a toujours la meme structure.
    return {
        "reponse": reponse["output"]["message"]["content"][0]["text"],
        "tokens": reponse["usage"],       # in / out / total (pour le cout)
        "arret": reponse["stopReason"],   # "end_turn" = fini, "max_tokens" = coupe
    }


# --- Test de BOUT EN BOUT : retrieval -> prompt -> generation ---
#     python -m rag.generation "ma question ?"
if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quelle base vectorielle est utilisee ?"

    print(f"Question : {question}")
    print("-" * 55)

    # 1) US 3.1 : chercher les chunks pertinents
    chunks = rechercher_chunks(question)
    # 2) Brique 1 : construire le prompt
    prompt = construire_prompt(question, chunks)
    # 3) Brique 2 : generer la reponse avec Claude
    resultat = generer_reponse(prompt)

    print("\nREPONSE DE CLAUDE :\n")
    print(resultat["reponse"])
    print("\n" + "-" * 55)
    print("Chunks fournis a Claude (contexte) :")
    for c in chunks:
        nom = str(c["source"]).split("/")[-1]
        print(f"   - {nom} p.{c['page']}  (score {c['score']:.3f})")
    print(f"\nArret : {resultat['arret']}  |  Tokens : {resultat['tokens']}")
