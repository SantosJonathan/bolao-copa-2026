import streamlit as st
from datetime import date
from utils.database import (
    save_palpite, palpite_enviado,
    get_palpite_completo_por_nome,
)

ADVERSARIOS = {
    'jogo1': {'nome': 'MARROCOS', 'data': '13/06'},
    'jogo2': {'nome': 'HAITI',    'data': '19/06'},
    'jogo3': {'nome': 'ESCÓCIA',  'data': '24/06'},
}

MATCH_CSS = """
<style>
html { -webkit-text-size-adjust:100%; text-size-adjust:100%; }
.stApp { background-color:#2a1b6b !important; }
.block-container {
    padding-top:1rem !important; padding-bottom:3rem !important;
    padding-left:0.75rem !important; padding-right:0.75rem !important;
    max-width:720px !important;
}
h1,h2,h3,h4,p,label,span { color:#fff; }

.title-bar { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:4px; }
.title-bar h1 { font-size:clamp(1.3rem,5.5vw,2rem); margin:0; font-weight:900; text-transform:uppercase; color:#fff; }
.grupo { color:#00c853; font-weight:800; font-size:clamp(1rem,4vw,1.2rem); }

.brasil-banner { display:flex; align-items:center; background:#fff; border-radius:14px; overflow:hidden; margin-bottom:14px; min-height:clamp(60px,16vw,90px); }
.brasil-flag { background:#009c3b; width:45%; flex-shrink:0; padding:clamp(10px,3vw,18px); display:flex; justify-content:center; align-items:center; }
.brasil-diamond { background:#ffdf00; width:clamp(70px,18vw,120px); height:clamp(38px,10vw,64px); clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%); display:flex; justify-content:center; align-items:center; }
.brasil-circle { background:#2a1b6b; width:clamp(20px,5vw,32px); height:clamp(20px,5vw,32px); border-radius:50%; display:flex; justify-content:center; align-items:center; font-size:clamp(5px,1.2vw,7px); color:#fff; font-weight:bold; text-align:center; line-height:1.1; }
.brasil-name { flex:1; text-align:center; font-size:clamp(1.5rem,7vw,2.5rem); font-weight:900; color:#2a1b6b; letter-spacing:clamp(1px,1vw,4px); padding:0 8px; }

.section-title { font-weight:900; font-size:clamp(0.9rem,3.5vw,1.1rem); color:#fff; letter-spacing:2px; border-left:4px solid #ffdf00; padding-left:10px; margin:18px 0 10px 0; text-transform:uppercase; }

.card { background:#fff; color:#2a1b6b; border-radius:14px; padding:clamp(10px,3vw,16px); margin-bottom:14px; }
.card * { color:#2a1b6b; }

/* ── MATCH CARD ─────────────────────────────── */
.match-card { background:#fff; border-radius:14px; overflow:hidden; margin-bottom:14px; }
.match-header-txt {
    text-align:center; font-weight:900;
    font-size:clamp(0.82rem,3.5vw,1rem);
    padding:10px; color:#2a1b6b;
    letter-spacing:1px; text-transform:uppercase;
    border-bottom:1px solid #eee;
}

/* Grid de 5 colunas que NUNCA quebra:
   [BRASIL]  [input]  [X]  [input]  [ADVERSARIO]
   Usa fr para os nomes e px fixo para inputs/X */
.match-grid {
    display: grid;
    grid-template-columns: 1fr clamp(44px,13vw,64px) clamp(18px,5vw,28px) clamp(44px,13vw,64px) 1fr;
    align-items: center;
    gap: clamp(3px,1.5vw,10px);
    padding: clamp(8px,2.5vw,14px) clamp(8px,2.5vw,16px);
}
.mg-home { font-weight:900; font-size:clamp(0.75rem,3.2vw,1.05rem); color:#2a1b6b; text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.mg-away { font-weight:900; font-size:clamp(0.75rem,3.2vw,1.05rem); color:#2a1b6b; text-align:right; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.mg-x    { font-weight:900; font-size:clamp(0.9rem,3.5vw,1.2rem); color:#2a1b6b; text-align:center; }
.mg-score { background:#f0f0f0; border:2px solid #2a1b6b; border-radius:7px; font-weight:900; font-size:clamp(1rem,4.5vw,1.4rem); color:#2a1b6b; text-align:center; width:100%; aspect-ratio:1; display:flex; align-items:center; justify-content:center; }

.match-footer-txt { text-align:center; font-weight:700; font-size:clamp(0.68rem,2.5vw,0.82rem); padding:8px; border-top:1px solid #eee; color:#2a1b6b; }
.match-footer-txt .red { color:#e53935 !important; font-weight:900; }

/* ── Força os st.number_input a caberem no grid ──
   Streamlit envolve o input em vários divs — zeramos padding/margin
   em todos eles dentro da nossa coluna de input */
.match-input-col > div,
.match-input-col > div > div,
.match-input-col > div > div > div,
.match-input-col [data-testid="stNumberInput"],
.match-input-col [data-testid="stNumberInput"] > div {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}
.match-input-col [data-testid="stNumberInput"] input {
    background: #fff !important;
    border: 2px solid #2a1b6b !important;
    border-radius: 7px !important;
    color: #2a1b6b !important;
    font-weight: 900 !important;
    font-size: clamp(1rem,4.5vw,1.4rem) !important;
    text-align: center !important;
    padding: 0 !important;
    width: 100% !important;
    aspect-ratio: 1 !important;
    min-height: unset !important;
    height: clamp(44px,13vw,64px) !important;
    -moz-appearance: textfield !important;
}
.match-input-col [data-testid="stNumberInput"] input::-webkit-outer-spin-button,
.match-input-col [data-testid="stNumberInput"] input::-webkit-inner-spin-button { -webkit-appearance:none !important; }
/* Esconde botões +/- do number input */
.match-input-col [data-testid="stNumberInput"] button { display:none !important; }
/* Remove label e gap extras */
.match-input-col [data-testid="stNumberInput"] label { display:none !important; }
.match-input-col [data-testid="stNumberInput"] > div > div { gap:0 !important; }

/* ── Colunas Streamlit dentro do match card ──
   Zeramos o gap padrão e removemos padding das células */
.match-cols-wrapper [data-testid="column"] {
    padding: 0 !important;
    overflow: visible !important;
}
.match-cols-wrapper > div {
    gap: clamp(3px,1.5vw,10px) !important;
    align-items: center !important;
}

/* text / select */
.stTextInput input { background:#fff !important; color:#2a1b6b !important; border-radius:8px !important; }
.stSelectbox div[data-baseweb="select"] { background:#fff !important; color:#2a1b6b !important; }
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label { color:#fff !important; font-weight:700; }

/* desc + pts */
.desc-pts-row { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
.desc-pts-row .card { flex:1; min-width:min(100%,240px); }

/* footer */
.footer-banner { background:#fff; border-radius:14px; padding:clamp(10px,3vw,14px); display:flex; flex-wrap:wrap; gap:12px; align-items:center; }
.money-box { background:#009c3b; padding:clamp(8px,2vw,12px); border-radius:10px; text-align:center; min-width:clamp(100px,30vw,130px); flex-shrink:0; }
.money-box * { color:#fff !important; }
.money-val { font-size:clamp(1.2rem,5vw,1.6rem); font-weight:900; display:block; }
.footer-cta { flex:1; min-width:180px; }
.footer-cta p { text-align:center; color:#2a1b6b !important; font-weight:900; font-size:clamp(0.75rem,2.8vw,0.95rem); margin:0 0 8px 0; }
.prizes { display:flex; justify-content:space-around; flex-wrap:wrap; gap:6px; }
.prize .pts { color:#e53935 !important; font-weight:900; font-size:clamp(0.85rem,3vw,1.1rem); }
.prize .lbl { color:#2a1b6b !important; font-weight:700; font-size:clamp(0.6rem,2vw,0.75rem); }

.stButton>button { background:#ffdf00 !important; color:#2a1b6b !important; font-weight:900 !important; border:none !important; border-radius:10px !important; width:100% !important; font-size:clamp(0.95rem,3.5vw,1.1rem) !important; min-height:48px !important; touch-action:manipulation !important; }
.saved-badge { background:rgba(0,156,59,0.15); border:1px solid #009c3b; border-radius:10px; padding:12px 16px; margin-bottom:16px; }
.obs-text { font-size:clamp(0.68rem,2.2vw,0.75rem); color:rgba(255,255,255,0.6); margin-top:8px; line-height:1.5; }
#MainMenu,footer,header { visibility:hidden; }

@media (max-width:400px) {
    .block-container { padding-left:4px !important; padding-right:4px !important; }
    .footer-banner { flex-direction:column; }
    .money-box { width:100%; min-width:unset; }
}
</style>
"""

def _render_desc_pts():
    st.markdown("""
    <div class="desc-pts-row">
      <div class="card">
        <h4>DESCRIÇÃO:</h4>
        <p>Preencha os placares dos jogos da Seleção Brasileira na primeira fase
        da Copa do Mundo e, ao final, ordene os times do Grupo C da 1ª ao 4ª
        colocação. Ganha quem acertar os placares e a ordem final dos colocados!</p>
      </div>
      <div class="card">
        <h4>🏆 PONTUAÇÃO:</h4>
        <p>⭐ <b>CRAVAR O RESULTADO EXATO DE CADA JOGO:</b><br><span class="red">50 PONTOS</span></p>
        <p>⭐ <b>ACERTAR UM COLOCADO INDIVIDUALMENTE:</b><br><span class="red">30 PONTOS</span></p>
        <p>⭐ <b>ACERTAR A ORDEM EXATA DA CLASSIFICAÇÃO (GABARITANDO):</b><br><span class="red">100 PONTOS</span></p>
      </div>
    </div>
    """, unsafe_allow_html=True)

def _render_footer():
    st.markdown("""
    <div class="footer-banner">
      <div class="money-box">
        💵<br><b style="font-size:0.7rem;">VALOR PARA PARTICIPAR<br>DO BOLÃO:</b><br>
        <span class="money-val">R$ 20,00</span>
        <b style="font-size:0.7rem;">POR PARTICIPANTE</b>
      </div>
      <div class="footer-cta">
        <p>CRAVE OS PLACARES. ACERTE A ORDEM. SEJA O CAMPEÃO!</p>
        <div class="prizes">
          <div class="prize"><div class="pts">50 PTS</div><div class="lbl">PLACAR EXATO</div></div>
          <div class="prize"><div class="pts">30 PTS</div><div class="lbl">COLOCADO IND.</div></div>
          <div class="prize"><div class="pts">100 PTS</div><div class="lbl">GABARITANDO!</div></div>
        </div>
      </div>
    </div>
    <p class="obs-text">⭐ <b>OBS.:</b> Em caso de empate: 1º mais placares exatos, 2º mais acertos de ordem, 3º sorteio.</p>
    """, unsafe_allow_html=True)

def _jogo_readonly(idx, info, gb, ga):
    st.markdown(f"""
    <div class="match-card">
      <div class="match-header-txt">JOGO {idx+1} ({info['data']})</div>
      <div class="match-grid">
        <span class="mg-home">BRASIL</span>
        <span class="mg-score">{gb}</span>
        <span class="mg-x">X</span>
        <span class="mg-score">{ga}</span>
        <span class="mg-away">{info['nome']}</span>
      </div>
      <div class="match-footer-txt">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>
    """, unsafe_allow_html=True)

def _jogo_input(idx, jkey, info):
    """
    Usa st.columns com proporções que cabem em qualquer tela.
    O CSS .match-input-col remove todo padding/margin interno do Streamlit
    para que as células do grid HTML e as colunas Streamlit se alinhem.
    """
    # Cabeçalho do card
    st.markdown(f"""
    <div class="match-card">
      <div class="match-header-txt">JOGO {idx+1} ({info['data']})</div>
      <div class="match-cols-wrapper">
    """, unsafe_allow_html=True)

    # 5 colunas: nome_br | input_br | X | input_adv | nome_adv
    # Proporções pensadas para não quebrar nem em 320px
    c_br_nm, c_br_in, c_x, c_adv_in, c_adv_nm = st.columns([3, 2, 1, 2, 3])

    with c_br_nm:
        st.markdown("<div style='font-weight:900;font-size:clamp(0.75rem,3.2vw,1.05rem);color:#2a1b6b;padding-top:8px;'>BRASIL</div>", unsafe_allow_html=True)

    with c_br_in:
        st.markdown('<div class="match-input-col">', unsafe_allow_html=True)
        gb = st.number_input("gb", min_value=0, max_value=20, value=0,
                             key=f"h{idx}", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_x:
        st.markdown("<div style='font-weight:900;font-size:clamp(0.9rem,3.5vw,1.2rem);color:#2a1b6b;text-align:center;padding-top:8px;'>X</div>", unsafe_allow_html=True)

    with c_adv_in:
        st.markdown('<div class="match-input-col">', unsafe_allow_html=True)
        ga = st.number_input("ga", min_value=0, max_value=20, value=0,
                             key=f"a{idx}", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_adv_nm:
        st.markdown(f"<div style='font-weight:900;font-size:clamp(0.75rem,3.2vw,1.05rem);color:#2a1b6b;text-align:right;padding-top:8px;'>{info['nome']}</div>", unsafe_allow_html=True)

    st.markdown("""
      </div>
      <div class="match-footer-txt">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>
    """, unsafe_allow_html=True)

    return gb, ga

def _render_palpite_salvo(nome, dados):
    st.markdown(f"""
    <div class="saved-badge">
      <div style="color:#7fffb0;font-size:1rem;font-weight:700;">
        ✅ Palpite de <b>{nome}</b> registrado em {dados['enviado_em']}
      </div>
      <div style="color:rgba(255,255,255,0.55);font-size:0.8rem;margin-top:4px;">
        Os palpites são definitivos e não podem ser alterados após o envio.
      </div>
    </div>
    """, unsafe_allow_html=True)
    for i, (jkey, info) in enumerate(ADVERSARIOS.items()):
        p = dados['palpites'].get(jkey)
        gb, ga = p if p else (0, 0)
        _jogo_readonly(i, info, gb, ga)
    _render_desc_pts()
    _render_footer()

def render():
    st.markdown(MATCH_CSS, unsafe_allow_html=True)

    st.markdown('<div class="title-bar"><h1>Jogos do Brasil</h1><span class="grupo">GRUPO C</span></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="brasil-banner">
      <div class="brasil-flag">
        <div class="brasil-diamond"><div class="brasil-circle">ORDEM E<br>PROGRESSO</div></div>
      </div>
      <div class="brasil-name">BRASIL</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">IDENTIFICAÇÃO</div>', unsafe_allow_html=True)
    nome = st.text_input("Seu nome completo", placeholder="Digite seu nome aqui...", key="nome_input")

    if not nome.strip():
        st.markdown("<div style='text-align:center;padding:24px;color:rgba(255,255,255,0.3);font-size:1rem;'>DIGITE SEU NOME PARA CONTINUAR 👆</div>", unsafe_allow_html=True)
        _render_desc_pts()
        _render_footer()
        return

    nome = nome.strip()
    if palpite_enviado(nome):
        _render_palpite_salvo(nome, get_palpite_completo_por_nome(nome))
        return

    st.markdown("""
    <div style="background:rgba(255,215,0,0.07);border:1px solid rgba(255,215,0,0.25);border-radius:10px;padding:10px 14px;margin-bottom:4px;">
      <span style="color:rgba(255,255,255,0.65);font-size:0.82rem;">⚠️ <b>Atenção:</b> após confirmar, seu palpite <b>não poderá ser alterado</b>.</span>
    </div>
    """, unsafe_allow_html=True)

    placares = {}
    for i, (jkey, info) in enumerate(ADVERSARIOS.items()):
        gb, ga = _jogo_input(i, jkey, info)
        placares[jkey] = (gb, ga)

    _render_desc_pts()

    st.markdown('<div class="card"><h3 style="text-align:center;color:#2a1b6b !important;">🏆 CLASSIFICAÇÃO DO GRUPO C</h3>', unsafe_allow_html=True)
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

    hoje = date.today().strftime("%d/%m/%Y")
    st.markdown(f"""
    <div class="card">
      <div style="display:flex;gap:12px;flex-wrap:wrap;">
        <div style="flex:2;min-width:140px;"><div style="font-weight:700;font-size:0.8rem;margin-bottom:4px;">NOME</div><div style="font-weight:900;font-size:1rem;">{nome}</div></div>
        <div style="flex:1;min-width:100px;"><div style="font-weight:700;font-size:0.8rem;margin-bottom:4px;">DATA</div><div style="font-weight:900;font-size:1rem;">{hoje}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _render_footer()

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
        <div style="background:rgba(200,16,46,0.1);border:1px solid rgba(200,16,46,0.35);border-radius:10px;padding:12px 16px;margin-bottom:10px;">
          <b style="color:#ff6b6b;">⚠️ CONFIRME SEU PALPITE — esta ação é irreversível!</b>
        </div>
        """, unsafe_allow_html=True)
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("✅ SIM, ENVIAR DEFINITIVAMENTE"):
                classif_final = [s for s in selecionados if s]
                ok = save_palpite(nome, placares, tuple(classif_final))
                st.session_state.confirmar_palpite = False
                if ok:
                    st.success(f"🎉 Palpite de **{nome}** registrado! Boa sorte")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Palpite já registrado e não pode ser alterado.")
        with col_cancel:
            if st.button("✏️ VOLTAR E EDITAR"):
                st.session_state.confirmar_palpite = False
                st.rerun()
