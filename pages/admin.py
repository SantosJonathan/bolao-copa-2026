import streamlit as st
import os
from utils.database import (
    save_placar_real, save_classificacao_real,
    get_placares_reais, get_classificacao_real,
)
from utils.scoring import TIMES_GRUPO

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brasil2026")

JOGOS_INFO = [
    ('jogo1', 'Jogo 1 · 13/06', '🇲🇦 Marrocos'),
    ('jogo2', 'Jogo 2 · 19/06', '🇭🇹 Haiti'),
    ('jogo3', 'Jogo 3 · 24/06', '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia'),
]


def render():
    st.markdown("""
    <div style="background:rgba(200,16,46,0.08); border:1px solid rgba(200,16,46,0.25);
                border-radius:12px; padding:12px 16px; margin-bottom:16px;">
        <span style="font-family:'Barlow Condensed',sans-serif; color:rgba(255,255,255,0.7);
                     font-size:0.9rem; font-weight:700; letter-spacing:0.5px;">
            ⚙️ ÁREA EXCLUSIVA DO ORGANIZADOR — protegida por senha
        </span>
    </div>
    """, unsafe_allow_html=True)

    senha = st.text_input("Senha do administrador", type="password", key="admin_senha")

    if senha != ADMIN_PASSWORD:
        if senha:
            st.error("❌ Senha incorreta!")
        return

    st.success("✅ Acesso liberado!")

    placares_reais = get_placares_reais()

    # ── Placares reais ────────────────────────────────────
    st.markdown('<div class="section-title">INSERIR PLACARES REAIS</div>', unsafe_allow_html=True)

    for jkey, jlabel, jadv in JOGOS_INFO:
        real = placares_reais.get(jkey, {})
        st.markdown(f"<div class='admin-section'>", unsafe_allow_html=True)
        st.markdown(f"**{jlabel} — Brasil × {jadv}**")

        if real.get('encerrado'):
            st.success(f"✅ Salvo: Brasil {real['brasil']} × {real['adversario']}")

        c1, cx, c2 = st.columns([4, 1, 4])
        with c1:
            gb = st.number_input(
                f"Gols Brasil ({jkey})", min_value=0, max_value=20,
                value=int(real['brasil']) if real.get('brasil') is not None else 0,
                key=f"admin_br_{jkey}",
            )
        with cx:
            st.markdown(
                "<div style='text-align:center;margin-top:28px;color:rgba(255,255,255,0.4);"
                "font-family:Bebas Neue,sans-serif;font-size:1.3rem;'>×</div>",
                unsafe_allow_html=True)
        with c2:
            ga = st.number_input(
                f"Gols Adv ({jkey})", min_value=0, max_value=20,
                value=int(real['adversario']) if real.get('adversario') is not None else 0,
                key=f"admin_adv_{jkey}",
            )

        if st.button(f"💾 Salvar — {jlabel}", key=f"save_{jkey}", use_container_width=True):
            save_placar_real(jkey, gb, ga)
            st.success(f"Placar salvo: Brasil {gb} × {ga}")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Classificação real ────────────────────────────────
    st.markdown('<div class="section-title">CLASSIFICAÇÃO FINAL DO GRUPO C</div>', unsafe_allow_html=True)
    classif_real = get_classificacao_real()

    st.markdown("<div class='admin-section'>", unsafe_allow_html=True)
    ordem = []
    TIMES_UPPER = [t.upper() for t in TIMES_GRUPO]
    for i in range(1, 5):
        atual = classif_real.get(i, TIMES_GRUPO[i-1])
        # busca case-insensitive para o índice
        atual_up = atual.upper()
        idx = next((j for j, t in enumerate(TIMES_UPPER) if t == atual_up), i-1)
        escolha = st.selectbox(f"{i}º Colocado", TIMES_GRUPO, index=idx, key=f"real_c{i}")
        ordem.append(escolha)
        ordem.append(escolha)

    if st.button("💾 Salvar Classificação Final", key="save_classif", use_container_width=True):
        if len(set(ordem)) != 4:
            st.error("❌ Todos os times devem ser diferentes!")
        else:
            # Normaliza para maiúsculas — igual ao que o formulário salva
            save_classificacao_real([t.upper() for t in ordem])
            st.success("✅ Classificação salva!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:16px; padding:12px; background:rgba(255,255,255,0.04);
                border-radius:8px;">
        <p style="font-family:'Barlow',sans-serif; font-size:0.78rem;
                  color:rgba(255,255,255,0.4); margin:0;">
            💡 Para trocar a senha, defina a variável de ambiente
            <code>ADMIN_PASSWORD</code> no Streamlit Cloud em
            <b>Settings → Secrets</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
