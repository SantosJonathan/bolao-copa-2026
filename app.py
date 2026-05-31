import streamlit as st

st.set_page_config(
    page_title="Bolão Copa 2026 · Grupo C",
    page_icon="🇧🇷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# CRÍTICO para mobile: injeta viewport meta tag que o Streamlit não coloca
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
  /* Remove padding lateral padrão do Streamlit que causa scroll horizontal */
  .appview-container .main .block-container {
      padding-left: 0.75rem !important;
      padding-right: 0.75rem !important;
  }
  /* Garante que nenhum elemento ultrapasse a tela */
  * { max-width: 100%; box-sizing: border-box; }
  img, video, iframe { max-width: 100% !important; }
  /* Esconde menu e rodapé do Streamlit */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

with open("utils/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from utils.database import init_db
import pages.formulario as formulario
import pages.ranking    as ranking
import pages.admin      as admin

init_db()

tab1, tab2, tab3 = st.tabs(["📝 PARTICIPAR", "🏆 RANKING", "⚙️ ADMIN"])

with tab1:
    formulario.render()
with tab2:
    ranking.render()
with tab3:
    admin.render()
