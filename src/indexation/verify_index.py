# ============================================================
#  US 2.2 - Verification de l'index k-NN
#  Confirme que l'index existe et que son mapping est correct :
#  champ vecteur (dim 1024, cosinus, HNSW) + champs de metadonnees.
# ============================================================

from indexation.client import creer_client_opensearch


def verifier_index(client, nom_index):
    """Lit l'index et affiche un compte rendu lisible de son mapping."""
    if not client.indices.exists(index=nom_index):
        print(f"[KO] L'index '{nom_index}' n'existe PAS.")
        return False

    mapping = client.indices.get_mapping(index=nom_index)
    props = mapping[nom_index]["mappings"]["properties"]
    emb = props.get("embedding", {})
    method = emb.get("method", {})

    print(f"[OK] Index '{nom_index}' : PRESENT\n")
    print("Champ vecteur 'embedding' :")
    print(f"   - type       : {emb.get('type')}")
    print(f"   - dimension  : {emb.get('dimension')}")
    print(f"   - algorithme : {method.get('name')}")
    print(f"   - moteur     : {method.get('engine')}")
    print(f"   - metrique   : {method.get('space_type')}  (cosinesimil = cosinus)")

    metadonnees = {k: v.get("type") for k, v in props.items() if k != "embedding"}
    print("\nChamps de metadonnees :")
    for nom, typ in metadonnees.items():
        print(f"   - {nom:<12} : {typ}")

    # Petit controle automatique des points cles.
    ok = (
        emb.get("type") == "knn_vector"
        and emb.get("dimension") == 1024
        and method.get("space_type") == "cosinesimil"
    )
    print("\n" + ("[OK] Le mapping est conforme (knn_vector, 1024, cosinus)."
                  if ok else "[KO] Le mapping ne correspond pas a l'attendu."))
    return ok


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    client = creer_client_opensearch(
        os.getenv("OPENSEARCH_ENDPOINT"),
        os.getenv("AWS_REGION"),
        os.getenv("AWS_PROFILE"),
    )
    verifier_index(client, os.getenv("INDEX_NAME", "smartovate-chunks"))
