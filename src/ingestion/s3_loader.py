# ============================================================
#  Lecture des documents depuis un bucket Amazon S3
#  US 1.1 - Marche B : telecharger + extraire depuis S3 (robuste)
# ============================================================

import os  # outils sur les chemins de fichiers
import tempfile  # dossier temporaire du systeme (pour les fichiers jetables)

import boto3  # SDK AWS pour Python
from dotenv import load_dotenv  # charge la config depuis le fichier .env
from extract import traiter_document  # notre chaine d'extraction (fichier extract.py)

# Types de documents que l'on sait traiter
TYPES_SUPPORTES = (".pdf", ".docx")


def creer_client_s3(profil):
    """Cree UN client S3 a partir d'un profil AWS (a reutiliser ensuite)."""
    session = boto3.Session(profile_name=profil)
    return session.client("s3")


def lister_documents_s3(s3, bucket):
    """Renvoie la liste des noms de fichiers presents dans un bucket S3."""
    reponse = s3.list_objects_v2(Bucket=bucket)
    return [objet["Key"] for objet in reponse.get("Contents", [])]


def traiter_document_s3(s3, bucket, cle):
    """Telecharge un document depuis S3, l'extrait et le nettoie. Renvoie texte + metadonnees."""
    # 0) Ignorer d'emblee les types non supportes (avant meme de telecharger)
    if not cle.lower().endswith(TYPES_SUPPORTES):
        raise ValueError(f"type non supporte ({cle})")
    # 1) Telecharger dans le dossier temporaire du systeme (copie jetable)
    chemin_temp = os.path.join(tempfile.gettempdir(), os.path.basename(cle))
    s3.download_file(bucket, cle, chemin_temp)
    # 2) Reutiliser notre chaine d'extraction locale
    resultat = traiter_document(chemin_temp)
    # 3) Noter la source S3 (pour citer les sources plus tard)
    resultat["source_s3"] = f"s3://{bucket}/{cle}"
    # 4) Supprimer la copie temporaire
    os.remove(chemin_temp)

    return resultat


# --- Ingestion de TOUS les documents du bucket (robuste) ---
if __name__ == "__main__":
    # Charger la configuration depuis le fichier .env
    load_dotenv()
    profil = os.getenv("AWS_PROFILE")
    bucket = os.getenv("S3_BUCKET")

    # Creer le client S3 UNE SEULE FOIS, puis le reutiliser
    s3 = creer_client_s3(profil)

    succes = 0
    echecs = 0

    for cle in lister_documents_s3(s3, bucket):
        try:
            doc = traiter_document_s3(s3, bucket, cle)
            print("=" * 45)
            print("Source S3       :", doc["source_s3"])
            print("Type            :", doc["type"])
            print("Taille du texte :", len(doc["texte"]), "caracteres")
            succes += 1
        # On attrape VOLONTAIREMENT toute erreur : un document fautif ne doit
        # pas arreter l'ingestion (choix de robustesse assume).
        except Exception as erreur:  # noqa: BLE001
            print("=" * 45)
            print("IGNORE          :", cle)
            print("Raison          :", erreur)
            echecs += 1

    print("=" * 45)
    print(f"Ingestion terminee : {succes} document(s) traite(s), {echecs} ignore(s).")
