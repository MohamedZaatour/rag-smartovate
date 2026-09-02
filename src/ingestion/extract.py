# ============================================================
#  US 1.1 - Extraction du texte (PDF + Word) + nettoyage + metadonnees
#  Boite a outils reutilisable : ne s'execute pas toute seule,
#  ses fonctions sont importees par d'autres fichiers (ex: s3_loader.py).
# ============================================================

# 1) Bibliotheque standard de Python
import os  # outils sur les chemins de fichiers
import re  # nettoyage par motifs
from datetime import datetime, timezone  # date/heure 

import docx  # lecture de Word 
import pymupdf  # lecture de PDF


def extraire_texte_pdf(chemin):
    """Ouvre un fichier PDF et renvoie tout son texte brut."""
    document = pymupdf.open(chemin)
    texte = ""
    for page in document:
        texte += page.get_text()
    document.close()
    return texte


def extraire_texte_docx(chemin):
    """Ouvre un fichier Word (.docx) et renvoie tout son texte brut."""
    document = docx.Document(chemin)
    texte = ""
    for paragraphe in document.paragraphs:
        texte += paragraphe.text + "\n"
    return texte


def nettoyer_texte(texte):
    """Nettoie le texte : caracteres invisibles, espaces et sauts de ligne en trop."""
    texte = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texte)
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    lignes = [ligne.strip() for ligne in texte.split("\n")]
    texte = "\n".join(lignes)
    return texte.strip()


def traiter_document(chemin):
    """Aiguille selon le type (PDF ou Word), extrait, nettoie, renvoie texte + metadonnees."""
    if chemin.lower().endswith(".pdf"):
        texte_brut = extraire_texte_pdf(chemin)
        type_doc = "pdf"
    elif chemin.lower().endswith(".docx"):
        texte_brut = extraire_texte_docx(chemin)
        type_doc = "docx"
    else:
        raise ValueError(f"Format non supporte : {chemin}")

    texte_propre = nettoyer_texte(texte_brut)

    resultat = {
        "nom_fichier": os.path.basename(chemin),
        "type": type_doc,
        "date_extraction": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "texte": texte_propre,
    }
    return resultat
