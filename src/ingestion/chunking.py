# ============================================================
#  US 1.2 - Decoupage du texte en chunks (Option A : fait main)
#  On coupe chaque page en morceaux de ~500 tokens, avec 10%
#  de chevauchement, en gardant la source et le numero de page.
# ============================================================

import tiktoken  # pour compter et decouper le texte en tokens

# Parametres (cahier des charges : 500-1000 tokens, 10% d'overlap)
TAILLE_CHUNK = 500   # nombre de tokens par chunk
OVERLAP = 50         # tokens repris du chunk precedent (10% de 500)

# On charge l'encodeur AU PREMIER USAGE (pas a l'import) : ainsi importer ce
# fichier ne declenche aucun telechargement reseau. C'est une bonne pratique.
_encodeur = None


def _get_encodeur():
    """Renvoie l'encodeur tiktoken, charge une seule fois (au premier appel)."""
    global _encodeur
    if _encodeur is None:
        _encodeur = tiktoken.get_encoding("cl100k_base")
    return _encodeur


def _decouper_texte(texte, taille_chunk=TAILLE_CHUNK, overlap=OVERLAP):
    """Decoupe UN texte en morceaux de `taille_chunk` tokens, avec `overlap`
    tokens de chevauchement. Renvoie une liste de chaines.

    Principe : une "fenetre glissante". On prend `taille_chunk` tokens, puis on
    avance de (taille_chunk - overlap) -> la fin d'un chunk se retrouve au debut
    du suivant.
    """
    enc = _get_encodeur()
    tokens = enc.encode(texte)
    if not tokens:
        return []                       # page vide -> aucun chunk

    pas = taille_chunk - overlap        # de combien on avance a chaque fenetre
    chunks = []
    debut = 0
    while debut < len(tokens):
        fin = debut + taille_chunk
        chunks.append(enc.decode(tokens[debut:fin]))   # tokens -> texte
        if fin >= len(tokens):                         # cette fenetre atteint la fin -> stop
            break
        debut += pas                                   # on glisse la fenetre
    return chunks


def decouper_document(document, taille_chunk=TAILLE_CHUNK, overlap=OVERLAP):
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
