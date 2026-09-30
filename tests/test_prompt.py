# ============================================================
#  Tests de la construction du prompt (US 3.2 - brique 1)
#  Brique 100% "texte" : AUCUN mock, aucun appel AWS.
# ============================================================

from rag.prompt import CONSIGNES_SYSTEME, construire_prompt, formater_contexte

# Deux faux chunks qui imitent la sortie de retrieval.py.
CHUNKS = [
    {
        "texte": "Amazon OpenSearch Serverless est la base vectorielle.",
        "source": "s3://smartovate-rag-documents-mohamed/exemple_cahier_des_charges.pdf",
        "page": 2, "chunk_index": 1, "score": 0.63,
    },
    {
        "texte": "Un index k-NN de dimension 1024 (Titan).",
        "source": "s3://smartovate-rag-documents-mohamed/exemple_cahier_des_charges.pdf",
        "page": 4, "chunk_index": 3, "score": 0.59,
    },
]


def test_structure_du_prompt():
    """construire_prompt renvoie un dict avec exactement les 2 cles attendues."""
    prompt = construire_prompt("Quelle base vectorielle ?", CHUNKS)
    assert set(prompt.keys()) == {"systeme", "utilisateur"}
    # Le bloc systeme est bien celui des consignes definies.
    assert prompt["systeme"] == CONSIGNES_SYSTEME


def test_contexte_contient_source_page_et_texte():
    """Chaque chunk apparait balise, avec sa page et son texte."""
    contexte = formater_contexte(CHUNKS)
    assert 'page="2"' in contexte
    assert 'page="4"' in contexte
    assert "Amazon OpenSearch Serverless" in contexte
    assert "<document" in contexte and "</document>" in contexte


def test_nom_de_fichier_sans_uri_s3():
    """La source affichee est le NOM du fichier, pas l'URI S3 complete."""
    contexte = formater_contexte(CHUNKS)
    assert 'source="exemple_cahier_des_charges.pdf"' in contexte
    assert "s3://" not in contexte


def test_question_presente_dans_le_message():
    """La question de l'utilisateur figure bien dans le bloc utilisateur."""
    question = "Quelle base vectorielle est utilisee ?"
    prompt = construire_prompt(question, CHUNKS)
    assert question in prompt["utilisateur"]
    assert "Contexte :" in prompt["utilisateur"]
