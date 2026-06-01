import streamlit as st
import json
from utils.database import (
    init_db, save_palpite, palpite_enviado,
    get_palpite_completo_por_nome, save_placar_real,
    save_classificacao_real, get_placares_reais,
    get_classificacao_real,
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
  .block-container { padding: 0 !important; max-width: 680px !important; }
  .stApp { background: #1a1464; }
</style>
""", unsafe_allow_html=True)

init_db()

# ── session state ─────────────────────────────────────────
for k,v in [("msg",""),("msg_ok",True),("confirmed",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Processa query params vindos do HTML (parent window) ──
qp = st.query_params

def handle_action():
    action = qp.get("action","")
    if not action:
        return

    if action == "submit":
        nome = qp.get("nome","").strip()
        j1b  = int(qp.get("j1b","0") or 0)
        j1a  = int(qp.get("j1a","0") or 0)
        j2b  = int(qp.get("j2b","0") or 0)
        j2a  = int(qp.get("j2a","0") or 0)
        j3b  = int(qp.get("j3b","0") or 0)
        j3a  = int(qp.get("j3a","0") or 0)
        c1   = qp.get("c1","")
        c2   = qp.get("c2","")
        c3   = qp.get("c3","")
        c4   = qp.get("c4","")

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
            st.session_state.msg    = (f"🎉 Palpite de {nome} registrado! Boa sorte 🇧🇷"
                                        if ok else "❌ Palpite já registrado.")
            st.session_state.msg_ok = ok
        st.query_params.clear()
        st.rerun()

    elif action == "admin_placar":
        if qp.get("pwd","") == "brasil2026":
            for jkey,jb_k,ja_k in [("jogo1","r1b","r1a"),("jogo2","r2b","r2a"),("jogo3","r3b","r3a")]:
                if qp.get(f"enc_{jkey}"):
                    save_placar_real(jkey,int(qp.get(jb_k,0) or 0),int(qp.get(ja_k,0) or 0))
            st.session_state.msg    = "✅ Placares salvos!"
            st.session_state.msg_ok = True
        else:
            st.session_state.msg    = "❌ Senha incorreta!"
            st.session_state.msg_ok = False
        st.query_params.clear()
        st.rerun()

    elif action == "admin_classif":
        if qp.get("pwd","") == "brasil2026":
            ordem = [qp.get(f"rc{i}","") for i in range(1,5)]
            if len(set(ordem))==4 and all(ordem):
                save_classificacao_real([t.upper() for t in ordem])
                st.session_state.msg    = "✅ Classificação salva!"
                st.session_state.msg_ok = True
            else:
                st.session_state.msg    = "❌ Selecione 4 times diferentes!"
                st.session_state.msg_ok = False
        else:
            st.session_state.msg    = "❌ Senha incorreta!"
            st.session_state.msg_ok = False
        st.query_params.clear()
        st.rerun()

handle_action()

# ── Dados ─────────────────────────────────────────────────
placares_reais     = get_placares_reais()
classificacao_real = get_classificacao_real()
scores             = calculate_scores()

JOGOS = [("jogo1","MARROCOS","13/06"),("jogo2","HAITI","19/06"),("jogo3","ESCÓCIA","24/06")]
TIMES = ["BRASIL","MARROCOS","HAITI","ESCÓCIA"]

jogos_js = []
for jkey,adv,data in JOGOS:
    r = placares_reais.get(jkey,{})
    jogos_js.append({"key":jkey,"adv":adv,"data":data,
                     "enc":bool(r.get("encerrado")),
                     "brasil":r.get("brasil"),"adversario":r.get("adversario")})

ranking_js = []
for i,e in enumerate(scores,1):
    det = e["detail"]
    jd  = []
    for jkey,_,_ in JOGOS:
        d = det.get(jkey,{})
        jd.append({"status":d.get("status","pendente"),
                   "palpite":list(d["palpite"]) if "palpite" in d else [],
                   "real":list(d["real"]) if "real" in d else []})
    cl = det.get("classificacao",{})
    ranking_js.append({"pos":i,"nome":e["nome"],"total":e["total"],"jogos":jd,
        "cp":cl.get("palpite",[]),"cr":cl.get("real",[]),
        "cs":{str(k):v for k,v in cl.get("status",{}).items()},
        "cpts":cl.get("pontos",0)})

cr_lista = [classificacao_real.get(i,"") for i in range(1,5)]

MSG    = st.session_state.msg
MSG_OK = st.session_state.msg_ok
st.session_state.msg = ""

JS_DATA = json.dumps({"jogos":jogos_js,"ranking":ranking_js,
                      "cr":cr_lista,"msg":MSG,"msg_ok":MSG_OK},ensure_ascii=False)

# ── HTML completo ─────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,sans-serif;background:#1a1464;color:#fff;min-height:100vh}}

/* TABS */
.tabs{{display:flex;background:#0d0a38;border-bottom:3px solid #ffdf00;position:sticky;top:0;z-index:99}}
.tab{{flex:1;padding:13px 4px;text-align:center;font-weight:900;font-size:clamp(.75rem,3.5vw,1rem);cursor:pointer;color:rgba(255,255,255,.5);border:none;background:none;letter-spacing:.5px}}
.tab.active{{color:#1a1464;background:#ffdf00}}

.page{{display:none;padding:clamp(10px,3vw,20px);max-width:680px;margin:0 auto}}
.page.active{{display:block}}

/* HEADER */
.titulo{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:6px}}
.titulo h1{{font-size:clamp(1.3rem,6vw,2rem);font-weight:900;text-transform:uppercase;color:#fff}}
.grupo-badge{{background:#009c3b;color:#fff;font-weight:900;font-size:clamp(.8rem,3vw,1rem);padding:4px 12px;border-radius:20px}}

/* BRASIL BANNER */
.bb{{display:flex;align-items:stretch;background:#fff;border-radius:14px;overflow:hidden;margin-bottom:14px;min-height:clamp(64px,18vw,96px)}}
.bb-flag{{background:#009c3b;width:42%;display:flex;align-items:center;justify-content:center;padding:clamp(8px,2.5vw,18px)}}
.bb-diamond{{background:#ffdf00;width:clamp(60px,16vw,100px);height:clamp(34px,9vw,56px);clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);display:flex;align-items:center;justify-content:center}}
.bb-circle{{background:#1a1464;width:clamp(18px,4.5vw,28px);height:clamp(18px,4.5vw,28px);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:clamp(4px,1vw,6px);color:#fff;font-weight:900;text-align:center;line-height:1.1}}
.bb-nome{{flex:1;display:flex;align-items:center;justify-content:center;font-size:clamp(1.6rem,7.5vw,2.8rem);font-weight:900;color:#1a1464;letter-spacing:clamp(2px,1.5vw,6px)}}

/* INPUT NOME */
.nome-input{{width:100%;padding:11px 14px;border:1.5px solid rgba(255,255,255,.25);border-radius:10px;background:rgba(255,255,255,.08);color:#fff;font-size:clamp(.9rem,3.5vw,1rem);outline:none;margin-bottom:12px}}
.nome-input:focus{{border-color:#ffdf00}}
.nome-input::placeholder{{color:rgba(255,255,255,.4)}}

/* JOGO CARD */
.jogo-card{{background:#fff;border-radius:14px;margin-bottom:14px;overflow:hidden}}
.jogo-titulo{{background:#e8e8f0;text-align:center;font-weight:900;font-size:clamp(.8rem,3.5vw,1rem);padding:10px;color:#2a1b6b;text-transform:uppercase;letter-spacing:1px}}
.jogo-body{{display:grid;grid-template-columns:1fr clamp(42px,12vw,60px) clamp(20px,5vw,28px) clamp(42px,12vw,60px) 1fr;align-items:center;gap:clamp(4px,2vw,10px);padding:clamp(10px,3vw,14px)}}
.jt{{font-weight:900;font-size:clamp(.78rem,3.5vw,1.05rem);color:#2a1b6b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.jt.home{{text-align:left}}.jt.away{{text-align:right}}
.jx{{font-weight:900;font-size:clamp(.9rem,4vw,1.2rem);color:#2a1b6b;text-align:center}}
.jinput{{width:100%;aspect-ratio:1;border:2.5px solid #1a1464;border-radius:8px;background:#fff;color:#1a1464;font-size:clamp(1rem,5vw,1.5rem);font-weight:900;text-align:center;-moz-appearance:textfield;appearance:textfield;outline:none;padding:0;touch-action:manipulation}}
.jinput::-webkit-outer-spin-button,.jinput::-webkit-inner-spin-button{{-webkit-appearance:none}}
.jinput:focus{{border-color:#009c3b;box-shadow:0 0 0 3px rgba(0,156,59,.25)}}
.jscore{{width:100%;aspect-ratio:1;border:2.5px solid #1a1464;border-radius:8px;background:#f0f0f0;color:#1a1464;font-size:clamp(1rem,5vw,1.5rem);font-weight:900;text-align:center;display:flex;align-items:center;justify-content:center}}
.jrodape{{text-align:center;font-size:clamp(.68rem,2.8vw,.82rem);font-weight:700;color:#2a1b6b;padding:8px;border-top:1px solid #eee}}
.jrodape .red{{color:#e53935;font-weight:900}}

/* CARDS */
.card{{background:#fff;border-radius:14px;padding:clamp(10px,3vw,16px);margin-bottom:14px}}
.card,.card *{{color:#2a1b6b}}
.card h4{{font-weight:900;font-size:clamp(.88rem,3.5vw,1rem);margin-bottom:8px}}
.card p{{font-size:clamp(.78rem,3vw,.88rem);line-height:1.5}}

/* DESCRIÇÃO + PONTUAÇÃO */
.desc-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
@media(max-width:480px){{.desc-row{{grid-template-columns:1fr}}}}
.pts-item{{display:flex;align-items:flex-start;gap:8px;padding:5px 0;border-bottom:1px solid rgba(42,27,107,.1)}}
.pts-item:last-child{{border-bottom:none}}
.pts-num{{font-weight:900;font-size:clamp(1rem,4vw,1.3rem);color:#e53935;min-width:42px;line-height:1.1}}
.pts-txt{{font-size:clamp(.75rem,2.8vw,.85rem)}}

/* CLASSIFICAÇÃO */
.classif-card{{background:#1e1560;border:1px solid rgba(255,255,255,.15);border-radius:14px;padding:clamp(10px,3vw,16px);margin-bottom:14px}}
.classif-card h3{{font-weight:900;font-size:clamp(.9rem,4vw,1.1rem);color:#fff;text-align:center;margin-bottom:14px}}
.sel-label{{font-weight:700;font-size:clamp(.8rem,3vw,.9rem);color:rgba(255,255,255,.8);margin-bottom:4px;letter-spacing:.5px}}
select.sel{{width:100%;padding:10px 14px;border:1.5px solid rgba(255,255,255,.25);border-radius:10px;background:rgba(255,255,255,.1);color:#fff;font-size:clamp(.9rem,3.5vw,1rem);outline:none;margin-bottom:10px;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M0 0l6 8 6-8z' fill='white'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;background-color:rgba(255,255,255,.1)}}
select.sel option{{background:#1e1560;color:#fff}}

/* FOOTER BANNER */
.footer-banner{{background:#fff;border-radius:14px;padding:clamp(10px,3vw,14px);display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:14px}}
.money-box{{background:#009c3b;padding:clamp(8px,2.5vw,12px);border-radius:10px;text-align:center;min-width:clamp(100px,28vw,130px);flex-shrink:0}}
.money-box,.money-box *{{color:#fff!important}}
.money-val{{font-size:clamp(1.2rem,5.5vw,1.6rem);font-weight:900;display:block}}
.footer-right{{flex:1;min-width:160px}}
.footer-right p{{text-align:center;color:#2a1b6b;font-weight:900;font-size:clamp(.72rem,3vw,.9rem);margin-bottom:8px}}
.prizes{{display:flex;justify-content:space-around;flex-wrap:wrap;gap:4px}}
.prize .pts{{color:#e53935;font-weight:900;font-size:clamp(.8rem,3.5vw,1rem)}}
.prize .lbl{{color:#2a1b6b;font-weight:700;font-size:clamp(.58rem,2vw,.72rem)}}
.obs{{font-size:clamp(.65rem,2.5vw,.75rem);color:rgba(255,255,255,.5);line-height:1.5;margin-bottom:14px}}

/* NOME/DATA */
.nome-data{{display:grid;grid-template-columns:2fr 1fr;gap:12px}}
.nd-label{{font-weight:700;font-size:.75rem;margin-bottom:3px;opacity:.6}}
.nd-val{{font-weight:900;font-size:clamp(.9rem,3.5vw,1.05rem)}}

/* BOTÕES */
.btn{{width:100%;padding:clamp(12px,3vw,14px);border:none;border-radius:12px;font-size:clamp(.95rem,4vw,1.1rem);font-weight:900;cursor:pointer;letter-spacing:1px;touch-action:manipulation}}
.btn-y{{background:#ffdf00;color:#1a1464}}
.btn-g{{background:#009c3b;color:#fff}}
.btn-gray{{background:rgba(255,255,255,.15);color:#fff}}
.btn-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}}

/* MENSAGENS */
.msg{{padding:12px 16px;border-radius:10px;font-weight:700;font-size:clamp(.85rem,3vw,.95rem);margin-bottom:14px}}
.msg.ok{{background:rgba(0,156,59,.2);border:1px solid #009c3b;color:#7fffb0}}
.msg.err{{background:rgba(200,16,46,.2);border:1px solid #c8102e;color:#ffaaaa}}
.saved-badge{{background:rgba(0,156,59,.15);border:1px solid #009c3b;border-radius:10px;padding:12px 16px;margin-bottom:16px}}
.sec-title{{font-weight:900;font-size:clamp(.88rem,3.5vw,1.1rem);color:#fff;letter-spacing:2px;border-left:4px solid #ffdf00;padding-left:10px;margin:16px 0 10px;text-transform:uppercase}}

/* AVISO */
.aviso{{background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.25);border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:clamp(.78rem,3vw,.88rem);color:rgba(255,255,255,.7)}}

/* CONFIRMAÇÃO */
.confirm-box{{background:rgba(200,16,46,.1);border:1px solid rgba(200,16,46,.35);border-radius:10px;padding:12px;margin-bottom:10px;font-weight:700;color:#ffaaaa}}

/* RANKING */
.status-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}}
.sc{{border-radius:10px;padding:clamp(8px,2.5vw,12px);text-align:center;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05)}}
.sc.enc{{border-color:rgba(0,156,59,.5);background:rgba(0,156,59,.12)}}
.sc-j{{font-size:clamp(.65rem,2.5vw,.75rem);color:rgba(255,255,255,.5);font-weight:700;letter-spacing:1px;text-transform:uppercase}}
.sc-p{{font-size:clamp(1rem,4vw,1.3rem);font-weight:900;color:#ffdf00;line-height:1.2}}
.sc-t{{font-size:clamp(.62rem,2.2vw,.72rem);font-weight:700}}
.rank-card{{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:clamp(10px,3vw,14px) clamp(12px,3.5vw,18px);margin-bottom:8px;cursor:pointer;transition:.15s}}
.rank-card:hover{{border-color:#ffdf00}}
.rank-card.r1{{border-color:#ffd700;background:rgba(255,215,0,.08)}}
.rank-card.r2{{border-color:#c0c0c0;background:rgba(192,192,192,.06)}}
.rank-card.r3{{border-color:#cd7f32;background:rgba(205,127,50,.06)}}
.rpos{{font-weight:900;font-size:clamp(1.2rem,5vw,1.5rem);min-width:32px;text-align:center;color:rgba(255,255,255,.3)}}
.r1 .rpos{{color:#ffd700}}.r2 .rpos{{color:#c0c0c0}}.r3 .rpos{{color:#cd7f32}}
.rnome{{flex:1;font-weight:900;font-size:clamp(.88rem,3.5vw,1.05rem);color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.rpts{{font-weight:900;font-size:clamp(1.2rem,5vw,1.5rem);color:#ffdf00;text-align:right}}
.rpts-l{{font-size:clamp(.6rem,2.2vw,.7rem);color:rgba(255,255,255,.4);text-align:right}}
.detail-panel{{background:rgba(255,255,255,.04);border-radius:10px;padding:12px;margin-bottom:8px;display:none;font-size:clamp(.78rem,3vw,.88rem)}}
.detail-panel.open{{display:block}}
.dl{{padding:4px 0;color:rgba(255,255,255,.85);border-bottom:1px solid rgba(255,255,255,.06)}}
.dl:last-child{{border-bottom:none}}
.ok-t{{color:#7fffb0;font-weight:700}}.err-t{{color:#ffaaaa}}.pend-t{{color:rgba(255,255,255,.4)}}
.cf-row{{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:10px 14px;margin-bottom:6px;color:#fff}}

/* ADMIN */
.admin-warn{{background:rgba(200,16,46,.08);border:1px solid rgba(200,16,46,.25);border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:.88rem;color:rgba(255,255,255,.7)}}
.admin-section{{background:rgba(200,16,46,.07);border:1px solid rgba(200,16,46,.25);border-radius:12px;padding:14px;margin-bottom:14px}}
.admin-grid{{display:grid;grid-template-columns:1fr clamp(50px,13vw,68px) 24px clamp(50px,13vw,68px);align-items:center;gap:10px;margin:10px 0}}
.ainput{{width:100%;padding:8px;border:1.5px solid rgba(255,255,255,.2);border-radius:8px;background:rgba(255,255,255,.1);color:#fff;font-size:1rem;font-weight:900;text-align:center;outline:none;-moz-appearance:textfield}}
.ainput::-webkit-outer-spin-button,.ainput::-webkit-inner-spin-button{{-webkit-appearance:none}}
</style>
</head>
<body>

<div class="tabs">
  <button class="tab active" onclick="goTab('form',this)">📝 PARTICIPAR</button>
  <button class="tab"        onclick="goTab('rank',this)">🏆 RANKING</button>
  <button class="tab"        onclick="goTab('admin',this)">⚙️ ADMIN</button>
</div>

<!-- ══════════ PARTICIPAR ══════════ -->
<div id="pg-form" class="page active">
  <div id="msg-area"></div>

  <div class="titulo">
    <h1>Jogos do Brasil</h1>
    <span class="grupo-badge">GRUPO C</span>
  </div>

  <div class="bb">
    <div class="bb-flag">
      <div class="bb-diamond"><div class="bb-circle">ORDEM E<br>PROGRESSO</div></div>
    </div>
    <div class="bb-nome">BRASIL</div>
  </div>

  <input id="nome-inp" class="nome-input" type="text"
         placeholder="Digite seu nome completo..."
         oninput="onNome(this.value)">

  <div id="hint" style="text-align:center;padding:20px;color:rgba(255,255,255,.3);font-weight:700;font-size:.9rem;">
    DIGITE SEU NOME PARA CONTINUAR 👆
  </div>

  <!-- Formulário novo palpite -->
  <div id="form-novo" style="display:none">
    <div class="aviso">⚠️ <b>Atenção:</b> após confirmar, seu palpite <b>não poderá ser alterado</b>.</div>

    <!-- JOGO 1 -->
    <div class="jogo-card">
      <div class="jogo-titulo">JOGO 1 (13/06)</div>
      <div class="jogo-body">
        <span class="jt home">BRASIL</span>
        <input class="jinput" id="j1b" type="number" min="0" max="20" value="0">
        <span class="jx">X</span>
        <input class="jinput" id="j1a" type="number" min="0" max="20" value="0">
        <span class="jt away">MARROCOS</span>
      </div>
      <div class="jrodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <!-- JOGO 2 -->
    <div class="jogo-card">
      <div class="jogo-titulo">JOGO 2 (19/06)</div>
      <div class="jogo-body">
        <span class="jt home">BRASIL</span>
        <input class="jinput" id="j2b" type="number" min="0" max="20" value="0">
        <span class="jx">X</span>
        <input class="jinput" id="j2a" type="number" min="0" max="20" value="0">
        <span class="jt away">HAITI</span>
      </div>
      <div class="jrodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <!-- JOGO 3 -->
    <div class="jogo-card">
      <div class="jogo-titulo">JOGO 3 (24/06)</div>
      <div class="jogo-body">
        <span class="jt home">BRASIL</span>
        <input class="jinput" id="j3b" type="number" min="0" max="20" value="0">
        <span class="jx">X</span>
        <input class="jinput" id="j3a" type="number" min="0" max="20" value="0">
        <span class="jt away">ESCÓCIA</span>
      </div>
      <div class="jrodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <!-- Desc + Pts -->
    <div class="desc-row">
      <div class="card">
        <h4>DESCRIÇÃO:</h4>
        <p>Preencha os placares e ordene os times do Grupo C da 1ª à 4ª colocação. Ganha quem acertar os placares e a ordem final!</p>
      </div>
      <div class="card">
        <h4>🏆 PONTUAÇÃO:</h4>
        <div class="pts-item"><span class="pts-num">50</span><span class="pts-txt"><b>Placar exato</b> de cada jogo</span></div>
        <div class="pts-item"><span class="pts-num">30</span><span class="pts-txt"><b>Colocado individual</b> correto</span></div>
        <div class="pts-item"><span class="pts-num">100</span><span class="pts-txt"><b>Gabaritar</b> a classificação</span></div>
      </div>
    </div>

    <!-- Classificação -->
    <div class="classif-card">
      <h3>🏆 CLASSIFICAÇÃO DO GRUPO C</h3>
      <div class="sel-label">1º Colocado</div>
      <select id="c1" class="sel"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="sel-label">2º Colocado</div>
      <select id="c2" class="sel"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="sel-label">3º Colocado</div>
      <select id="c3" class="sel"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="sel-label">4º Colocado</div>
      <select id="c4" class="sel"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
    </div>

    <!-- Nome + Data -->
    <div class="card">
      <div class="nome-data">
        <div><div class="nd-label">NOME</div><div class="nd-val" id="nome-display">—</div></div>
        <div><div class="nd-label">DATA</div><div class="nd-val" id="data-display">—</div></div>
      </div>
    </div>

    <!-- Footer -->
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

    <div id="btn-area">
      <button class="btn btn-y" onclick="validar()">ENVIAR PALPITE 🇧🇷</button>
    </div>
    <div id="confirm-area" style="display:none">
      <div class="confirm-box">⚠️ CONFIRME SEU PALPITE — esta ação é irreversível!</div>
      <div class="btn-row">
        <button class="btn btn-g" onclick="enviar()">✅ SIM, ENVIAR</button>
        <button class="btn btn-gray" onclick="cancelar()">✏️ EDITAR</button>
      </div>
    </div>
  </div>

  <!-- Palpite já enviado -->
  <div id="form-salvo" style="display:none">
    <div class="saved-badge">
      <div id="salvo-msg" style="color:#7fffb0;font-weight:700;font-size:1rem;"></div>
      <div style="color:rgba(255,255,255,.5);font-size:.8rem;margin-top:4px;">Os palpites são definitivos e não podem ser alterados.</div>
    </div>
    <div id="salvo-jogos"></div>
  </div>
</div>

<!-- ══════════ RANKING ══════════ -->
<div id="pg-rank" class="page">
  <div class="sec-title" style="margin-top:4px">PLACARES</div>
  <div class="status-grid" id="status-grid"></div>
  <div class="sec-title">CLASSIFICAÇÃO GERAL</div>
  <div id="rank-list"></div>
  <div id="classif-final"></div>
</div>

<!-- ══════════ ADMIN ══════════ -->
<div id="pg-admin" class="page">
  <div class="admin-warn">⚙️ Área exclusiva do organizador</div>
  <div class="sel-label">Senha do administrador</div>
  <div style="display:flex;gap:10px;margin-bottom:8px;">
    <input id="admin-pwd" class="nome-input" type="password" placeholder="••••••••" style="margin-bottom:0;flex:1" onkeydown="if(event.key==='Enter')authAdmin()">
    <button class="btn btn-y" style="width:auto;padding:10px 20px;flex-shrink:0" onclick="authAdmin()">ENTRAR</button>
  </div>
  <div id="admin-msg"></div>
  <div id="admin-body" style="display:none">
    <div style="background:rgba(0,156,59,.12);border:1px solid #009c3b;border-radius:10px;padding:10px 14px;margin-bottom:16px;color:#7fffb0;font-size:.88rem;font-weight:700;">✅ Acesso liberado</div>
    <div class="sec-title">PLACARES REAIS</div>
    <div id="admin-placares"></div>
    <button class="btn btn-g" style="margin-bottom:20px" onclick="savePlacar()">💾 SALVAR PLACARES</button>
    <div class="sec-title">CLASSIFICAÇÃO FINAL</div>
    <div id="admin-classif"></div>
    <button class="btn btn-g" onclick="saveClassif()">💾 SALVAR CLASSIFICAÇÃO</button>
  </div>
</div>

<script>
const D = {JS_DATA};
const TIMES = ['BRASIL','MARROCOS','HAITI','ESCÓCIA'];
const ADVS  = ['MARROCOS','HAITI','ESCÓCIA'];
const DATAS = ['13/06','19/06','24/06'];
const PICONS= ['🥇','🥈','🥉','4°'];

// ── Tabs ─────────────────────────────────────────────────
function goTab(id, el) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('pg-'+id).classList.add('active');
  el.classList.add('active');
}}

// ── Mensagem global ──────────────────────────────────────
function showMsg(txt, ok) {{
  const el = document.getElementById('msg-area');
  el.innerHTML = `<div class="msg ${{ok?'ok':'err'}}">${{txt}}</div>`;
  setTimeout(() => el.innerHTML = '', 7000);
}}

// ── Nome ─────────────────────────────────────────────────
document.getElementById('data-display').textContent =
  new Date().toLocaleDateString('pt-BR');

function onNome(val) {{
  const nome = val.trim();
  document.getElementById('nome-display').textContent = nome || '—';
  document.getElementById('hint').style.display       = nome ? 'none' : 'block';
  document.getElementById('form-novo').style.display  = 'none';
  document.getElementById('form-salvo').style.display = 'none';
  if (!nome) return;

  const entry = D.ranking.find(r => r.nome.toLowerCase() === nome.toLowerCase());
  if (entry) {{
    document.getElementById('form-salvo').style.display = 'block';
    document.getElementById('salvo-msg').innerHTML = `✅ Palpite de <b>${{entry.nome}}</b> já registrado!`;
    let h = '';
    entry.jogos.forEach((j,i) => {{
      const gb = j.palpite[0]??'?', ga = j.palpite[1]??'?';
      h += `<div class="jogo-card">
        <div class="jogo-titulo">JOGO ${{i+1}} (${{DATAS[i]}})</div>
        <div class="jogo-body">
          <span class="jt home">BRASIL</span>
          <span class="jscore">${{gb}}</span>
          <span class="jx">X</span>
          <span class="jscore">${{ga}}</span>
          <span class="jt away">${{ADVS[i]}}</span>
        </div>
        <div class="jrodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
      </div>`;
    }});
    document.getElementById('salvo-jogos').innerHTML = h;
  }} else {{
    document.getElementById('form-novo').style.display = 'block';
  }}
}}

// ── Validar e enviar ──────────────────────────────────────
function validar() {{
  const c1=document.getElementById('c1').value, c2=document.getElementById('c2').value;
  const c3=document.getElementById('c3').value, c4=document.getElementById('c4').value;
  if (!c1||!c2||!c3||!c4) {{ showMsg('❌ Selecione os 4 colocados!', false); return; }}
  if (new Set([c1,c2,c3,c4]).size!==4) {{ showMsg('❌ Selecione times diferentes!', false); return; }}
  document.getElementById('btn-area').style.display     = 'none';
  document.getElementById('confirm-area').style.display = 'block';
}}
function cancelar() {{
  document.getElementById('btn-area').style.display     = 'block';
  document.getElementById('confirm-area').style.display = 'none';
}}
function g(id) {{ return document.getElementById(id).value; }}
function enviar() {{
  // Monta a URL do PARENT (Streamlit real), não do iframe
  const base = window.parent.location.href.split('?')[0];
  const p = new URLSearchParams({{
    action:'submit', nome:g('nome-inp'),
    j1b:g('j1b'), j1a:g('j1a'),
    j2b:g('j2b'), j2a:g('j2a'),
    j3b:g('j3b'), j3a:g('j3a'),
    c1:g('c1'),   c2:g('c2'),
    c3:g('c3'),   c4:g('c4'),
  }});
  window.parent.location.href = base + '?' + p.toString();
}}

// ── Ranking ───────────────────────────────────────────────
function buildRanking() {{
  document.getElementById('status-grid').innerHTML = D.jogos.map(j => {{
    return `<div class="sc ${{j.enc?'enc':''}}">
      <div class="sc-j">Jogo ${{j.key.slice(-1)}} · ${{j.data}}</div>
      ${{j.enc
        ? `<div class="sc-p">Brasil ${{j.brasil}} × ${{j.adversario}}</div><div class="sc-t" style="color:#7fffb0">✅ Encerrado</div>`
        : `<div class="sc-p" style="font-size:.9rem;color:rgba(255,255,255,.3)">—</div><div class="sc-t" style="color:rgba(255,255,255,.3)">⏳ Pendente</div>`
      }}
    </div>`;
  }}).join('');

  const rl = document.getElementById('rank-list');
  if (!D.ranking.length) {{
    rl.innerHTML='<div style="text-align:center;padding:40px;color:rgba(255,255,255,.3);font-weight:700;">NENHUM PALPITE AINDA 🎯</div>';
    return;
  }}
  const rcs = ['r1','r2','r3'];
  const meds= ['🥇','🥈','🥉'];
  rl.innerHTML = `<div style="text-align:right;color:rgba(255,255,255,.35);font-size:.78rem;margin-bottom:8px;">${{D.ranking.length}} participante(s)</div>`;

  D.ranking.forEach(e => {{
    const idx = e.pos-1;
    const card = document.createElement('div');
    card.className = 'rank-card '+(rcs[idx]||'');
    card.innerHTML = `<div class="rpos">${{meds[idx]||e.pos+'°'}}</div>
      <div class="rnome">${{e.nome.toUpperCase()}}</div>
      <div><div class="rpts">${{e.total}}</div><div class="rpts-l">PONTOS</div></div>`;
    card.onclick = () => document.getElementById('dp-'+e.pos).classList.toggle('open');
    rl.appendChild(card);

    const panel = document.createElement('div');
    panel.id = 'dp-'+e.pos;
    panel.className = 'detail-panel';
    let dh = '';
    e.jogos.forEach((j,ji) => {{
      if (j.status==='exato')
        dh+=`<div class="dl">Brasil ${{j.palpite[0]}}×${{j.palpite[1]}} ${{ADVS[ji]}} <span class="ok-t">✅ +50pts</span></div>`;
      else if(j.status==='errado')
        dh+=`<div class="dl">Brasil ${{j.palpite[0]}}×${{j.palpite[1]}} ${{ADVS[ji]}} <span class="err-t">❌ (real: ${{j.real[0]}}×${{j.real[1]}})</span></div>`;
      else {{
        const pal = j.palpite.length ? j.palpite[0]+'×'+j.palpite[1] : '—';
        dh+=`<div class="dl">Brasil ${{pal}} ${{ADVS[ji]}} <span class="pend-t">⏳</span></div>`;
      }}
    }});
    if (e.cp.length) {{
      dh+='<div class="dl" style="margin-top:6px;font-weight:700;border:none;">Classificação:</div>';
      e.cp.forEach((t,ci) => {{
        const st=e.cs[String(ci+1)];
        const tag=st==='acerto'?'<span class="ok-t">✅ +30pts</span>'
          :st==='errado'?`<span class="err-t">❌ (era ${{e.cr[ci]||'?'}})</span>`
          :'<span class="pend-t">⏳</span>';
        dh+=`<div class="dl">${{PICONS[ci]}} ${{t}} ${{tag}}</div>`;
      }});
      if (e.cs['gabarito']===true) dh+='<div class="dl"><span class="ok-t">🏆 GABARITO! +100pts bônus</span></div>';
    }}
    panel.innerHTML = dh;
    rl.appendChild(panel);
  }});

  const cfa = document.getElementById('classif-final');
  if (D.cr.some(t=>t)) {{
    cfa.innerHTML = '<div class="sec-title">CLASSIFICAÇÃO FINAL · GRUPO C</div>'
      + D.cr.map((t,i)=>`<div class="cf-row"><span style="font-size:1.1rem">${{PICONS[i]}}</span><span style="font-weight:900;font-size:1rem;">${{t}}</span></div>`).join('');
  }}
}}

// ── Admin ─────────────────────────────────────────────────
function authAdmin() {{
  const pwd = document.getElementById('admin-pwd').value;
  const msg = document.getElementById('admin-msg');
  if (pwd === 'brasil2026') {{
    document.getElementById('admin-body').style.display = 'block';
    msg.innerHTML = '';
    buildAdmin();
  }} else {{
    msg.innerHTML = '<div class="msg err">❌ Senha incorreta!</div>';
    document.getElementById('admin-body').style.display = 'none';
  }}
}}

function buildAdmin() {{
  const KEYS = ['jogo1','jogo2','jogo3'];
  let ph = '';
  D.jogos.forEach((j,i) => {{
    const vb=j.brasil??0, va=j.adversario??0;
    ph += `<div class="admin-section">
      <b>Jogo ${{i+1}} (${{j.data}}) — Brasil × ${{ADVS[i]}}</b>
      ${{j.enc?`<div style="color:#7fffb0;font-size:.82rem;margin:6px 0;">✅ Salvo: Brasil ${{vb}} × ${{va}}</div>`:''}}
      <div class="admin-grid">
        <span style="font-weight:700;font-size:.88rem;color:#fff;">Brasil</span>
        <input class="ainput" id="r${{i+1}}b" type="number" min="0" max="20" value="${{vb}}">
        <span style="text-align:center;font-weight:900;color:#fff;">×</span>
        <input class="ainput" id="r${{i+1}}a" type="number" min="0" max="20" value="${{va}}">
      </div>
      <label style="font-size:.82rem;color:rgba(255,255,255,.7);display:flex;align-items:center;gap:8px;margin-top:8px;cursor:pointer;">
        <input type="checkbox" id="enc_${{KEYS[i]}}" ${{j.enc?'checked':''}}>
        Marcar como encerrado
      </label>
    </div>`;
  }});
  document.getElementById('admin-placares').innerHTML = ph;

  let ch = '';
  for(let i=1;i<=4;i++) {{
    const cur = (D.cr[i-1]||'').toUpperCase();
    ch += `<div class="sel-label">${{i}}º Colocado</div>
    <select id="rc${{i}}" class="sel">
      <option value="">-- Selecione --</option>
      ${{TIMES.map(t=>`<option value="${{t}}" ${{t===cur?'selected':''}}>${{t}}</option>`).join('')}}
    </select>`;
  }}
  document.getElementById('admin-classif').innerHTML = ch;
}}

function savePlacar() {{
  const pwd = document.getElementById('admin-pwd').value;
  const base = window.parent.location.href.split('?')[0];
  const p = new URLSearchParams({{action:'admin_placar',pwd}});
  ['jogo1','jogo2','jogo3'].forEach((k,i) => {{
    p.set('r'+(i+1)+'b', document.getElementById('r'+(i+1)+'b').value||0);
    p.set('r'+(i+1)+'a', document.getElementById('r'+(i+1)+'a').value||0);
    if(document.getElementById('enc_'+k).checked) p.set('enc_'+k,'1');
  }});
  window.parent.location.href = base + '?' + p.toString();
}}

function saveClassif() {{
  const pwd = document.getElementById('admin-pwd').value;
  const base = window.parent.location.href.split('?')[0];
  const p = new URLSearchParams({{action:'admin_classif',pwd}});
  for(let i=1;i<=4;i++) p.set('rc'+i, document.getElementById('rc'+i).value);
  window.parent.location.href = base + '?' + p.toString();
}}

// ── Init ──────────────────────────────────────────────────
buildRanking();
if (D.msg) showMsg(D.msg, D.msg_ok);
</script>
</body>
</html>"""

st.components.v1.html(HTML, height=2800, scrolling=True)
