import streamlit as st
import json
from utils.database import (
    init_db, save_palpite, palpite_enviado,
    save_placar_real, save_classificacao_real,
    get_placares_reais, get_classificacao_real,
    get_palpite_completo_por_nome,
)
from utils.scoring import calculate_scores

st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="🇧🇷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  #MainMenu, footer, header, .stDeployButton { visibility: hidden !important; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #1a1464; }
</style>
""", unsafe_allow_html=True)

init_db()

# ── session state ─────────────────────────────────────────
for k, v in [("msg",""),("msg_ok",True),("tab","form"),("confirmed",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Processa form submissions ─────────────────────────────
def handle_forms():
    # --- enviar palpite ---
    if st.session_state.get("_submit_palpite"):
        nome = st.session_state.get("f_nome","").strip()
        j1b  = int(st.session_state.get("f_j1b") or 0)
        j1a  = int(st.session_state.get("f_j1a") or 0)
        j2b  = int(st.session_state.get("f_j2b") or 0)
        j2a  = int(st.session_state.get("f_j2a") or 0)
        j3b  = int(st.session_state.get("f_j3b") or 0)
        j3a  = int(st.session_state.get("f_j3a") or 0)
        c1   = st.session_state.get("f_c1","")
        c2   = st.session_state.get("f_c2","")
        c3   = st.session_state.get("f_c3","")
        c4   = st.session_state.get("f_c4","")
        st.session_state["_submit_palpite"] = False

        if not nome:
            st.session_state.msg    = "❌ Informe seu nome!"
            st.session_state.msg_ok = False
        elif palpite_enviado(nome):
            st.session_state.msg    = f"❌ Palpite de {nome} já registrado!"
            st.session_state.msg_ok = False
        elif not all([c1,c2,c3,c4]) or len({c1,c2,c3,c4}) != 4:
            st.session_state.msg    = "❌ Selecione os 4 colocados sem repetir!"
            st.session_state.msg_ok = False
        else:
            ok = save_palpite(nome,
                {"jogo1":(j1b,j1a),"jogo2":(j2b,j2a),"jogo3":(j3b,j3a)},
                (c1,c2,c3,c4))
            if ok:
                st.session_state.msg      = f"🎉 Palpite de {nome} registrado! Boa sorte 🇧🇷"
                st.session_state.msg_ok   = True
                st.session_state.confirmed = False
            else:
                st.session_state.msg    = "❌ Palpite já registrado e não pode ser alterado."
                st.session_state.msg_ok = False
        st.rerun()

    # --- admin salvar placares ---
    if st.session_state.get("_admin_save_placar"):
        st.session_state["_admin_save_placar"] = False
        pwd = st.session_state.get("admin_pwd","")
        if pwd == "brasil2026":
            for jkey, kb, ka in [("jogo1","ar1b","ar1a"),("jogo2","ar2b","ar2a"),("jogo3","ar3b","ar3a")]:
                if st.session_state.get(f"enc_{jkey}"):
                    jb = int(st.session_state.get(kb) or 0)
                    ja = int(st.session_state.get(ka) or 0)
                    save_placar_real(jkey, jb, ja)
            st.session_state.msg    = "✅ Placares salvos!"
            st.session_state.msg_ok = True
        else:
            st.session_state.msg    = "❌ Senha incorreta!"
            st.session_state.msg_ok = False
        st.rerun()

    # --- admin salvar classificação ---
    if st.session_state.get("_admin_save_classif"):
        st.session_state["_admin_save_classif"] = False
        pwd = st.session_state.get("admin_pwd","")
        if pwd == "brasil2026":
            ordem = [st.session_state.get(f"arc{i}","") for i in range(1,5)]
            if len(set(ordem)) == 4 and all(ordem):
                save_classificacao_real([t.upper() for t in ordem])
                st.session_state.msg    = "✅ Classificação salva!"
                st.session_state.msg_ok = True
            else:
                st.session_state.msg    = "❌ Selecione 4 times diferentes!"
                st.session_state.msg_ok = False
        else:
            st.session_state.msg    = "❌ Senha incorreta!"
            st.session_state.msg_ok = False
        st.rerun()

handle_forms()

# ── Dados ────────────────────────────────────────────────
placares_reais     = get_placares_reais()
classificacao_real = get_classificacao_real()
scores             = calculate_scores()

JOGOS = [
    ("jogo1","MARROCOS","13/06"),
    ("jogo2","HAITI","19/06"),
    ("jogo3","ESCÓCIA","24/06"),
]
TIMES = ["BRASIL","MARROCOS","HAITI","ESCÓCIA"]

# ── CSS global ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Barlow:wght@400;600&display=swap');
html,body,.stApp { background:#1a1464 !important; font-family:'Barlow',sans-serif; }
.block-container { padding:0 !important; max-width:100% !important; }

/* wrapper geral */
.bolao-wrap { max-width:680px; margin:0 auto; padding:clamp(8px,3vw,20px); }

/* tabs */
.bolao-tabs { display:flex; background:#0d0a38; border-bottom:3px solid #ffdf00; margin-bottom:0; }
.bolao-tab  { flex:1; padding:14px 6px; text-align:center; font-family:'Barlow Condensed',sans-serif;
              font-weight:900; font-size:clamp(0.75rem,3.5vw,1rem); letter-spacing:.5px;
              color:rgba(255,255,255,.5); cursor:pointer; border:none; background:none; }
.bolao-tab.active { color:#1a1464; background:#ffdf00; }

/* header */
.b-titulo { display:flex; justify-content:space-between; align-items:center;
            margin-bottom:12px; flex-wrap:wrap; gap:6px; }
.b-titulo h1 { font-family:'Barlow Condensed',sans-serif; font-size:clamp(1.3rem,6vw,2rem);
               font-weight:900; text-transform:uppercase; color:#fff; margin:0; }
.b-grupo { background:#009c3b; color:#fff; font-weight:900; font-size:clamp(.8rem,3vw,1rem);
           padding:4px 12px; border-radius:20px; }

/* brasil banner */
.b-banner { display:flex; align-items:stretch; background:#fff; border-radius:14px;
            overflow:hidden; margin-bottom:16px; min-height:clamp(64px,18vw,96px); }
.b-flag   { background:#009c3b; width:42%; display:flex; align-items:center;
            justify-content:center; padding:clamp(8px,2.5vw,18px); }
.b-diamond{ background:#ffdf00; width:clamp(60px,16vw,100px); height:clamp(34px,9vw,56px);
            clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);
            display:flex; align-items:center; justify-content:center; }
.b-circle { background:#1a1464; width:clamp(18px,4.5vw,28px); height:clamp(18px,4.5vw,28px);
            border-radius:50%; display:flex; align-items:center; justify-content:center;
            font-size:clamp(4px,1vw,6px); color:#fff; font-weight:900;
            text-align:center; line-height:1.1; }
.b-nome   { flex:1; display:flex; align-items:center; justify-content:center;
            font-family:'Barlow Condensed',sans-serif;
            font-size:clamp(1.6rem,7.5vw,2.8rem); font-weight:900;
            color:#1a1464; letter-spacing:clamp(2px,1.5vw,6px); }

/* jogo card */
.jogo-card  { background:#fff; border-radius:14px; margin-bottom:14px; overflow:hidden; }
.jogo-titulo{ background:#e8e8f0; text-align:center; font-family:'Barlow Condensed',sans-serif;
              font-weight:900; font-size:clamp(.8rem,3.5vw,1rem); padding:10px;
              color:#2a1b6b; text-transform:uppercase; letter-spacing:1px; }
.jogo-body  { display:grid;
              grid-template-columns:1fr clamp(42px,12vw,60px) clamp(20px,5vw,28px) clamp(42px,12vw,60px) 1fr;
              align-items:center; gap:clamp(4px,2vw,10px);
              padding:clamp(10px,3vw,14px); }
.jogo-time  { font-family:'Barlow Condensed',sans-serif; font-weight:900;
              font-size:clamp(.78rem,3.5vw,1.05rem); color:#2a1b6b;
              overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jogo-time.home { text-align:left; }
.jogo-time.away { text-align:right; }
.jogo-x     { font-family:'Barlow Condensed',sans-serif; font-weight:900;
              font-size:clamp(.9rem,4vw,1.2rem); color:#2a1b6b; text-align:center; }
.jogo-score { border:2.5px solid #1a1464; border-radius:8px; background:#f0f0f0;
              color:#1a1464; font-family:'Barlow Condensed',sans-serif;
              font-size:clamp(1rem,5vw,1.5rem); font-weight:900;
              text-align:center; display:flex; align-items:center; justify-content:center;
              width:100%; aspect-ratio:1; }
.jogo-rodape{ background:#fff; text-align:center;
              font-size:clamp(.68rem,2.8vw,.82rem); font-weight:700;
              color:#2a1b6b; padding:8px; border-top:1px solid #eee; }
.jogo-rodape .red { color:#e53935; font-weight:900; }

/* card branco genérico */
.b-card { background:#fff; border-radius:14px; padding:clamp(10px,3vw,16px); margin-bottom:14px; }
.b-card, .b-card * { color:#2a1b6b; }
.b-card h3,.b-card h4 { font-family:'Barlow Condensed',sans-serif; font-weight:900;
                         font-size:clamp(.9rem,4vw,1.1rem); margin:0 0 10px 0; }

/* section title */
.sec-title { font-family:'Barlow Condensed',sans-serif; font-weight:900;
             font-size:clamp(.88rem,3.5vw,1.1rem); color:#fff; letter-spacing:2px;
             border-left:4px solid #ffdf00; padding-left:10px;
             margin:16px 0 10px; text-transform:uppercase; }

/* desc + pts */
.desc-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }
@media(max-width:480px){ .desc-row { grid-template-columns:1fr; } }
.pts-item { display:flex; align-items:flex-start; gap:8px; padding:5px 0;
            border-bottom:1px solid rgba(42,27,107,.1); }
.pts-item:last-child { border-bottom:none; }
.pts-num  { font-family:'Barlow Condensed',sans-serif; font-weight:900;
            font-size:clamp(1rem,4vw,1.3rem); color:#e53935; min-width:42px; line-height:1.1; }
.pts-txt  { font-size:clamp(.75rem,2.8vw,.85rem); }

/* footer banner */
.footer-banner { background:#fff; border-radius:14px; padding:clamp(10px,3vw,14px);
                 display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:14px; }
.money-box  { background:#009c3b; padding:clamp(8px,2.5vw,12px); border-radius:10px;
              text-align:center; min-width:clamp(100px,28vw,130px); flex-shrink:0; }
.money-box,.money-box * { color:#fff !important; }
.money-val  { font-family:'Barlow Condensed',sans-serif; font-size:clamp(1.2rem,5.5vw,1.6rem);
              font-weight:900; display:block; }
.footer-right { flex:1; min-width:160px; }
.footer-right p { text-align:center; color:#2a1b6b; font-weight:900;
                   font-size:clamp(.72rem,3vw,.9rem); margin:0 0 8px 0; }
.prizes { display:flex; justify-content:space-around; flex-wrap:wrap; gap:4px; }
.prize .pts { color:#e53935; font-weight:900; font-size:clamp(.8rem,3.5vw,1rem); }
.prize .lbl { color:#2a1b6b; font-weight:700; font-size:clamp(.58rem,2vw,.72rem); }
.obs { font-size:clamp(.65rem,2.5vw,.75rem); color:rgba(255,255,255,.5);
       line-height:1.5; margin-bottom:14px; }

/* classificacao card (fundo escuro p/ selects ficarem visíveis) */
.classif-card { background:#1e1560; border:1px solid rgba(255,255,255,.15);
                border-radius:14px; padding:clamp(10px,3vw,16px); margin-bottom:14px; }
.classif-card h3 { font-family:'Barlow Condensed',sans-serif; font-weight:900;
                   font-size:clamp(.9rem,4vw,1.1rem); color:#fff; text-align:center;
                   margin:0 0 14px 0; }

/* inputs Streamlit — overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background:#fff !important; color:#2a1b6b !important;
    border:2px solid #2a1b6b !important; border-radius:8px !important;
    font-family:'Barlow Condensed',sans-serif !important;
    font-weight:900 !important; font-size:clamp(1rem,5vw,1.4rem) !important;
    text-align:center !important;
}
div[data-testid="stNumberInput"] button { display:none !important; }
div[data-testid="stSelectbox"] > div > div {
    background:rgba(255,255,255,.1) !important; color:#fff !important;
    border:1.5px solid rgba(255,255,255,.25) !important; border-radius:10px !important;
}
div[data-testid="stSelectbox"] svg { fill:#fff !important; }
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label {
    color:rgba(255,255,255,.8) !important; font-weight:700 !important;
    font-family:'Barlow Condensed',sans-serif !important; letter-spacing:.5px !important;
}

/* botões Streamlit */
.stButton > button {
    background:#ffdf00 !important; color:#1a1464 !important;
    font-family:'Barlow Condensed',sans-serif !important;
    font-weight:900 !important; font-size:clamp(.95rem,4vw,1.1rem) !important;
    letter-spacing:1px !important; border:none !important;
    border-radius:12px !important; width:100% !important;
    min-height:48px !important; touch-action:manipulation !important;
}
.stButton > button:hover { background:#ffe833 !important; }

/* botão verde */
.btn-green > button {
    background:#009c3b !important; color:#fff !important;
}
/* botão cinza */
.btn-gray > button {
    background:rgba(255,255,255,.15) !important; color:#fff !important;
}

/* mensagem */
.msg-ok  { background:rgba(0,156,59,.2); border:1px solid #009c3b;
           border-radius:10px; padding:12px 16px; margin-bottom:14px;
           color:#7fffb0; font-weight:700; font-size:clamp(.85rem,3vw,.95rem); }
.msg-err { background:rgba(200,16,46,.2); border:1px solid #c8102e;
           border-radius:10px; padding:12px 16px; margin-bottom:14px;
           color:#ffaaaa; font-weight:700; font-size:clamp(.85rem,3vw,.95rem); }

/* saved badge */
.saved-badge { background:rgba(0,156,59,.15); border:1px solid #009c3b;
               border-radius:10px; padding:12px 16px; margin-bottom:16px; }

/* ranking */
.rank-status-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:16px; }
.status-card { border-radius:10px; padding:clamp(8px,2.5vw,12px); text-align:center;
               border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.05); }
.status-card.enc { border-color:rgba(0,156,59,.5); background:rgba(0,156,59,.12); }
.status-jogo   { font-size:clamp(.65rem,2.5vw,.75rem); color:rgba(255,255,255,.5);
                 font-weight:700; letter-spacing:1px; text-transform:uppercase; }
.status-placar { font-family:'Barlow Condensed',sans-serif; font-size:clamp(1rem,4vw,1.3rem);
                 font-weight:900; color:#ffdf00; line-height:1.2; }
.status-tag    { font-size:clamp(.62rem,2.2vw,.72rem); font-weight:700; }
.rank-card { display:flex; align-items:center; gap:12px;
             background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
             border-radius:12px; padding:clamp(10px,3vw,14px) clamp(12px,3.5vw,18px);
             margin-bottom:8px; }
.rank-card.r1 { border-color:#ffd700; background:rgba(255,215,0,.08); }
.rank-card.r2 { border-color:#c0c0c0; background:rgba(192,192,192,.06); }
.rank-card.r3 { border-color:#cd7f32; background:rgba(205,127,50,.06); }
.rank-pos  { font-family:'Barlow Condensed',sans-serif; font-weight:900;
             font-size:clamp(1.2rem,5vw,1.5rem); min-width:32px; text-align:center;
             color:rgba(255,255,255,.3); }
.r1 .rank-pos { color:#ffd700; } .r2 .rank-pos { color:#c0c0c0; } .r3 .rank-pos { color:#cd7f32; }
.rank-nome { flex:1; font-family:'Barlow Condensed',sans-serif; font-weight:900;
             font-size:clamp(.88rem,3.5vw,1.05rem); color:#fff;
             white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.rank-pts-val { font-family:'Barlow Condensed',sans-serif; font-weight:900;
                font-size:clamp(1.2rem,5vw,1.5rem); color:#ffdf00; text-align:right; }
.rank-pts-lbl { font-size:clamp(.6rem,2.2vw,.7rem); color:rgba(255,255,255,.4); text-align:right; }
.detail-box { background:rgba(255,255,255,.04); border-radius:10px; padding:12px;
              margin-bottom:8px; font-size:clamp(.78rem,3vw,.88rem); color:rgba(255,255,255,.85); }
.dl { padding:4px 0; border-bottom:1px solid rgba(255,255,255,.06); }
.dl:last-child { border-bottom:none; }
.ok-t  { color:#7fffb0; font-weight:700; }
.err-t { color:#ffaaaa; }
.pend-t{ color:rgba(255,255,255,.4); }
.cf-row { display:flex; align-items:center; gap:10px;
          background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
          border-radius:10px; padding:10px 14px; margin-bottom:6px; color:#fff; }

/* admin */
.admin-warn { background:rgba(200,16,46,.08); border:1px solid rgba(200,16,46,.25);
              border-radius:12px; padding:12px 16px; margin-bottom:16px;
              font-size:.88rem; color:rgba(255,255,255,.7); }
.admin-section { background:rgba(200,16,46,.07); border:1px solid rgba(200,16,46,.25);
                 border-radius:12px; padding:14px; margin-bottom:14px; }
.admin-section b { color:#fff; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Helpers de layout ─────────────────────────────────────
def banner():
    st.markdown("""
    <div class="b-titulo">
      <h1>Jogos do Brasil</h1><span class="b-grupo">GRUPO C</span>
    </div>
    <div class="b-banner">
      <div class="b-flag">
        <div class="b-diamond"><div class="b-circle">ORDEM E<br>PROGRESSO</div></div>
      </div>
      <div class="b-nome">BRASIL</div>
    </div>""", unsafe_allow_html=True)

def jogo_card_static(idx, jkey, adv, data, gb, ga):
    st.markdown(f"""
    <div class="jogo-card">
      <div class="jogo-titulo">JOGO {idx} ({data})</div>
      <div class="jogo-body">
        <span class="jogo-time home">BRASIL</span>
        <span class="jogo-score">{gb}</span>
        <span class="jogo-x">X</span>
        <span class="jogo-score">{ga}</span>
        <span class="jogo-time away">{adv}</span>
      </div>
      <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>""", unsafe_allow_html=True)

def desc_pts():
    st.markdown("""
    <div class="desc-row">
      <div class="b-card">
        <h4>DESCRIÇÃO:</h4>
        <p style="font-size:clamp(.78rem,3vw,.88rem);line-height:1.5;">
        Preencha os placares e ordene os times do Grupo C da 1ª à 4ª colocação.
        Ganha quem acertar os placares e a ordem final!</p>
      </div>
      <div class="b-card">
        <h4>🏆 PONTUAÇÃO:</h4>
        <div class="pts-item"><span class="pts-num">50</span><span class="pts-txt"><b>Placar exato</b> de cada jogo</span></div>
        <div class="pts-item"><span class="pts-num">30</span><span class="pts-txt"><b>Colocado individual</b> correto</span></div>
        <div class="pts-item"><span class="pts-num">100</span><span class="pts-txt"><b>Gabaritar</b> a classificação</span></div>
      </div>
    </div>""", unsafe_allow_html=True)

def footer_banner():
    st.markdown("""
    <div class="footer-banner">
      <div class="money-box">
        💵<br><b style="font-size:.7rem;">VALOR PARA PARTICIPAR<br>DO BOLÃO:</b><br>
        <span class="money-val">R$ 20,00</span>
        <b style="font-size:.7rem;">POR PARTICIPANTE</b>
      </div>
      <div class="footer-right">
        <p>CRAVE OS PLACARES. ACERTE A ORDEM. SEJA O CAMPEÃO!</p>
        <div class="prizes">
          <div class="prize"><div class="pts">50 PTS</div><div class="lbl">PLACAR EXATO</div></div>
          <div class="prize"><div class="pts">30 PTS</div><div class="lbl">COLOCADO IND.</div></div>
          <div class="prize"><div class="pts">100 PTS</div><div class="lbl">GABARITANDO!</div></div>
        </div>
      </div>
    </div>
    <p class="obs">⭐ <b>OBS.:</b> Em caso de empate: 1º mais placares exatos, 2º mais acertos de ordem, 3º sorteio.</p>
    """, unsafe_allow_html=True)

def show_msg():
    if st.session_state.msg:
        cls = "msg-ok" if st.session_state.msg_ok else "msg-err"
        st.markdown(f'<div class="{cls}">{st.session_state.msg}</div>', unsafe_allow_html=True)
        st.session_state.msg = ""

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 PARTICIPAR", "🏆 RANKING", "⚙️ ADMIN"])

# ════════════════════════════════════════════════════════
# ABA 1 — PARTICIPAR
# ════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="bolao-wrap">', unsafe_allow_html=True)
    banner()
    show_msg()

    nome = st.text_input("Seu nome completo", placeholder="Digite seu nome aqui...",
                         key="f_nome")

    if not nome.strip():
        st.markdown('<div style="text-align:center;padding:20px;color:rgba(255,255,255,.3);font-weight:700;">DIGITE SEU NOME PARA CONTINUAR 👆</div>', unsafe_allow_html=True)
        desc_pts()
        footer_banner()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    nome = nome.strip()

    # Palpite já enviado → somente leitura
    if palpite_enviado(nome):
        dados = get_palpite_completo_por_nome(nome)
        st.markdown(f"""
        <div class="saved-badge">
          <div style="color:#7fffb0;font-weight:700;font-size:1rem;">
            ✅ Palpite de <b>{nome}</b> registrado em {dados['enviado_em']}
          </div>
          <div style="color:rgba(255,255,255,.5);font-size:.8rem;margin-top:4px;">
            Os palpites são definitivos e não podem ser alterados.
          </div>
        </div>""", unsafe_allow_html=True)
        for i,(jkey,adv,data) in enumerate(JOGOS,1):
            p = dados["palpites"].get(jkey)
            gb,ga = p if p else (0,0)
            jogo_card_static(i, jkey, adv, data, gb, ga)
        desc_pts()
        footer_banner()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # Aviso
    st.markdown("""
    <div style="background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.25);
    border-radius:10px;padding:10px 14px;margin-bottom:4px;font-size:.82rem;color:rgba(255,255,255,.7);">
    ⚠️ <b>Atenção:</b> após confirmar, seu palpite <b>não poderá ser alterado</b>.
    </div>""", unsafe_allow_html=True)

    # ── Jogos ─────────────────────────────────────────────
    for i,(jkey,adv,data) in enumerate(JOGOS,1):
        kb = f"f_j{i}b"; ka = f"f_j{i}a"
        st.markdown(f"""
        <div class="jogo-card">
          <div class="jogo-titulo">JOGO {i} ({data})</div>
        """, unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns([3,2,1,2,3])
        with c1:
            st.markdown(f"<div style='font-family:Barlow Condensed,sans-serif;font-weight:900;font-size:clamp(.78rem,3.5vw,1.05rem);color:#2a1b6b;padding-top:6px;'>BRASIL</div>", unsafe_allow_html=True)
        with c2:
            st.number_input("gols_br", min_value=0, max_value=20, value=0,
                            key=kb, label_visibility="collapsed")
        with c3:
            st.markdown("<div style='text-align:center;font-weight:900;font-size:1.2rem;color:#2a1b6b;padding-top:6px;'>X</div>", unsafe_allow_html=True)
        with c4:
            st.number_input("gols_adv", min_value=0, max_value=20, value=0,
                            key=ka, label_visibility="collapsed")
        with c5:
            st.markdown(f"<div style='font-family:Barlow Condensed,sans-serif;font-weight:900;font-size:clamp(.78rem,3.5vw,1.05rem);color:#2a1b6b;text-align:right;padding-top:6px;'>{adv}</div>", unsafe_allow_html=True)
        st.markdown("""
          <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
        </div>""", unsafe_allow_html=True)

    desc_pts()

    # ── Classificação ─────────────────────────────────────
    st.markdown('<div class="classif-card"><h3>🏆 CLASSIFICAÇÃO DO GRUPO C</h3>', unsafe_allow_html=True)
    opcoes = [""]+TIMES
    c1v = st.selectbox("1º Colocado", opcoes, key="f_c1")
    c2v = st.selectbox("2º Colocado", opcoes, key="f_c2")
    c3v = st.selectbox("3º Colocado", opcoes, key="f_c3")
    c4v = st.selectbox("4º Colocado", opcoes, key="f_c4")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Nome + Data ───────────────────────────────────────
    from datetime import date as dt
    st.markdown(f"""
    <div class="b-card">
      <div style="display:grid;grid-template-columns:2fr 1fr;gap:12px;">
        <div><div style="font-weight:700;font-size:.75rem;margin-bottom:3px;opacity:.6;">NOME</div>
             <div style="font-weight:900;font-size:1rem;">{nome}</div></div>
        <div><div style="font-weight:700;font-size:.75rem;margin-bottom:3px;opacity:.6;">DATA</div>
             <div style="font-weight:900;font-size:1rem;">{dt.today().strftime('%d/%m/%Y')}</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    footer_banner()

    # ── Botão envio ───────────────────────────────────────
    if not st.session_state.confirmed:
        if st.button("ENVIAR PALPITE 🇧🇷", key="btn_enviar"):
            erros = []
            if not all([c1v,c2v,c3v,c4v]):
                erros.append("Selecione os 4 colocados!")
            elif len({c1v,c2v,c3v,c4v}) != 4:
                erros.append("Selecione times diferentes na classificação!")
            if erros:
                st.error(" | ".join(erros))
            else:
                st.session_state.confirmed = True
                st.rerun()
    else:
        st.markdown("""
        <div style="background:rgba(200,16,46,.12);border:1px solid rgba(200,16,46,.4);
        border-radius:10px;padding:12px;margin-bottom:10px;font-weight:700;color:#ffaaaa;">
        ⚠️ CONFIRME SEU PALPITE — esta ação é irreversível!
        </div>""", unsafe_allow_html=True)
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            st.markdown('<div class="btn-green">', unsafe_allow_html=True)
            if st.button("✅ SIM, ENVIAR", key="btn_confirmar"):
                st.session_state["_submit_palpite"] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_cancel:
            st.markdown('<div class="btn-gray">', unsafe_allow_html=True)
            if st.button("✏️ EDITAR", key="btn_cancelar"):
                st.session_state.confirmed = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# ABA 2 — RANKING
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="bolao-wrap">', unsafe_allow_html=True)

    # Status jogos
    st.markdown('<div class="sec-title" style="margin-top:4px">PLACARES</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for col,(jkey,adv,data) in zip(cols,JOGOS):
        r = placares_reais.get(jkey,{})
        enc = r.get("encerrado")
        with col:
            if enc:
                st.markdown(f"""
                <div class="status-card enc">
                  <div class="status-jogo">Jogo {jkey[-1]} · {data}</div>
                  <div class="status-placar">Brasil {r['brasil']} × {r['adversario']}</div>
                  <div class="status-tag" style="color:#7fffb0">✅ Encerrado</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card">
                  <div class="status-jogo">Jogo {jkey[-1]} · {data}</div>
                  <div class="status-placar" style="color:rgba(255,255,255,.3)">—</div>
                  <div class="status-tag" style="color:rgba(255,255,255,.3)">⏳ Pendente</div>
                </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-title">CLASSIFICAÇÃO GERAL</div>', unsafe_allow_html=True)

    if not scores:
        st.markdown('<div style="text-align:center;padding:40px;color:rgba(255,255,255,.3);font-weight:700;">NENHUM PALPITE AINDA 🎯</div>', unsafe_allow_html=True)
    else:
        medals = ["🥇","🥈","🥉"]
        rcs    = ["r1","r2","r3"]
        adv_nomes = ["Marrocos","Haiti","Escócia"]
        pos_icons = ["🥇","🥈","🥉","4°"]

        st.markdown(f'<div style="text-align:right;color:rgba(255,255,255,.35);font-size:.78rem;margin-bottom:8px;">{len(scores)} participante(s)</div>', unsafe_allow_html=True)

        for idx, e in enumerate(scores):
            pos = idx+1
            med = medals[idx] if idx < 3 else f"{pos}°"
            cls = rcs[idx]    if idx < 3 else ""
            det = e["detail"]

            st.markdown(f"""
            <div class="rank-card {cls}">
              <div class="rank-pos">{med}</div>
              <div class="rank-nome">{e['nome'].upper()}</div>
              <div>
                <div class="rank-pts-val">{e['total']}</div>
                <div class="rank-pts-lbl">PONTOS</div>
              </div>
            </div>""", unsafe_allow_html=True)

            with st.expander(f"Detalhes — {e['nome']}"):
                for ji,(jkey,adv,data) in enumerate(JOGOS):
                    d = det.get(jkey,{})
                    s = d.get("status","pendente")
                    if s == "exato":
                        p = d["palpite"]
                        st.markdown(f'<div class="dl">Brasil {p[0]}×{p[1]} {adv_nomes[ji]} <span class="ok-t">✅ +50pts</span></div>', unsafe_allow_html=True)
                    elif s == "errado":
                        p,r2 = d["palpite"],d["real"]
                        st.markdown(f'<div class="dl">Brasil {p[0]}×{p[1]} {adv_nomes[ji]} <span class="err-t">❌ (real: {r2[0]}×{r2[1]})</span></div>', unsafe_allow_html=True)
                    else:
                        pal = d.get("palpite")
                        txt = f"{pal[0]}×{pal[1]}" if pal else "—"
                        st.markdown(f'<div class="dl">Brasil {txt} {adv_nomes[ji]} <span class="pend-t">⏳</span></div>', unsafe_allow_html=True)

                cl = det.get("classificacao",{})
                cp = cl.get("palpite",[])
                if cp:
                    st.markdown('<div class="dl" style="margin-top:6px;font-weight:700;border-bottom:none;">Classificação palpitada:</div>', unsafe_allow_html=True)
                    cs = cl.get("status",{})
                    cr2 = cl.get("real",[])
                    for ci,t in enumerate(cp):
                        acerto = cs.get(ci+1)
                        if acerto == "acerto":
                            tag = '<span class="ok-t">✅ +30pts</span>'
                        elif acerto == "errado":
                            era = cr2[ci] if ci < len(cr2) else "?"
                            tag = f'<span class="err-t">❌ (era {era})</span>'
                        else:
                            tag = '<span class="pend-t">⏳</span>'
                        st.markdown(f'<div class="dl">{pos_icons[ci]} {t} {tag}</div>', unsafe_allow_html=True)
                    if cs.get("gabarito") is True:
                        st.markdown('<div class="dl"><span class="ok-t">🏆 GABARITO! +100pts bônus</span></div>', unsafe_allow_html=True)

        # Classificação final publicada
        if any(classificacao_real.values()):
            st.markdown('<div class="sec-title">CLASSIFICAÇÃO FINAL · GRUPO C</div>', unsafe_allow_html=True)
            for p in range(1,5):
                t = classificacao_real.get(p,"—")
                st.markdown(f'<div class="cf-row"><span style="font-size:1.1rem;">{pos_icons[p-1]}</span><span style="font-family:Barlow Condensed,sans-serif;font-weight:900;font-size:1rem;">{t}</span></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# ABA 3 — ADMIN
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="bolao-wrap">', unsafe_allow_html=True)
    show_msg()
    st.markdown('<div class="admin-warn">⚙️ Área exclusiva do organizador</div>', unsafe_allow_html=True)

    pwd_input = st.text_input("Senha do administrador", type="password", key="admin_pwd")

    if pwd_input != "brasil2026":
        if pwd_input:
            st.error("❌ Senha incorreta!")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    st.success("✅ Acesso liberado!")

    # Placares reais
    st.markdown('<div class="sec-title">PLACARES REAIS</div>', unsafe_allow_html=True)
    for i,(jkey,adv,data) in enumerate(JOGOS,1):
        r = placares_reais.get(jkey,{})
        enc = bool(r.get("encerrado"))
        st.markdown(f'<div class="admin-section"><b>Jogo {i} ({data}) — Brasil × {adv}</b>', unsafe_allow_html=True)
        if enc:
            st.markdown(f'<div style="color:#7fffb0;font-size:.82rem;margin:6px 0;">✅ Salvo: Brasil {r["brasil"]} × {r["adversario"]}</div>', unsafe_allow_html=True)
        ca,cb,cc,cd = st.columns([3,2,1,2])
        with ca: st.markdown("<div style='color:#fff;font-weight:700;padding-top:8px;font-size:.88rem;'>Brasil</div>", unsafe_allow_html=True)
        with cb: st.number_input("gols_br", min_value=0, max_value=20,
                                  value=int(r.get("brasil") or 0),
                                  key=f"ar{i}b", label_visibility="collapsed")
        with cc: st.markdown("<div style='text-align:center;color:#fff;font-weight:900;padding-top:8px;'>×</div>", unsafe_allow_html=True)
        with cd: st.number_input("gols_adv", min_value=0, max_value=20,
                                   value=int(r.get("adversario") or 0),
                                   key=f"ar{i}a", label_visibility="collapsed")
        st.checkbox("Marcar como encerrado", value=enc, key=f"enc_{jkey}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btn-green">', unsafe_allow_html=True)
    if st.button("💾 SALVAR PLACARES", key="btn_admin_placar"):
        st.session_state["_admin_save_placar"] = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Classificação final
    st.markdown('<div class="sec-title" style="margin-top:20px">CLASSIFICAÇÃO FINAL DO GRUPO C</div>', unsafe_allow_html=True)
    opcoes_admin = [""]+TIMES
    for i in range(1,5):
        cur = (classificacao_real.get(i,"")).upper()
        idx_cur = opcoes_admin.index(cur) if cur in opcoes_admin else 0
        st.selectbox(f"{i}º Colocado", opcoes_admin, index=idx_cur, key=f"arc{i}")

    st.markdown('<div class="btn-green">', unsafe_allow_html=True)
    if st.button("💾 SALVAR CLASSIFICAÇÃO", key="btn_admin_classif"):
        st.session_state["_admin_save_classif"] = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
