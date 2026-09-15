import json
import os

from aws_cdk import (
    Stack,
    aws_opensearchserverless as opensearchserverless,
)
from constructs import Construct
from dotenv import load_dotenv

# Charge les variables du fichier .env (situé dans infra/) dans l'environnement
load_dotenv()

# Lecture des valeurs de configuration depuis le .env
COLLECTION_NAME = os.environ["COLLECTION_NAME"]
DATA_ACCESS_ROLE_ARN = os.environ["DATA_ACCESS_ROLE_ARN"]


class SmartovateRagStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Brique 1/4 : Encryption policy (chiffrement au repos) ---
        encryption_policy = opensearchserverless.CfnSecurityPolicy(
            self, "EncryptionPolicy",
            name="smartovate-rag-enc",
            type="encryption",
            policy=json.dumps({
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{COLLECTION_NAME}"],
                    }
                ],
                "AWSOwnedKey": True,
            }),
        )

        # --- Brique 2/4 : Network policy (chemin d'accès réseau) ---
        network_policy = opensearchserverless.CfnSecurityPolicy(
            self, "NetworkPolicy",
            name="smartovate-rag-net",
            type="network",
            policy=json.dumps([
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{COLLECTION_NAME}"],
                        },
                        {
                            "ResourceType": "dashboard",
                            "Resource": [f"collection/{COLLECTION_NAME}"],
                        },
                    ],
                    "AllowFromPublic": True,
                }
            ]),
        )

        # --- Brique 3/4 : Data access policy (qui peut lire/écrire) ---
        data_access_policy = opensearchserverless.CfnAccessPolicy(
            self, "DataAccessPolicy",
            name="smartovate-rag-access",
            type="data",
            policy=json.dumps([
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{COLLECTION_NAME}"],
                            "Permission": [
                                "aoss:CreateCollectionItems",
                                "aoss:DeleteCollectionItems",
                                "aoss:UpdateCollectionItems",
                                "aoss:DescribeCollectionItems",
                            ],
                        },
                        {
                            "ResourceType": "index",
                            "Resource": [f"index/{COLLECTION_NAME}/*"],
                            "Permission": [
                                "aoss:CreateIndex",
                                "aoss:DeleteIndex",
                                "aoss:UpdateIndex",
                                "aoss:DescribeIndex",
                                "aoss:ReadDocument",
                                "aoss:WriteDocument",
                            ],
                        },
                    ],
                    "Principal": [DATA_ACCESS_ROLE_ARN],
                }
            ]),
        )

        # --- Brique 4/4 : La collection vectorielle elle-même ---
        collection = opensearchserverless.CfnCollection(
            self, "RagCollection",
            name=COLLECTION_NAME,
            type="VECTORSEARCH",
            description="Collection vectorielle du systeme RAG Smartovate",
        )

        # Dépendances : la collection ne peut être créée QU'APRÈS les 3 policies
        collection.add_resource_dependency(encryption_policy)
        collection.add_resource_dependency(network_policy)
        collection.add_resource_dependency(data_access_policy)