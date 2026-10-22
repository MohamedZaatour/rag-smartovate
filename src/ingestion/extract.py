# ============================================================
#  US 1.1 - Extraction du texte (PDF + Word)
#  Version PAGE PAR PAGE : chaque morceau de texte garde son
#  numero de page. Le Word lit aussi les TABLEAUX, dans l'ordre.
# ============================================================

import os  # outils sur les chemins de fichiers
import re  # nettoyage par motifs
from datetime import UTC, datetime  # date/heure

import docx  # lecture de Word
import pymupdf  # lecture de PDF

# Ces classes servent a reconnaitre, dans un .docx, ce qui est un
# paragraphe (<w:p>) et ce qui est un tableau (<w:tbl>).
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


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


def _parcourir_blocs(document):
    """Parcourt le document Word DANS L'ORDRE et rend chaque bloc :
    soit un Paragraph, soit un Table.

    Word range les tableaux a part ; ici on lit le "corps" du document
    element par element pour ne rien perdre et garder l'ordre d'origine.
    """
    corps = document.element.body  # le corps brut du document
    for element in corps.iterchildren():
        if isinstance(element, CT_P):        # <w:p> = un paragraphe
            yield Paragraph(element, document)
        elif isinstance(element, CT_Tbl):    # <w:tbl> = un tableau
            yield Table(element, document)


def _texte_du_tableau(table):
    """Transforme un tableau en texte lisible :
    cellules separees par ' | ', une ligne par rangee.
    """
    lignes = []
    for rangee in table.rows:
        cellules = [cellule.text.strip() for cellule in rangee.cells]
        lignes.append(" | ".join(cellules))
    return "\n".join(lignes)


def extraire_texte_docx(chemin):
    """Ouvre un Word (.docx) et renvoie une liste d'UNE seule page.

    On parcourt paragraphes ET tableaux dans l'ordre. Un .docx n'a pas de
    vraie notion de page, donc tout le document = un seul bloc = page 1.
    """
    document = docx.Document(chemin)
    morceaux = []
    for bloc in _parcourir_blocs(document):
        if isinstance(bloc, Paragraph):
            morceaux.append(bloc.text)
        elif isinstance(bloc, Table):
            morceaux.append(_texte_du_tableau(bloc))
    texte = "\n".join(morceaux)
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
        "date_extraction": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "nb_pages": len(pages_propres),
        "pages": pages_propres,
    }
    return resultat
