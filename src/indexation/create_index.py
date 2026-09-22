# ============================================================
#  US 2.2 - Creation de l'index k-NN dans la collection AOSS
#  On definit le "mapping" (le schema de l'index) :
#    - un champ vecteur "embedding" (knn_vector, dim 1024, cosinus, algo HNSW)
#    - les champs de metadonnees, calques sur les chunks du Sprint 1.
#  Puis on cree l'index (operation idempotente : pas de doublon).
# ============================================================

from indexation.client import creer_client_opensearch

# --- Le corps de l'index : "settings" + "mappings" -----------------------
# settings : reglages de l'index. Ici on ACTIVE la recherche vectorielle.
# mappings : le SCHEMA = la liste des champs et le type de chacun.
CORPS_INDEX = {
    "settings": {
        "index.knn": True,               # indispensable : active le k-NN sur l'index
    },
    "mappings": {
        "properties": {
            # ---- LE champ vecteur : celui qu'on interrogera par similarite ----
            "embedding": {
                "type": "knn_vector",          # type special "vecteur"
                "dimension": 1024,             # impose par Titan Text Embeddings V2
                "method": {
                    "name": "hnsw",                 # l'algorithme (cf. explication HNSW)
                    "engine": "nmslib",             # moteur k-NN (gere le cosinus en direct)
                    "space_type": "cosinesimil",    # = metrique COSINUS
                    "parameters": {
                        "ef_construction": 512,     # qualite du graphe a la CONSTRUCTION
                        "m": 16,                    # nb de voisins gardes par noeud
                    },
                },
            },
            # ---- Les metadonnees : memes cles que les chunks du Sprint 1 ----
            "texte": {"type": "text"},         # contenu du chunk (recherche plein-texte)
            "source": {"type": "keyword"},     # nom/URL du doc (valeur EXACTE, filtrable)
            "page": {"type": "integer"},       # numero de page
            "chunk_index": {"type": "integer"},# position du chunk dans le document
            "nb_tokens": {"type": "integer"},  # taille du chunk en tokens
        },
    },
}


def creer_index(client, nom_index):
    """Cree l'index k-NN s'il n'existe pas deja (operation IDEMPOTENTE).

    Renvoie True si l'index vient d'etre cree, False s'il existait deja.
    """
    # Idempotence : on ne recree pas un index deja present (ca leverait une erreur).
    if client.indices.exists(index=nom_index):
        print(f"L'index '{nom_index}' existe deja : rien a faire.")
        return False

    client.indices.create(index=nom_index, body=CORPS_INDEX)
    print(f"Index '{nom_index}' cree avec succes.")
    return True


# --- Lancement : depuis src/, lancer :  python -m indexation.create_index ---
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    endpoint = os.getenv("OPENSEARCH_ENDPOINT")
    region = os.getenv("AWS_REGION")
    profil = os.getenv("AWS_PROFILE")
    nom_index = os.getenv("INDEX_NAME", "smartovate-chunks")

    client = creer_client_opensearch(endpoint, region, profil)
    creer_index(client, nom_index)

    print(
        "\nNote : sur OpenSearch Serverless, l'index peut mettre jusqu'a ~1 minute\n"
        "a etre pleinement disponible (on le verifiera a l'etape suivante)."
    )
