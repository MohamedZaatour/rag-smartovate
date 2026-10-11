# ============================================================
#  Sprint 4 / US 4.1 - Interface Streamlit « Smartovate AI Assistant »
#  - Historique des conversations (en memoire de session)
#  - Bulles : utilisateur a droite, assistant a gauche
#  - Rendu Markdown complet (titres, listes, code, tableaux)
#  - Section « Sources utilisees » repliable sous chaque reponse
#  - Palette Smartovate : bleu nuit, blanc casse, accent teal
#  Lancement (depuis src/) :  streamlit run frontend/app.py
# ============================================================

import html
import re
import uuid

import markdown as md
import requests
import streamlit as st

from api_client import api_en_ligne, poser_question

# ---------- Parametres d'affichage ----------
NOM_UTILISATEUR = "Mohamed Zaatour"   # pas d'authentification : simple libelle
INITIALES = "MZ"
SUGGESTIONS = [
    (":material/database:", "Quelle base vectorielle est utilisée\u00a0?"),
    (":material/checklist:", "Quels sont les livrables attendus du projet\u00a0?"),
    (":material/memory:", "Quelles technologies sont utilisées pour le backend\u00a0?"),
]

st.set_page_config(
    page_title="Smartovate AI Assistant", page_icon=":material/layers:", layout="wide"
)

# ---------- Icones SVG (meme style partout) ----------
ICONE_LOGO = (
    "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
    "stroke-linecap='round' stroke-linejoin='round'><path d='m12 2 10 5-10 5L2 7z'/>"
    "<path d='m2 17 10 5 10-5'/><path d='m2 12 10 5 10-5'/></svg>"
)
ICONE_IA = (
    "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
    "stroke-linecap='round' stroke-linejoin='round'><path d='M12 3l1.9 5.1L19 10l-5.1 "
    "1.9L12 17l-1.9-5.1L5 10l5.1-1.9z'/><path d='M19 3v4'/><path d='M21 5h-4'/></svg>"
)
ICONE_DOC = (
    "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
    "stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 "
    "2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><path d='M14 2v6h6'/><path d='M16 13H8'/>"
    "<path d='M16 17H8'/></svg>"
)

# ---------- Style (charte : bleu nuit / blanc casse / teal) ----------
st.markdown(
    """
<style>
:root{
  --navy:#1E2E3E; --navy-deep:#15212D; --bg:#F6F7F8; --surface:#FFFFFF;
  --border:#E2E7EB; --muted:#6B7B89; --accent:#1C9AAA; --accent-soft:#E4F3F5;
  --radius:14px; --radius-sm:10px;
}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stDecoration"]{display:none;}
[data-testid="stMainBlockContainer"]{max-width:860px;padding:3rem 1.5rem 1.5rem;}
[data-testid="stBottomBlockContainer"]{max-width:860px;padding:.5rem 1.5rem 1.4rem;}

/* ---------- Barre laterale ---------- */
section[data-testid="stSidebar"]{background:var(--navy-deep);color:#D5DEE5;}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] svg{color:#8FA3B3;}
.brand{display:flex;align-items:center;gap:10px;margin:0 0 18px;}
.brand-logo{width:34px;height:34px;border-radius:var(--radius-sm);background:var(--accent);
  color:#fff;display:flex;align-items:center;justify-content:center;}
.brand-logo svg{width:18px;height:18px;}
.brand-name{font-weight:700;font-size:1rem;color:#FFFFFF;line-height:1.15;}
.brand-sub{font-size:.75rem;color:#8FA3B3;}
.side-label{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:#7F93A3;
  margin:22px 0 6px 4px;}
.side-empty{font-size:.82rem;color:#7F93A3;margin-left:4px;}
section[data-testid="stSidebar"] button p{color:inherit !important;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  border-radius:var(--radius-sm);font-weight:600;color:#fff;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{
  justify-content:flex-start;text-align:left;border-radius:var(--radius-sm);
  padding:6px 10px;min-height:0;font-size:.86rem;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]{color:#C2CDD6;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] > div,
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] > div{
  justify-content:flex-start;width:100%;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover{
  background:rgba(255,255,255,.06);color:#FFFFFF;}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{
  background:rgba(28,154,170,.18);border:none;border-left:3px solid var(--accent);color:#FFFFFF;}
.side-footer{margin-top:28px;padding-top:14px;border-top:1px solid rgba(255,255,255,.08);
  display:flex;align-items:center;gap:10px;font-size:.85rem;color:#D5DEE5;}

/* ---------- En-tete ---------- */
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;
  padding-bottom:14px;margin-bottom:4px;border-bottom:1px solid var(--border);}
.topbar .title{font-size:1.25rem;font-weight:700;color:var(--navy);letter-spacing:-.01em;}
.topbar .subtitle{font-size:.84rem;color:var(--muted);margin-top:2px;}
.status{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:999px;
  font-size:.74rem;font-weight:600;border:1px solid var(--border);background:var(--surface);
  color:var(--navy);white-space:nowrap;}
.status .dot{width:7px;height:7px;border-radius:50%;background:#22A45D;}
.status.off .dot{background:#D9534F;}

/* ---------- Messages ---------- */
.msg-row{display:flex;gap:10px;align-items:flex-start;margin:18px 0 10px;}
.msg-row.user{justify-content:flex-end;}
.avatar{width:32px;height:32px;border-radius:50%;flex:0 0 32px;display:flex;
  align-items:center;justify-content:center;font-size:.72rem;font-weight:700;}
.avatar.user{background:var(--navy);color:#FFFFFF;}
.avatar.bot{background:var(--accent-soft);color:var(--accent);}
.avatar svg{width:16px;height:16px;}
.bubble{max-width:74%;padding:11px 15px;border-radius:var(--radius);font-size:.94rem;line-height:1.6;}
.bubble.user{background:var(--navy);color:#FFFFFF;border-top-right-radius:4px;white-space:pre-wrap;}
.bubble.assistant{background:var(--surface);color:var(--navy);border:1px solid var(--border);
  border-top-left-radius:4px;box-shadow:0 1px 2px rgba(21,33,45,.04);}
.bubble.erreur{background:#FDF4F4;border-color:#F1C4C2;color:#8A2C2A;}

/* Markdown dans les reponses */
.bubble p{margin:0 0 .6em;font-size:.94rem;}
.bubble p:last-child{margin-bottom:0;}
.bubble h1,.bubble h2,.bubble h3,.bubble h4{color:var(--navy);margin:.2em 0 .45em;
  line-height:1.3;padding:0;font-weight:700;}
.bubble h1{font-size:1.08rem !important;}
.bubble h2{font-size:1.02rem !important;}
.bubble h3,.bubble h4{font-size:.96rem !important;}
.bubble ul,.bubble ol{margin:.25em 0 .6em;padding-left:1.25rem;}
.bubble li{margin:.15em 0;font-size:.94rem;}
.bubble code{background:#EEF2F5;color:var(--navy);padding:1px 6px;border-radius:6px;font-size:.84em;}
.bubble pre{background:var(--navy-deep);color:#E3EAF0;padding:12px 14px;
  border-radius:var(--radius-sm);overflow-x:auto;margin:.5em 0;}
.bubble pre code{background:transparent;color:inherit;padding:0;}
.bubble pre,.bubble pre code,.bubble pre span{font-size:.82rem !important;line-height:1.55;}
.bubble table{width:100%;border-collapse:collapse;margin:.5em 0 .7em;font-size:.86rem;}
.bubble th{background:#F1F4F6;text-align:left;font-weight:600;}
.bubble th,.bubble td{border:1px solid var(--border);padding:6px 10px;}

/* Indicateur de chargement */
.typing{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:.88rem;}
.dots{display:inline-flex;gap:4px;}
.dots i{width:6px;height:6px;border-radius:50%;background:var(--accent);opacity:.3;
  animation:blink 1.2s infinite;}
.dots i:nth-child(2){animation-delay:.2s;}
.dots i:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%,80%,100%{opacity:.25;}40%{opacity:1;}}

/* ---------- Sources utilisees ---------- */
[data-testid="stMainBlockContainer"] [data-testid="stExpander"]{margin:-4px 0 4px 42px;max-width:560px;}
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] details{
  border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);}
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary p{font-size:.82rem;color:var(--muted);}
.src-head,.src-row{display:grid;grid-template-columns:18px 1fr 54px 46px;gap:8px;
  align-items:center;font-size:.83rem;}
.src-head{color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;
  padding:0 0 6px;border-bottom:1px solid var(--border);}
.src-head span:first-child{grid-column:1 / 3;}
.src-row{padding:7px 0;border-bottom:1px solid #F0F2F4;color:var(--navy);}
.src-row:last-child{border-bottom:none;}
.src-row svg{width:15px;height:15px;color:var(--accent);}
.src-nom{font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.src-page,.src-score{color:var(--muted);font-variant-numeric:tabular-nums;}

/* ---------- Ecran d'accueil ---------- */
.welcome{text-align:center;margin:8vh auto 26px;max-width:520px;}
.welcome-icon{width:52px;height:52px;border-radius:16px;background:var(--accent-soft);
  color:var(--accent);display:flex;align-items:center;justify-content:center;margin:0 auto 14px;}
.welcome-icon svg{width:26px;height:26px;}
.welcome-title{font-size:1.4rem;font-weight:700;color:var(--navy);}
.welcome-text{font-size:.9rem;color:var(--muted);margin-top:6px;line-height:1.5;}
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]{
  min-height:88px;align-items:flex-start;justify-content:flex-start;text-align:left;
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:14px 16px;box-shadow:0 1px 2px rgba(21,33,45,.04);color:var(--navy);}
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:hover{
  border-color:var(--accent);color:var(--navy);box-shadow:0 4px 14px rgba(21,33,45,.08);}
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"] [data-testid="stIconMaterial"]{
  color:var(--accent);}

/* ---------- Barre de saisie ---------- */
[data-testid="stChatInput"]{border:1px solid #C9D2DA;border-radius:var(--radius);
  background:var(--surface);box-shadow:0 2px 12px rgba(21,33,45,.07);}
[data-testid="stChatInput"]:focus-within{border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(28,154,170,.15);}
[data-testid="stChatInputSubmitButton"]{background:var(--accent) !important;
  border-radius:var(--radius-sm) !important;}
[data-testid="stChatInputSubmitButton"] svg{color:#FFFFFF !important;fill:#FFFFFF !important;}
[data-testid="stChatInputSubmitButton"]:disabled{background:#BFDFE3 !important;}
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Rendu Markdown des reponses ----------
_LISTE = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
_TABLE = re.compile(r"^\s*\|")
_TITRE = re.compile(r"^\s*#{1,6}\s")


def preparer_markdown(texte):
    """python-markdown exige une ligne vide avant une liste, un tableau ou un titre :
    on l'ajoute si le modele l'a oubliee (sinon la liste s'affiche sur une ligne)."""
    sortie, dans_code = [], False
    for ligne in texte.split("\n"):
        if ligne.strip().startswith("```"):
            if not dans_code and sortie and sortie[-1].strip():
                sortie.append("")
            dans_code = not dans_code
        elif not dans_code and sortie and sortie[-1].strip():
            prec = sortie[-1]
            if ((_LISTE.match(ligne) and not _LISTE.match(prec))
                    or (_TABLE.match(ligne) and not _TABLE.match(prec))
                    or _TITRE.match(ligne)):
                sortie.append("")
        sortie.append(ligne)
    return "\n".join(sortie)


def markdown_en_html(texte):
    return md.markdown(
        preparer_markdown(texte), extensions=["tables", "fenced_code", "sane_lists", "nl2br"]
    )


# ---------- Composants d'affichage ----------
def bulle_user(texte):
    st.markdown(
        f"<div class='msg-row user'><div class='bubble user'>{html.escape(texte)}</div>"
        f"<div class='avatar user'>{INITIALES}</div></div>",
        unsafe_allow_html=True,
    )


def bulle_assistant(texte, erreur=False):
    classe = "bubble assistant erreur" if erreur else "bubble assistant"
    corps = html.escape(texte) if erreur else markdown_en_html(texte)
    st.markdown(
        f"<div class='msg-row'><div class='avatar bot'>{ICONE_IA}</div>"
        f"<div class='{classe}'>{corps}</div></div>",
        unsafe_allow_html=True,
    )


def bloc_sources(sources):
    """Section repliable « Sources utilisees » : document, page, score."""
    if not sources:
        return
    def ligne(s):
        score = s.get("score")
        score_txt = f"{score:.2f}" if score is not None else "–"
        return (
            f"<div class='src-row'>{ICONE_DOC}"
            f"<span class='src-nom'>{html.escape(str(s.get('source', '')))}</span>"
            f"<span class='src-page'>p. {s.get('page', '–')}</span>"
            f"<span class='src-score'>{score_txt}</span></div>"
        )

    lignes = "".join(ligne(s) for s in sources)
    with st.expander(f"Sources utilisées ({len(sources)})", icon=":material/description:"):
        st.markdown(
            "<div class='src-head'><span>Document</span><span>Page</span><span>Score</span></div>"
            + lignes,
            unsafe_allow_html=True,
        )


def indicateur_chargement():
    st.markdown(
        f"<div class='msg-row'><div class='avatar bot'>{ICONE_IA}</div>"
        f"<div class='bubble assistant typing'><span class='dots'><i></i><i></i><i></i></span>"
        f"Recherche dans la base de connaissances…</div></div>",
        unsafe_allow_html=True,
    )


# ---------- Etat : plusieurs conversations (en session) ----------
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    st.session_state.conv_courante = None


def nouvelle_conversation():
    """Ouvre une conversation vide (sauf si on est deja sur une conversation vide)."""
    courante = st.session_state.conversations.get(st.session_state.conv_courante)
    if courante is not None and not courante["messages"]:
        return
    cid = uuid.uuid4().hex[:8]
    st.session_state.conversations[cid] = {"titre": None, "messages": []}
    st.session_state.conv_courante = cid


if st.session_state.conv_courante is None:
    nouvelle_conversation()
conv = st.session_state.conversations[st.session_state.conv_courante]

# ---------- Barre laterale ----------
with st.sidebar:
    st.markdown(
        f"<div class='brand'><div class='brand-logo'>{ICONE_LOGO}</div><div>"
        f"<div class='brand-name'>Smartovate</div><div class='brand-sub'>AI Assistant</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("Nouvelle conversation", icon=":material/add:", type="primary", width="stretch"):
        nouvelle_conversation()
        st.rerun()

    st.markdown("<div class='side-label'>Conversations récentes</div>", unsafe_allow_html=True)
    precedentes = [
        (cid, c) for cid, c in reversed(list(st.session_state.conversations.items()))
        if c["messages"]
    ]
    if not precedentes:
        st.markdown(
            "<div class='side-empty'>Aucune conversation pour le moment.</div>",
            unsafe_allow_html=True,
        )
    for cid, c in precedentes:
        titre = c["titre"] or "Sans titre"
        libelle = titre if len(titre) <= 32 else titre[:31] + "…"
        actif = cid == st.session_state.conv_courante
        if st.button(libelle, key=f"conv_{cid}", icon=":material/chat_bubble:",
                     type="secondary" if actif else "tertiary", width="stretch"):
            st.session_state.conv_courante = cid
            st.rerun()

    st.markdown(
        f"<div class='side-footer'><div class='avatar user'>{INITIALES}</div>"
        f"{NOM_UTILISATEUR}</div>",
        unsafe_allow_html=True,
    )

# ---------- En-tete ----------
en_ligne = api_en_ligne()
st.markdown(
    f"<div class='topbar'><div><div class='title'>Smartovate AI Assistant</div>"
    f"<div class='subtitle'>Interrogez la base documentaire interne en langage naturel</div></div>"
    f"<div class='status {'' if en_ligne else 'off'}' title='OpenSearch + Bedrock'>"
    f"<span class='dot'></span>{'En ligne' if en_ligne else 'Hors ligne'}</div></div>",
    unsafe_allow_html=True,
)

# ---------- Question entrante : suggestion cliquee OU saisie ----------
saisie = st.chat_input("Posez votre question…")
question = st.session_state.pop("suggestion", None) or saisie

# ---------- Ecran d'accueil (conversation vide) ----------
if not conv["messages"] and not question:
    st.markdown(
        f"<div class='welcome'><div class='welcome-icon'>{ICONE_IA}</div>"
        f"<div class='welcome-title'>Comment puis-je vous aider ?</div>"
        f"<div class='welcome-text'>Posez une question sur la documentation interne de "
        f"Smartovate, ou commencez par l'une de ces suggestions.</div></div>",
        unsafe_allow_html=True,
    )
    colonnes = st.columns(3)
    for colonne, (icone, texte) in zip(colonnes, SUGGESTIONS):
        with colonne:
            if st.button(texte, icon=icone, key=f"sug_{texte[:16]}", width="stretch", wrap=True):
                st.session_state.suggestion = texte
                st.rerun()

# ---------- Historique de la conversation courante ----------
for m in conv["messages"]:
    if m["role"] == "user":
        bulle_user(m["content"])
    else:
        bulle_assistant(m["content"], erreur=m.get("erreur", False))
        bloc_sources(m.get("sources", []))

# ---------- Traitement d'une nouvelle question ----------
if question:
    conv["messages"].append({"role": "user", "content": question})
    if conv["titre"] is None:
        conv["titre"] = question            # le titre = la 1re question
    bulle_user(question)
    attente = st.empty()
    with attente:
        indicateur_chargement()
    erreur = None
    try:
        resultat = poser_question(question)
        conv["messages"].append({
            "role": "assistant",
            "content": resultat["reponse"],
            "sources": resultat.get("sources", []),
            "appel_llm": resultat.get("appel_llm", True),
        })
    # L'ordre compte : un Timeout est aussi une ConnectionError -> on le teste d'abord.
    except requests.exceptions.Timeout:
        erreur = ("L'API met trop de temps à répondre (délai dépassé). "
                  "Regardez le terminal uvicorn pour voir où elle bloque.")
    except requests.exceptions.ConnectionError:
        erreur = ("API injoignable. Vérifiez que le serveur (uvicorn) est lancé, "
                  "puis réessayez.")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        erreur = (f"L'API a renvoyé une erreur (code {code}). Vérifiez votre session AWS "
                  f"(aws sso login) et le message d'erreur dans le terminal uvicorn.")
    except Exception as e:                       # noqa: BLE001
        erreur = f"Erreur inattendue : {e}"
    if erreur:
        conv["messages"].append({"role": "assistant", "content": erreur, "erreur": True})
    # On relance le script : la barre laterale (titre) et l'historique se mettent a jour.
    st.rerun()
