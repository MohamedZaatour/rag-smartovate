# ============================================================
#  US 3.2 - Brique 1 : Construction du prompt
#  Assemble ce qu'on donnera a Claude : des CONSIGNES (system) +
#  un message UTILISATEUR (contexte des chunks + question).
#  Brique 100% "texte" : AUCUN appel AWS ici -> testable gratuitement.
#  Lancement (depuis src/) :  python -m rag.prompt
# ============================================================

# --- Les CONSIGNES (le "system") : le reglement donne a Claude ---
# Chaque regle repond a un critere d'acceptation du cahier des charges.
CONSIGNES_SYSTEME = """Tu es un assistant documentaire interne pour l'entreprise Smartovate.
Ta mission : repondre aux questions en t'appuyant UNIQUEMENT sur le contexte fourni.

Regles a respecter STRICTEMENT :
1. Utilise UNIQUEMENT les informations presentes dans le contexte ci-dessous.
   N'utilise jamais tes connaissances generales.
2. Cite systematiquement tes sources, au format [Source : nom_du_fichier, p. X].
3. Si la reponse ne figure PAS dans le contexte, reponds exactement :
   "Je ne trouve pas cette information dans la base documentaire."
   N'invente jamais de reponse.
4. Reponds en francais, de maniere claire et concise."""


def formater_contexte(chunks):
    """Transforme la liste de chunks en un bloc de texte balise.

    Chaque chunk devient une balise <document> qui porte sa source et sa page,
    pour que Claude puisse CITER (il ne peut citer que ce qu'il voit).
    """
    blocs = []
    for i, c in enumerate(chunks, start=1):
        # La source est une URI S3 complete ; on garde juste le nom du fichier
        # pour une citation lisible (ex: "exemple_cahier_des_charges.pdf").
        nom_fichier = str(c.get("source", "")).split("/")[-1]
        bloc = (
            f'<document id="{i}" source="{nom_fichier}" page="{c.get("page")}">\n'
            f'{c.get("texte", "").strip()}\n'
            f'</document>'
        )
        blocs.append(bloc)
    return "\n".join(blocs)


def construire_prompt(question, chunks):
    """Assemble le prompt final.

    Renvoie un dictionnaire pret pour la brique de generation :
        {"systeme": <consignes>, "utilisateur": <contexte + question>}
    On SEPARE les deux : les consignes iront dans le parametre 'system' de
    Converse, le reste dans 'messages'.
    """
    contexte = formater_contexte(chunks)
    message_utilisateur = (
        f"Contexte :\n{contexte}\n\n"
        f"Question : {question}"
    )
    return {"systeme": CONSIGNES_SYSTEME, "utilisateur": message_utilisateur}


# --- Test SANS AWS : on fabrique de faux chunks et on affiche le prompt ---
#     (python -m rag.prompt)  -> zero appel reseau, zero cout.
if __name__ == "__main__":
    faux_chunks = [
        {
            "texte": "Le systeme utilise Amazon OpenSearch Serverless comme base vectorielle.",
            "source": "s3://smartovate-rag-documents-mohamed/exemple_cahier_des_charges.pdf",
            "page": 1, "chunk_index": 0, "score": 0.63,
        },
        {
            "texte": "Un index k-NN est cree avec la dimension du modele Titan Embeddings.",
            "source": "s3://smartovate-rag-documents-mohamed/exemple_cahier_des_charges.pdf",
            "page": 4, "chunk_index": 3, "score": 0.59,
        },
    ]

    prompt = construire_prompt("Quelle base vectorielle est utilisee ?", faux_chunks)

    print("===== BLOC SYSTEME (les consignes) =====")
    print(prompt["systeme"])
    print("\n===== BLOC UTILISATEUR (contexte + question) =====")
    print(prompt["utilisateur"])
