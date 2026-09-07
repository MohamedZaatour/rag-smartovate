# ============================================================
#  US 1.2 - Decoupage du texte en chunks (Option A : fait main)
#  On coupe chaque page en morceaux de <= TAILLE_CHUNK tokens,
#  avec 10% de chevauchement, en gardant source et numero de page.
# ============================================================

import tiktoken  # pour compter et decouper le texte en tokens

# Parametres (cahier des charges : 500-1000 tokens, 10% d'overlap)
TAILLE_CHUNK = 500            # taille MAX d'un chunk, en tokens
POURCENTAGE_OVERLAP = 0.10    # 10% -> l'overlap suit toujours la taille choisie

# On charge l'encodeur AU PREMIER USAGE (pas a l'import) : importer ce fichier
# ne declenche donc aucun telechargement reseau (bonne pratique).
_encodeur = None


def _get_encodeur():
    """Renvoie l'encodeur tiktoken, charge une seule fois (au premier appel)."""
    global _encodeur
    if _encodeur is None:
        _encodeur = tiktoken.get_encoding("cl100k_base")
    return _encodeur


def _decouper_texte(texte, taille_chunk=TAILLE_CHUNK, overlap=None):
    """Decoupe UN texte en morceaux de <= `taille_chunk` tokens, avec un
    chevauchement. Si `overlap` n'est pas precise, il vaut 10% de la taille.

    Principe : une "fenetre glissante". On prend `taille_chunk` tokens, puis on
    avance de (taille_chunk - overlap) -> la fin d'un chunk se retrouve au debut
    du suivant.
    """
    if overlap is None:
        overlap = int(taille_chunk * POURCENTAGE_OVERLAP)   # ex: 10% de 500 = 50

    enc = _get_encodeur()
    tokens = enc.encode(texte)
    if not tokens:
        return []                             # page vide -> aucun chunk

    pas = max(1, taille_chunk - overlap)      # de combien on avance (au moins 1)
    chunks = []
    debut = 0
    while debut < len(tokens):
        fin = debut + taille_chunk
        chunks.append(enc.decode(tokens[debut:fin]))   # tokens -> texte
        if fin >= len(tokens):                         # fenetre a la fin -> stop
            break
        debut += pas                                   # on glisse la fenetre
    return chunks


def decouper_document(document, taille_chunk=TAILLE_CHUNK, overlap=None):
    """Decoupe un document (sortie de traiter_document) en chunks, PAGE PAR PAGE.

    Chaque chunk conserve ses metadonnees : source, numero de page, index, taille.
    """
    enc = _get_encodeur()
    # La source : l'adresse S3 si elle existe, sinon le nom du fichier.
    source = document.get("source_s3") or document.get("nom_fichier", "inconnu")

    chunks = []
    index = 0
    for page in document["pages"]:
        for morceau in _decouper_texte(page["texte"], taille_chunk, overlap):
            chunks.append({
                "source": source,
                "page": page["page"],
                "chunk_index": index,
                "nb_tokens": len(enc.encode(morceau)),
                "texte": morceau,
            })
            index += 1
    return chunks
