# ============================================================
#  US 2.2 - Client OpenSearch (connexion a la collection AOSS)
#  Construit un client "opensearch-py" authentifie en SigV4, service "aoss".
#  Ce client est REUTILISE dans tout le Sprint 2 :
#     US 2.2 (creer l'index) -> US 2.3 (inserer les chunks) -> US 2.4 (rechercher)
# ============================================================

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

# OpenSearch Serverless => nom de service "aoss" pour la signature SigV4.
# ATTENTION : surtout PAS "es" (qui designe l'ancien OpenSearch manage,
# non-serverless). Se tromper ici = erreur 403 tres deroutante.
SERVICE_AOSS = "aoss"


def creer_client_opensearch(endpoint, region, profil=None):
    """Cree un client opensearch-py connecte a la collection AOSS.

    - endpoint : hote de la collection, SANS "https://"
                 (ex: abcd1234.us-west-2.aoss.amazonaws.com)
    - region   : region AWS de la collection (ex: us-west-2)
    - profil   : profil AWS local (ex: smartovate).
                 None => boto3 prend le role IAM (cas Lambda/ECS).
    """
    # 1) Recuperer les identifiants AWS (cle + secret) de la session.
    #    Meme logique que creer_client_s3 / creer_client_bedrock du Sprint 1.
    session = boto3.Session(profile_name=profil, region_name=region)
    credentials = session.get_credentials()

    # 2) Le "signeur" SigV4 : il signe CHAQUE requete HTTP avec ces identifiants,
    #    pour le service "aoss". C'est le 1er niveau d'autorisation (IAM).
    #    Le 2e niveau, c'est la data access policy de l'US 2.1 (deja en place).
    auth = AWSV4SignerAuth(credentials, region, SERVICE_AOSS)

    # 3) Le client lui-meme : HTTPS sur le port 443, transport via "requests".
    client = OpenSearch(
        hosts=[{"host": endpoint, "port": 443}],
        http_auth=auth,
        use_ssl=True,               # AOSS n'accepte que le HTTPS
        verify_certs=True,          # on verifie le certificat du serveur
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,            # reutilise les connexions (perf)
        timeout=300,                # marge pour les operations lentes (anti-timeout)
    )
    return client


# --- Petit test de connexion : depuis src/, lancer :  python -m indexation.client ---
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    endpoint = os.getenv("OPENSEARCH_ENDPOINT")
    region = os.getenv("AWS_REGION")
    profil = os.getenv("AWS_PROFILE")
    index = os.getenv("INDEX_NAME", "smartovate-chunks")

    client = creer_client_opensearch(endpoint, region, profil)

    # indices.exists est un appel LEGER : s'il repond sans erreur 403,
    # c'est que l'authentification SigV4 fonctionne. Il renvoie False
    # tant que l'index n'a pas encore ete cree (ce qui est normal ici).
    existe = client.indices.exists(index=index)
    print("Connexion OpenSearch OK (authentification SigV4 valide).")
    print(f"Endpoint      : {endpoint}")
    print(f"Index '{index}' existe deja ? -> {existe}")
