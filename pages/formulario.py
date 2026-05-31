import streamlit as st
from datetime import date
from utils.database import (
    save_palpite, palpite_enviado,
    get_palpite_completo_por_nome,
)
from utils.scoring import TIMES_GRUPO

ADVERSARIOS = {
    'jogo1': {'nome': 'MARROCOS', 'data': '13/06'},
    'jogo2': {'nome': 'HAITI',    'data': '19/06'},
    'jogo3': {'nome': 'ESCÓCIA',  'data': '24/06'},
}

# ── CSS do modelo original ─────────────────────────────────
MATCH_CSS = """
<style>
.stApp { background-color: #2a1b6b; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 720px; }
h1, h2, h3, h4, p, label, span, div { color: #ffffff; }
.card {
    background: #ffffff; color: #2a1b6b; border-radius: 14px;
    padding: 16px; margin-bottom: 14px;
}
.card * { color: #2a1b6b; }
.title-bar { display:flex; justify-content:space-between; align-items:baseline; }
.title-bar h1 { font-size: 2rem; margin:0; font-weight: 900; text-transform: uppercase; }
.grupo { color: #00c853; font-weight: 800; font-size: 1.2rem; }
.brasil-banner {
    display:flex; align-items:center; background:#fff; border-radius:14px; overflow:hidden;
    margin-bottom: 14px;
}
.brasil-flag {
    background:#009c3b; width:50%; padding:18px; display:flex; justify-content:center; align-items:center;
}
.brasil-diamond {
    background:#ffdf00; width:120px; height:64px;
    clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%);
    display:flex; justify-content:center; align-items:center;
}
.brasil-circle {
    background:#2a1b6b; width:32px; height:32px; border-radius:50%;
    display:flex; justify-content:center; align-items:center;
    font-size:7px; color:#fff; font-weight:bold; text-align:center; line-height:1.1;
}
.brasil-name { flex:1; text-align:center; font-size:2.5rem; font-weight:900; color:#2a1b6b; letter-spacing:4px; }
.match-header { text-align:center; font-weight:900; padding:6px 0; color:#2a1b6b !important; }
.match-info { text-align:center; font-weight:700; font-size:0.85rem; padding-top:6px; border-top:1px solid #ddd;}
.match-info * { color:#2a1b6b !important; }
.red { color:#e53935 !important; font-weight:900; }
.footer-banner {
    background:#fff; border-radius:14px; padding:14px; display:flex; gap:14px; align-items:center;
}
.money-box {
    background:#009c3b; color:#fff; padding:12px; border-radius:10px; text-align:center; min-width:130px;
}
.money-box * { color:#fff !important; }
.prize { text-align:center; }
.prize .pts { color:#e53935 !important; font-weight:900; font-size:1.1rem; }
.prize .lbl { color:#2a1b6b !important; font-weight:700; font-size:0.75rem; }
.stNumberInput input, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background:#fff !important; color:#2a1b6b !important;
}
div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label, div[data-testid="stDateInput"] label { color:#fff !important; font-weight:700; }
.stButton button {
    background:#ffdf00 !important; color:#2a1b6b !important; font-weight:900 !important;
    border:none !important; border-radius:10px !important;
    padding:12px 24px !important; width:100% !important; font-size:1.1rem !important;
}
/* saved badge */
.saved-badge {
    background: rgba(0,156,59,0.15);
    border: 1px solid #009c3b;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
</style>
"""

# ── Descrição + Pontuação ──────────────────────────────────
def _render_desc_pts():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
          <h4>DESCRIÇÃO:</h4>
          <p>Preencha os placares dos jogos da Seleção Brasileira na primeira fase
          da Copa do Mundo e, ao final, ordene os times do Grupo C da 1ª ao 4ª
          colocação. Ganha quem acertar os placares e a ordem final dos colocados!</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
          <h4>🏆 PONTUAÇÃO:</h4>
          <p>⭐ <b>CRAVAR O RESULTADO EXATO DE CADA JOGO:</b><br><span class="red">50 PONTOS</span></p>
          <p>⭐ <b>ACERTAR UM COLOCADO INDIVIDUALMENTE:</b><br><span class="red">30 PONTOS</span></p>
          <p>⭐ <b>ACERTAR A ORDEM EXATA DA CLASSIFICAÇÃO (GABARITANDO):</b><br><span class="red">100 PONTOS</span></p>
        </div>
        """, unsafe_allow_html=True)


# ── Faixa final ────────────────────────────────────────────
def _render_footer():
    st.markdown("""
    <div class="footer-banner">
      <div class="money-box">
        💵<br>
        <b style="font-size:0.7rem;">VALOR PARA PARTICIPAR<br>DO BOLÃO:</b><br>
        <span style="font-size:1.6rem; font-weight:900;">R$ 20,00</span><br>
        <b style="font-size:0.7rem;">POR PARTICIPANTE</b>
      </div>
      <div style="flex:1;">
        <p style="text-align:center; color:#2a1b6b; font-weight:900;">CRAVE OS PLACARES. ACERTE A ORDEM. SEJA O CAMPEÃO!</p>
        <div style="display:flex; justify-content:space-around;">
          <div class="prize"><div class="pts">50 PONTOS</div><div class="lbl">POR PLACAR EXATO</div></div>
          <div class="prize"><div class="pts">30 PONTOS</div><div class="lbl">POR COLOCADO INDIVIDUAL</div></div>
          <div class="prize"><div class="pts">100 PONTOS</div><div class="lbl">GABARITANDO!</div></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:0.75rem; margin-top:10px;">⭐ <b>OBS.:</b> Em caso de empate, o critério de desempate será: '
        '1º mais pontos por placares exatos, 2º mais acertos de ordem, 3º sorteio.</p>',
        unsafe_allow_html=True,
    )


# ── Palpite já enviado (somente leitura) ───────────────────
def _render_palpite_salvo(nome: str, dados: dict):
    st.markdown(f"""
    <div class="saved-badge">
        <div style="font-family:'Barlow Condensed',sans-serif; color:#7fffb0; font-size:1rem; font-weight:700;">
            ✅ Palpite de <b>{nome}</b> registrado em {dados['enviado_em']}
        </div>
        <div style="font-family:'Barlow',sans-serif; color:rgba(255,255,255,0.55); font-size:0.8rem; margin-top:4px;">
            Os palpites são definitivos e não podem ser alterados após o envio.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mostra os jogos no estilo do modelo (somente leitura)
    for i, (jkey, info) in enumerate(ADVERSARIOS.items()):
        p = dados['palpites'].get(jkey)
        gb, ga = p if p else (0, 0)
        st.markdown(
            f'<div class="card"><div class="match-header">JOGO {i+1} ({info["data"]})</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4, c5 = st.columns([3, 1, 0.4, 1, 3])
        with c1:
            st.markdown(f"### **BRASIL**")
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.6rem; font-weight:900; color:#2a1b6b;'>{gb}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown("### X")
        with c4:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.6rem; font-weight:900; color:#2a1b6b;'>{ga}</div>", unsafe_allow_html=True)
        with c5:
            st.markdown(f"### **{info['nome']}**")
        st.markdown(
            '<div class="match-info">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div></div>',
            unsafe_allow_html=True,
        )

    _render_desc_pts()
    _render_footer()


# ── Formulário principal ───────────────────────────────────
def render():
    # Injeta o CSS do modelo original
    st.markdown(MATCH_CSS, unsafe_allow_html=True)

    # Header
    st.markdown(
        '<div class="title-bar"><h1>Jogos do Brasil</h1><span class="grupo">GRUPO C</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <div class="brasil-banner">
      <div class="brasil-flag">
        <div class="brasil-diamond">
          <div class="brasil-circle">ORDEM E<br>PROGRESSO</div>
        </div>
      </div>
      <div class="brasil-name">BRASIL</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Identificação ────────────────────────────────────
    st.markdown('<div class="section-title">IDENTIFICAÇÃO</div>', unsafe_allow_html=True)
    nome = st.text_input("Seu nome completo", placeholder="Digite seu nome aqui...", key="nome_input")

    if not nome.strip():
        st.markdown("""
        <div style="text-align:center; padding:24px; color:rgba(255,255,255,1);
                    font-family:'Barlow Condensed',sans-serif; font-size:1rem; letter-spacing:1px;">
            DIGITE SEU NOME PARA CONTINUAR 👆
        </div>
        """, unsafe_allow_html=True)
        _render_desc_pts()
        _render_footer()
        return

    nome = nome.strip()

    if palpite_enviado(nome):
        dados = get_palpite_completo_por_nome(nome)
        _render_palpite_salvo(nome, dados)
        return

    # Aviso imutabilidade
    st.markdown("""
    <div style="background:rgba(255,215,0,0.07); border:1px solid rgba(255,215,0,1);
                border-radius:10px; padding:10px 14px; margin-bottom:4px;">
        <span style="font-family:'Barlow',sans-serif; color:rgba(255,255,255,1); font-size:0.82rem;">
            ⚠️ <b>Atenção:</b> após confirmar, seu palpite <b>não poderá ser alterado</b>.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Jogos (layout exato do modelo) ───────────────────
    placares = {}
    for i, (jkey, info) in enumerate(ADVERSARIOS.items()):
        st.markdown(
            f'<div class="card"><div class="match-header">JOGO {i+1} ({info["data"]})</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4, c5 = st.columns([3, 1, 0.4, 1, 3])
        with c1:
            st.markdown(f"### **BRASIL**")
        with c2:
            h = st.number_input("Casa", min_value=0, max_value=20, value=0, step=1,
                                key=f"h{i}", label_visibility="collapsed")
        with c3:
            st.markdown("### X")
        with c4:
            a = st.number_input("Fora", min_value=0, max_value=20, value=0, step=1,
                                key=f"a{i}", label_visibility="collapsed")
        with c5:
            st.markdown(f"### **{info['nome']}**")

        st.markdown(
        '<div class="match-info">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div></div>',
        unsafe_allow_html=True,
    )
        placares[jkey] = (h, a)

    # ── Descrição + Pontuação ────────────────────────────
    _render_desc_pts()

    # ── Classificação ────────────────────────────────────
    st.markdown('<div class="card"><h3 style="text-align:center; color:#2a1b6b !important;">🏆 CLASSIFICAÇÃO DO GRUPO C</h3>', unsafe_allow_html=True)
    times = ["", "BRASIL", "MARROCOS", "HAITI", "ESCÓCIA"]
    selecionados = []
    classif_ok = True
    for pos in range(1, 5):
        escolha = st.selectbox(f"{pos}º Colocado", times, key=f"pos{pos}")
        if escolha and escolha in selecionados:
            st.warning(f"⚠️ {escolha} já selecionado!")
            classif_ok = False
        selecionados.append(escolha)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Nome + Data ──────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"<div style='font-family:sans-serif; color:#2a1b6b; font-weight:700; margin-bottom:4px;'>NOME</div>"
                    f"<div style='font-size:1rem; font-weight:700; color:#2a1b6b; padding:8px 0;'>{nome}</div>",
                    unsafe_allow_html=True)
    with c2:
        hoje = date.today().strftime("%d/%m/%Y")
        st.markdown(f"<div style='font-family:sans-serif; color:#2a1b6b; font-weight:700; margin-bottom:4px;'>DATA</div>"
                    f"<div style='font-size:1rem; font-weight:700; color:#2a1b6b; padding:8px 0;'>{hoje}</div>",
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Faixa final ──────────────────────────────────────
    _render_footer()

    # ── Confirmação 2 etapas ─────────────────────────────
    if "confirmar_palpite" not in st.session_state:
        st.session_state.confirmar_palpite = False

    if not st.session_state.confirmar_palpite:
        if st.button("ENVIAR PALPITE"):
            if "" in selecionados or len(set(s for s in selecionados if s)) != 4:
                st.error("❌ Selecione os 4 colocados sem repetir times.")
            elif not classif_ok:
                st.error("❌ Corrija a classificação — times repetidos.")
            else:
                st.session_state.confirmar_palpite = True
                st.rerun()
    else:
        st.markdown("""
        <div style="background:rgba(200,16,46,1); border:1px solid rgba(200,16,46,1);
                    border-radius:10px; padding:12px 16px; margin-bottom:10px;">
            <b style="color:#ffffff;">⚠️ CONFIRME SEU PALPITE — esta ação é irreversível!</b>
        </div>
        """, unsafe_allow_html=True)
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("✅ SIM, ENVIAR DEFINITIVAMENTE"):
                classif_final = [s for s in selecionados if s]
                ok = save_palpite(nome, placares, tuple(classif_final))
                st.session_state.confirmar_palpite = False
                if ok:
                    st.success(f"🎉 Palpite de **{nome}** registrado! Boa sorte🍀")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Palpite já registrado e não pode ser alterado.")
        with col_cancel:
            if st.button("✏️ VOLTAR E EDITAR"):
                st.session_state.confirmar_palpite = False
                st.rerun()
