"""
Bolão Copa do Mundo 2026 — Grupo C
Streamlit app — versão responsiva
"""

import streamlit as st

st.set_page_config(
    page_title="Bolão Copa 2026 · Grupo C",
    page_icon="🇧🇷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

with open("utils/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from utils.database import init_db
import pages.formulario as formulario
import pages.ranking    as ranking
import pages.admin      as admin

init_db()

# ── Header ─────────────────────────────────────────────────
st.markdown("""
 
    <div class="header-title">
        <span class="title-main">BOLÃO COPA 2026</span>
        <span class="title-sub">FASE DE GRUPOS</span>
    </div>

""", unsafe_allow_html=True)



# ── Tabs ────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 PARTICIPAR", "🏆 RANKING", "⚙️ ADMIN"])

with tab1:
    formulario.render()
with tab2:
    ranking.render()
with tab3:
    admin.render()
