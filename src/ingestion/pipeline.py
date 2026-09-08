# ============================================================
#  US 1.2 - Pipeline d'ingestion (orchestrateur)
#  Pour chaque document du bucket S3 :
#     extraction  ->  chunking  ->  embeddings
#  Produit des chunks complets (texte + metadonnees + vecteur),
#  prets a etre indexes dans OpenSearch (Sprint 2).
# ============================================================

import os

from dotenv import load_dotenv

from ingestion.chunking import decouper_document
from ingestion.embeddings import creer_client_bedrock, vectoriser_chunks
from ingestion.s3_loader import (
    creer_client_s3,
    lister_documents_s3,
    traiter_document_s3,
)


def ingerer_document(s3, bedrock, bucket, cle):
    """Chaine complete pour UN document : extraction -> chunking -> embeddings.

    Renvoie la liste des chunks vectorises (texte + metadonnees + embedding).
    """
    document = traiter_document_s3(s3, bucket, cle)   # 1) extraire (page par page)
    chunks = decouper_document(document)              # 2) decouper en chunks
    chunks = vectoriser_chunks(bedrock, chunks)       # 3) vectoriser chaque chunk
    return chunks


# --- Ingestion de TOUT le bucket : python -m ingestion.pipeline (depuis src) ---
if __name__ == "__main__":
    load_dotenv()
    profil = os.getenv("AWS_PROFILE")
    region = os.getenv("AWS_REGION")
    bucket = os.getenv("S3_BUCKET")

    # On cree les DEUX clients une seule fois, puis on les reutilise.
    s3 = creer_client_s3(profil, region)
    bedrock = creer_client_bedrock(profil, region)

    tous_les_chunks = []
    succes = 0
    echecs = 0

    for cle in lister_documents_s3(s3, bucket):
        try:
            chunks = ingerer_document(s3, bedrock, bucket, cle)
            tous_les_chunks.extend(chunks)
            print("=" * 50)
            print("Document       :", cle)
            print("Chunks generes :", len(chunks))
            if chunks:
                print("Dimension vec  :", len(chunks[0]["embedding"]))
            succes += 1
        # Robustesse : un document fautif est ignore et signale, sans arreter les autres.
        except Exception as erreur:  # noqa: BLE001
            print("=" * 50)
            print("IGNORE         :", cle)
            print("Raison         :", erreur)
            echecs += 1

    print("=" * 50)
    print(
        f"Pipeline termine : {succes} document(s) traite(s), {echecs} ignore(s), "
        f"{len(tous_les_chunks)} chunks vectorises au total."
    )
