# ============================================================
#  US 1.2 - Vectorisation des chunks avec Amazon Titan (Bedrock)
#  On envoie chaque chunk a Titan, qui renvoie un vecteur (embedding).
# ============================================================

import json

import boto3

# Modele d'embeddings d'Amazon (Titan Text Embeddings V2)
MODELE_EMBEDDING = "amazon.titan-embed-text-v2:0"


def creer_client_bedrock(profil=None, region=None):
    """Cree un client Bedrock Runtime (celui qui appelle les modeles).

    Comme pour S3 : profil AWS en local, sinon boto3 prend le role IAM.
    """
    session = boto3.Session(profile_name=profil, region_name=region)
    return session.client("bedrock-runtime")


def generer_embedding(client, texte, modele=MODELE_EMBEDDING):
    """Envoie UN texte a Titan et renvoie son vecteur (une liste de nombres)."""
    reponse = client.invoke_model(
        modelId=modele,
        body=json.dumps({"inputText": texte}),   # ce qu'on envoie a Titan
    )
    # La reponse de Titan est un JSON ; on le lit et on en extrait le vecteur.
    donnees = json.loads(reponse["body"].read())
    return donnees["embedding"]


def vectoriser_chunks(client, chunks, modele=MODELE_EMBEDDING):
    """Ajoute a CHAQUE chunk sa cle 'embedding' (son vecteur)."""
    for chunk in chunks:
        chunk["embedding"] = generer_embedding(client, chunk["texte"], modele)
    return chunks


# --- Petit test en reel : python -m ingestion.embeddings (depuis src) ---
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    client = creer_client_bedrock(os.getenv("AWS_PROFILE"), os.getenv("AWS_REGION"))

    vecteur = generer_embedding(client, "Bonjour, ceci est un test d'embedding.")
    print("Dimension du vecteur :", len(vecteur))
    print("5 premieres valeurs  :", vecteur[:5])
