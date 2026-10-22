# ============================================================
#  Tests automatiques du decoupage (US 1.2)
#  On remplace le vrai encodeur par un FAUX (mock) : 1 mot = 1 token.
#  Ainsi les tests sont rapides et ne dependent d'aucun reseau.
# ============================================================

import pytest

from ingestion import chunking


class FauxEncodeur:
    """Faux encodeur : 1 mot = 1 token (aucun telechargement)."""

    def encode(self, texte):
        return texte.split()

    def decode(self, tokens):
        return " ".join(tokens)


@pytest.fixture(autouse=True)
def _encodeur_factice(monkeypatch):
    """Avant CHAQUE test, on installe le faux encodeur a la place du vrai."""
    monkeypatch.setattr(chunking, "_encodeur", FauxEncodeur())


def _doc(pages):
    """Fabrique un document au format de traiter_document (pour les tests)."""
    return {
        "nom_fichier": "test.pdf",
        "type": "pdf",
        "nb_pages": len(pages),
        "pages": [{"page": i + 1, "texte": t} for i, t in enumerate(pages)],
    }


# --- _decouper_texte : la fenetre glissante ---

def test_texte_court_donne_un_seul_chunk():
    chunks = chunking._decouper_texte("un deux trois", taille_chunk=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0] == "un deux trois"


def test_texte_vide_donne_aucun_chunk():
    assert chunking._decouper_texte("", taille_chunk=10, overlap=2) == []


def test_taille_des_chunks_respectee():
    texte = " ".join(f"m{i}" for i in range(1, 101))  # 100 tokens
    chunks = chunking._decouper_texte(texte, taille_chunk=20, overlap=5)
    for c in chunks:
        assert len(c.split()) <= 20


def test_overlap_correct():
    texte = " ".join(f"m{i}" for i in range(1, 51))  # 50 tokens
    chunks = chunking._decouper_texte(texte, taille_chunk=20, overlap=5)
    fin_du_chunk0 = chunks[0].split()[-5:]
    debut_du_chunk1 = chunks[1].split()[:5]
    assert fin_du_chunk0 == debut_du_chunk1


# --- decouper_document : metadonnees et pages ---

def test_metadonnees_conservees():
    doc = _doc(["texte de la page une", "texte de la page deux"])
    chunks = chunking.decouper_document(doc, taille_chunk=10, overlap=2)
    assert chunks[0]["source"] == "test.pdf"
    assert chunks[0]["page"] == 1
    assert chunks[1]["page"] == 2
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_page_conservee_quand_la_page_se_decoupe():
    longue = " ".join(f"m{i}" for i in range(1, 46))  # 45 tokens -> plusieurs chunks
    chunks = chunking.decouper_document(_doc([longue]), taille_chunk=20, overlap=5)
    assert len(chunks) > 1
    assert all(c["page"] == 1 for c in chunks)


def test_source_s3_prioritaire_sur_nom_fichier():
    doc = _doc(["bonjour"])
    doc["source_s3"] = "s3://bucket/cle.pdf"
    chunks = chunking.decouper_document(doc, taille_chunk=10, overlap=2)
    assert chunks[0]["source"] == "s3://bucket/cle.pdf"
