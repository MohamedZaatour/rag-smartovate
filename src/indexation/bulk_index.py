# ============================================================
#  US 2.3 - Indexation en masse (bulk) des chunks dans l'index k-NN
#  Flux complet :
#     pipeline Sprint 1 (extraction -> chunking -> embeddings)
#        -> repartir d'un index VIDE (idempotence)
#        -> insertion en masse via le helper "bulk" d'opensearch-py
#
#  NB : sur une collection VECTORSEARCH, AOSS INTERDIT les _id personnalises.
#  On ne fournit donc PAS d'_id (OpenSearch en genere un automatiquement).
#  D'ou la strategie "index vide avant chaque indexation complete" pour
#  eviter les doublons au reindexage.
# ============================================================

import time

from opensearchpy import helpers

from indexation.client import creer_client_opensearch
from indexation.create_index import creer_index

# Nombre de documents envoyes par paquet (batching -> anti-timeout).
TAILLE_LOT = 100


def _actions(chunks, nom_index):
    """Transforme chaque chunk en 'action' bulk : ranger ce contenu dans l'index.

    On mappe explicitement les 6 champs du chunk sur les champs du mapping
    (US 2.2). Aucun _id fourni (interdit sur VECTORSEARCH).
    """
    for chunk in chunks:
        yield {
            "_index": nom_index,
            "_source": {
                "texte": chunk["texte"],
                "source": chunk["source"],
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "nb_tokens": chunk["nb_tokens"],
                "embedding": chunk["embedding"],
            },
        }


def reinitialiser_index(client, nom_index):
    """Repart d'un index VIDE : supprime l'index s'il existe, puis le recree.

    Garantit l'idempotence malgre l'absence d'_id : relancer donne toujours
    le meme resultat, sans doublon.
    """
    if client.indices.exists(index=nom_index):
        client.indices.delete(index=nom_index)
        print(f"Index '{nom_index}' supprime (on repart a zero).")
        time.sleep(5)  # laisse AOSS propager la suppression
    creer_index(client, nom_index)
    time.sleep(5)      # laisse le nouvel index devenir disponible


def indexer_chunks(client, nom_index, chunks):
    """Insere les chunks en masse (par lots), avec reessais automatiques.

    Renvoie (nb_succes, liste_erreurs).
    """
    succes, erreurs = helpers.bulk(
        client,
        _actions(chunks, nom_index),
        chunk_size=TAILLE_LOT,     # taille des paquets
        max_retries=3,             # reessaie en cas d'erreur passagere (throttling)
        initial_backoff=2,         # attente croissante entre les tentatives
        raise_on_error=False,      # ne stoppe pas tout sur une erreur -> on collecte
    )
    return succes, erreurs


# --- Lancement : depuis src/, lancer :  python -m indexation.bulk_index ---
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    from ingestion.embeddings import creer_client_bedrock
    from ingestion.pipeline import ingerer_document
    from ingestion.s3_loader import creer_client_s3, lister_documents_s3

    load_dotenv()
    profil = os.getenv("AWS_PROFILE")
    region = os.getenv("AWS_REGION")
    bucket = os.getenv("S3_BUCKET")
    endpoint = os.getenv("OPENSEARCH_ENDPOINT")
    nom_index = os.getenv("INDEX_NAME", "smartovate-chunks")

    # 1) Produire les chunks vectorises (pipeline du Sprint 1)
    print("== 1/4 : production des chunks (pipeline Sprint 1) ==")
    s3 = creer_client_s3(profil, region)
    bedrock = creer_client_bedrock(profil, region)
    chunks = []
    for cle in lister_documents_s3(s3, bucket):
        try:
            chunks.extend(ingerer_document(s3, bedrock, bucket, cle))
            print("  traite :", cle)
        except Exception as erreur:  # noqa: BLE001
            print("  ignore :", cle, "->", erreur)
    print(f"  => {len(chunks)} chunk(s) vectorise(s) a indexer.")

    # 2) Repartir d'un index vide (idempotence)
    print("== 2/4 : reinitialisation de l'index ==")
    client = creer_client_opensearch(endpoint, region, profil)
    reinitialiser_index(client, nom_index)

    # 3) Indexation en masse
    print("== 3/4 : indexation en masse (bulk) ==")
    succes, erreurs = indexer_chunks(client, nom_index, chunks)
    print(f"  => {succes} document(s) indexe(s), {len(erreurs)} erreur(s).")
    if erreurs:
        print("  premieres erreurs :", erreurs[:3])

    # 4) Verification : on attend que le refresh AOSS rende les documents comptables
    print("== 4/4 : verification (attente du refresh AOSS) ==")
    total = 0
    for _ in range(18):            # jusqu'a ~90 s
        total = client.count(index=nom_index)["count"]
        if total >= succes:
            break
        time.sleep(5)
    print(f"  => {total} document(s) present(s) dans l'index '{nom_index}'.")
