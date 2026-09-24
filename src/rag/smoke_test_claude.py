# ============================================================
#  Etape 0 (Sprint 3) - Smoke test Claude sur Bedrock
#  But : PROUVER qu'on peut reellement appeler le LLM avant
#  d'ecrire le moteur RAG. On utilise l'API "Converse" (le format
#  UNIFIE de Bedrock) - la meme qu'on reutilisera a l'US 3.2.
#  Lancement (depuis src/) :  python -m rag.smoke_test_claude
# ============================================================

import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv

# boto3 reessaie tout seul en cas d'erreur passagere (throttling,
# timeout), avec une attente croissante entre les essais (backoff).
# Anticipe le bug "timeouts" du cahier des charges, sans code manuel.
_CONFIG_RETRY = Config(retries={"max_attempts": 4, "mode": "standard"})


def main():
    load_dotenv()
    profil = os.getenv("AWS_PROFILE")
    # Region dediee au LLM si precisee, sinon on retombe sur AWS_REGION.
    region = os.getenv("BEDROCK_LLM_REGION") or os.getenv("AWS_REGION")
    model_id = os.getenv("BEDROCK_LLM_MODEL_ID")

    print("Profil AWS :", profil)
    print("Region     :", region)
    print("Modele     :", model_id)
    print("-" * 55)

    # Client Bedrock Runtime (celui qui APPELLE les modeles).
    # Comme pour S3/Titan : profil en local, role IAM en deploiement.
    session = boto3.Session(profile_name=profil, region_name=region)
    client = session.client("bedrock-runtime", config=_CONFIG_RETRY)

    # --- L'appel Converse ---
    # system   : les consignes (vide ici, on teste juste l'acces)
    # messages : le fil de conversation (role user/assistant)
    # inferenceConfig : temperature basse = reponse fidele, peu "creative"
    reponse = client.converse(
        modelId=model_id,
        messages=[
            {"role": "user", "content": [{"text": "Reponds en une phrase : qui es-tu ?"}]}
        ],
        inferenceConfig={"maxTokens": 100, "temperature": 0},
    )

    # La reponse Converse a TOUJOURS la meme forme, quel que soit le modele.
    texte = reponse["output"]["message"]["content"][0]["text"]
    usage = reponse["usage"]   # nb de tokens (utile pour suivre les couts)

    print("[OK] Appel Claude reussi (acces Bedrock valide).\n")
    print("Reponse du modele :")
    print("  ", texte)
    print("\nTokens consommes :", usage)


if __name__ == "__main__":
    main()
