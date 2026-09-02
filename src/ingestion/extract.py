# ============================================================
#  US 1.1 - Extraction du texte (PDF + Word)
#  Version PAGE PAR PAGE : chaque morceau de texte garde son
#  numero de page. Utile pour citer les sources plus tard
#  ("d'apres la page 4...") et pour le decoupage (US 1.2).
# ============================================================

import os  # outils sur les chemins de fichiers
import re  # nettoyage par motifs
from datetime import datetime, timezone  # date/heure

import docx  # lecture de Word
import pymupdf  # lecture de PDF


def extraire_texte_pdf(chemin):
    """Ouvre un PDF et renvoie une LISTE de pages numerotees.

    Format : [{"page": 1, "texte": "..."}, {"page": 2, "texte": "..."}, ...]
    """
    document = pymupdf.open(chemin)
    pages = []
    # enumerate donne le numero (1, 2, 3...) ET la page en meme temps.
    for numero, page in enumerate(document, start=1):
        pages.append({"page": numero, "texte": page.get_text()})
    document.close()
    return pages


def extraire_texte_docx(chemin):
    """Ouvre un Word (.docx) et renvoie une liste d'UNE seule page.

    Un .docx n'a pas de vraie notion de page (le texte se recompose selon
    l'affichage), donc on traite tout le document comme un seul bloc = page 1.
    """
    document = docx.Document(chemin)
    texte = ""
    for paragraphe in document.paragraphs:
        texte += paragraphe.text + "\n"
    return [{"page": 1, "texte": texte}]


def nettoyer_texte(texte):
    """Nettoie un texte : caracteres invisibles, espaces et sauts de ligne en trop."""
    texte = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texte)
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    lignes = [ligne.strip() for ligne in texte.split("\n")]
    texte = "\n".join(lignes)
    return texte.strip()


def traiter_document(chemin):
    """Aiguille selon le type (PDF ou Word), extrait page par page, nettoie
    chaque page, et renvoie les metadonnees + la liste des pages."""
    if chemin.lower().endswith(".pdf"):
        pages_brutes = extraire_texte_pdf(chemin)
        type_doc = "pdf"
    elif chemin.lower().endswith(".docx"):
        pages_brutes = extraire_texte_docx(chemin)
        type_doc = "docx"
    else:
        raise ValueError(f"Format non supporte : {chemin}")

    # On nettoie le texte de CHAQUE page, en conservant son numero.
    pages_propres = []
    for page in pages_brutes:
        pages_propres.append({
            "page": page["page"],
            "texte": nettoyer_texte(page["texte"]),
        })

    # Si AUCUN texte n'a ete extrait (toutes les pages vides), c'est
    # souvent un PDF scanne (des images, pas du texte). On le signale
    # clairement au lieu de laisser passer un document vide en silence.
    total_caracteres = sum(len(page["texte"]) for page in pages_propres)
    if total_caracteres == 0:
        raise ValueError(
            f"aucun texte extrait de {os.path.basename(chemin)} "
            "(PDF scanne / image ? -> OCR a envisager)"
        )

    resultat = {
        "nom_fichier": os.path.basename(chemin),
        "type": type_doc,
        "date_extraction": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "nb_pages": len(pages_propres),
        "pages": pages_propres,
    }
    return resultat
