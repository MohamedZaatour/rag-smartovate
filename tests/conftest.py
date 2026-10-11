# ============================================================
#  conftest.py : fichier SPECIAL de pytest, lu automatiquement
#  avant les tests. On y met ce qui est commun a TOUS les tests.
# ============================================================

import pytest

from rag import generation, retrieval


@pytest.fixture(autouse=True)
def vider_les_caches():
    """Vide le cache des clients AWS avant ET apres chaque test.

    Depuis le Sprint 4, les clients sont memorises par @lru_cache (perf API).
    Sans ce nettoyage, un test reutiliserait la DOUBLURE (faux client) du test
    precedent au lieu de la sienne -> resultats faux.
    autouse=True : s'applique a tous les tests, sans rien modifier dans ces tests.
    """
    retrieval._clients.cache_clear()
    generation._client_claude.cache_clear()
    yield                                   # <- le test s'execute ici
    retrieval._clients.cache_clear()
    generation._client_claude.cache_clear()
