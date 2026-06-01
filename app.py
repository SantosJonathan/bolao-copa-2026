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
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #1a1464; }
</style>
""", unsafe_allow_html=True)

init_db()

# ── Estado da sessão ─────────────────────────────────────
if "page"    not in st.session_state: st.session_state.page    = "form"
if "msg"     not in st.session_state: st.session_state.msg     = ""
if "msg_ok"  not in st.session_state: st.session_state.msg_ok  = True
if "confirm" not in st.session_state: st.session_state.confirm = None

# ── Dados para o frontend ────────────────────────────────
placares_reais     = get_placares_reais()
classificacao_real = get_classificacao_real()
scores             = calculate_scores()

jogos_status = []
for jkey, jadv, jdata in [("jogo1","MARROCOS","13/06"),("jogo2","HAITI","19/06"),("jogo3","ESCÓCIA","24/06")]:
    r = placares_reais.get(jkey, {})
    jogos_status.append({
        "key": jkey, "adv": jadv, "data": jdata,
        "encerrado": bool(r.get("encerrado")),
        "brasil": r.get("brasil"), "adversario": r.get("adversario"),
    })

ranking_data = []
for i, e in enumerate(scores, 1):
    det = e["detail"]
    jogos_det = []
    for jkey in ["jogo1","jogo2","jogo3"]:
        d = det.get(jkey, {})
        jogos_det.append({
            "status": d.get("status","pendente"),
            "palpite": list(d["palpite"]) if "palpite" in d else [],
            "real":    list(d["real"])    if "real"    in d else [],
        })
    cl = det.get("classificacao", {})
    ranking_data.append({
        "pos": i, "nome": e["nome"], "total": e["total"],
        "jogos": jogos_det,
        "classif_palpite": cl.get("palpite", []),
        "classif_real":    cl.get("real", []),
        "classif_status":  {str(k): v for k, v in cl.get("status", {}).items()},
        "classif_pts":     cl.get("pontos", 0),
    })

classif_real_lista = [classificacao_real.get(i,"") for i in range(1,5)]

# ── Processa ações do formulário ─────────────────────────
query = st.query_params

def handle_action():
    action = query.get("action","")

    if action == "submit":
        nome    = query.get("nome","").strip()
        j1b     = int(query.get("j1b","0") or 0)
        j1a     = int(query.get("j1a","0") or 0)
        j2b     = int(query.get("j2b","0") or 0)
        j2a     = int(query.get("j2a","0") or 0)
        j3b     = int(query.get("j3b","0") or 0)
        j3a     = int(query.get("j3a","0") or 0)
        c1      = query.get("c1","")
        c2      = query.get("c2","")
        c3      = query.get("c3","")
        c4      = query.get("c4","")

        if not nome:
            st.session_state.msg    = "Informe seu nome!"
            st.session_state.msg_ok = False
        elif palpite_enviado(nome):
            st.session_state.msg    = f"Palpite de {nome} já registrado!"
            st.session_state.msg_ok = False
        elif not all([c1,c2,c3,c4]) or len({c1,c2,c3,c4}) != 4:
            st.session_state.msg    = "Selecione os 4 colocados sem repetir!"
            st.session_state.msg_ok = False
        else:
            ok = save_palpite(
                nome,
                {"jogo1":(j1b,j1a),"jogo2":(j2b,j2a),"jogo3":(j3b,j3a)},
                (c1,c2,c3,c4),
            )
            if ok:
                st.session_state.msg    = f"✅ Palpite de {nome} registrado! Boa sorte 🇧🇷"
                st.session_state.msg_ok = True
                st.session_state.page   = "form"
            else:
                st.session_state.msg    = "Palpite já registrado e não pode ser alterado."
                st.session_state.msg_ok = False
        st.query_params.clear()
        st.rerun()

    elif action == "admin_save_placar":
        pwd  = query.get("pwd","")
        if pwd == "brasil2026":
            for jkey, jb, ja in [
                ("jogo1", int(query.get("r1b","0") or 0), int(query.get("r1a","0") or 0)),
                ("jogo2", int(query.get("r2b","0") or 0), int(query.get("r2a","0") or 0)),
                ("jogo3", int(query.get("r3b","0") or 0), int(query.get("r3a","0") or 0)),
            ]:
                if query.get(f"enc_{jkey}"):
                    save_placar_real(jkey, jb, ja)
            st.session_state.msg    = "✅ Placares salvos!"
            st.session_state.msg_ok = True
        else:
            st.session_state.msg    = "❌ Senha incorreta!"
            st.session_state.msg_ok = False
        st.query_params.clear()
        st.rerun()

    elif action == "admin_save_classif":
        pwd = query.get("pwd","")
        if pwd == "brasil2026":
            ordem = [query.get(f"rc{i}","") for i in range(1,5)]
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
        st.query_params.clear()
        st.rerun()

if query.get("action"):
    handle_action()

# ── HTML principal ───────────────────────────────────────
MSG      = st.session_state.msg
MSG_OK   = st.session_state.msg_ok
st.session_state.msg = ""

JS_DATA  = json.dumps({
    "jogos":       jogos_status,
    "ranking":     ranking_data,
    "classif_real": classif_real_lista,
    "msg":         MSG,
    "msg_ok":      MSG_OK,
}, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bolão Copa 2026</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Arial',sans-serif;background:#1a1464;color:#fff;min-height:100vh}}

/* ── TABS ── */
.tabs{{display:flex;background:#0d0a38;border-bottom:2px solid #ffdf00}}
.tab{{flex:1;padding:14px 4px;text-align:center;font-weight:900;font-size:clamp(0.75rem,3.5vw,1rem);cursor:pointer;color:rgba(255,255,255,0.5);letter-spacing:0.5px;border:none;background:none;transition:.2s}}
.tab.active{{color:#1a1464;background:#ffdf00}}
.page{{display:none;padding:clamp(8px,3vw,20px);max-width:700px;margin:0 auto}}
.page.active{{display:block}}

/* ── HEADER ── */
.titulo{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:6px}}
.titulo h1{{font-size:clamp(1.3rem,6vw,2rem);font-weight:900;text-transform:uppercase;color:#fff}}
.grupo-badge{{background:#009c3b;color:#fff;font-weight:900;font-size:clamp(0.8rem,3vw,1rem);padding:4px 12px;border-radius:20px}}

/* ── BRASIL BANNER ── */
.brasil-banner{{display:flex;align-items:stretch;background:#fff;border-radius:14px;overflow:hidden;margin-bottom:16px;min-height:clamp(64px,18vw,96px)}}
.flag-side{{background:#009c3b;width:42%;display:flex;align-items:center;justify-content:center;padding:clamp(8px,2.5vw,18px)}}
.diamond{{background:#ffdf00;width:clamp(60px,16vw,100px);height:clamp(34px,9vw,56px);clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);display:flex;align-items:center;justify-content:center}}
.circle{{background:#1a1464;width:clamp(18px,4.5vw,28px);height:clamp(18px,4.5vw,28px);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:clamp(4px,1vw,6px);color:#fff;font-weight:900;text-align:center;line-height:1.1}}
.brasil-nome{{flex:1;display:flex;align-items:center;justify-content:center;font-size:clamp(1.6rem,7.5vw,2.8rem);font-weight:900;color:#1a1464;letter-spacing:clamp(2px,1.5vw,6px)}}

/* ── CARD BRANCO ── */
.card{{background:#fff;border-radius:14px;padding:clamp(10px,3vw,16px);margin-bottom:14px;color:#2a1b6b}}
.card *{{color:#2a1b6b}}

/* ── JOGO CARD ── */
.jogo-card{{background:#fff;border-radius:14px;margin-bottom:14px;overflow:hidden}}
.jogo-titulo{{background:#e8e8f0;text-align:center;font-weight:900;font-size:clamp(0.8rem,3.5vw,1rem);padding:10px;color:#2a1b6b;text-transform:uppercase;letter-spacing:1px}}
.jogo-body{{display:grid;grid-template-columns:1fr clamp(42px,12vw,60px) clamp(20px,5vw,30px) clamp(42px,12vw,60px) 1fr;align-items:center;gap:clamp(4px,2vw,10px);padding:clamp(10px,3vw,14px)}}
.jogo-time{{font-weight:900;font-size:clamp(0.78rem,3.5vw,1.05rem);color:#2a1b6b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.jogo-time.home{{text-align:left}}
.jogo-time.away{{text-align:right}}
.jogo-x{{font-weight:900;font-size:clamp(0.9rem,4vw,1.2rem);color:#2a1b6b;text-align:center}}
.jogo-input{{width:100%;aspect-ratio:1;border:2.5px solid #1a1464;border-radius:8px;background:#fff;color:#1a1464;font-size:clamp(1rem,5vw,1.5rem);font-weight:900;text-align:center;-moz-appearance:textfield;appearance:textfield;outline:none;padding:0;touch-action:manipulation}}
.jogo-input::-webkit-outer-spin-button,.jogo-input::-webkit-inner-spin-button{{-webkit-appearance:none}}
.jogo-input:focus{{border-color:#009c3b;box-shadow:0 0 0 3px rgba(0,156,59,0.25)}}
.jogo-score{{width:100%;aspect-ratio:1;border:2.5px solid #1a1464;border-radius:8px;background:#f0f0f0;color:#1a1464;font-size:clamp(1rem,5vw,1.5rem);font-weight:900;text-align:center;display:flex;align-items:center;justify-content:center}}
.jogo-rodape{{background:#fff;text-align:center;font-size:clamp(0.68rem,2.8vw,0.82rem);font-weight:700;color:#2a1b6b;padding:8px;border-top:1px solid #eee}}
.jogo-rodape .red{{color:#e53935;font-weight:900}}

/* ── INPUTS GERAIS ── */
.input-field{{width:100%;padding:10px 14px;border:1.5px solid rgba(255,255,255,0.2);border-radius:10px;background:rgba(255,255,255,0.1);color:#fff;font-size:clamp(0.9rem,3.5vw,1rem);outline:none;margin-bottom:10px}}
.input-field:focus{{border-color:#ffdf00}}
.input-label{{font-weight:700;font-size:clamp(0.8rem,3vw,0.9rem);margin-bottom:5px;color:rgba(255,255,255,0.8);letter-spacing:.5px}}
select.input-field{{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M0 0l6 8 6-8z' fill='white'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;background-color:rgba(255,255,255,0.1);cursor:pointer}}
select.input-field option{{background:#2a1b6b;color:#fff}}

/* ── BOTÕES ── */
.btn{{width:100%;padding:clamp(12px,3vw,14px);border:none;border-radius:12px;font-size:clamp(0.95rem,4vw,1.1rem);font-weight:900;cursor:pointer;touch-action:manipulation;letter-spacing:1px}}
.btn-yellow{{background:#ffdf00;color:#1a1464}}
.btn-green{{background:#009c3b;color:#fff}}
.btn-red{{background:#c8102e;color:#fff}}
.btn-gray{{background:rgba(255,255,255,0.15);color:#fff}}
.btn-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}}

/* ── MENSAGEM ── */
.msg{{padding:12px 16px;border-radius:10px;font-weight:700;font-size:clamp(0.85rem,3vw,0.95rem);margin-bottom:14px;display:none}}
.msg.show{{display:block}}
.msg.ok{{background:rgba(0,156,59,0.2);border:1px solid #009c3b;color:#7fffb0}}
.msg.err{{background:rgba(200,16,46,0.2);border:1px solid #c8102e;color:#ffaaaa}}

/* ── DESC + PONTUAÇÃO ── */
.desc-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
@media(max-width:480px){{.desc-row{{grid-template-columns:1fr}}}}
.pts-item{{display:flex;align-items:flex-start;gap:8px;padding:5px 0;border-bottom:1px solid rgba(42,27,107,.1)}}
.pts-item:last-child{{border-bottom:none}}
.pts-num{{font-weight:900;font-size:clamp(1rem,4vw,1.3rem);color:#e53935;min-width:42px;line-height:1.1}}

/* ── FOOTER BANNER ── */
.footer-banner{{background:#fff;border-radius:14px;padding:clamp(10px,3vw,14px);display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:14px}}
.money-box{{background:#009c3b;padding:clamp(8px,2.5vw,12px);border-radius:10px;text-align:center;min-width:clamp(100px,28vw,130px);flex-shrink:0}}
.money-box *{{color:#fff!important}}
.money-val{{font-size:clamp(1.2rem,5.5vw,1.6rem);font-weight:900;display:block}}
.footer-right{{flex:1;min-width:160px}}
.footer-right p{{text-align:center;color:#2a1b6b;font-weight:900;font-size:clamp(0.72rem,3vw,0.9rem);margin-bottom:8px}}
.prizes{{display:flex;justify-content:space-around;flex-wrap:wrap;gap:4px}}
.prize{{text-align:center}}
.prize .pts{{color:#e53935;font-weight:900;font-size:clamp(0.8rem,3.5vw,1rem)}}
.prize .lbl{{color:#2a1b6b;font-weight:700;font-size:clamp(0.58rem,2vw,0.72rem)}}
.obs{{font-size:clamp(0.65rem,2.5vw,0.75rem);color:rgba(255,255,255,0.5);line-height:1.5;margin-bottom:14px}}

/* ── SEÇÃO TITLE ── */
.sec-title{{font-weight:900;font-size:clamp(0.88rem,3.5vw,1.1rem);color:#fff;letter-spacing:2px;border-left:4px solid #ffdf00;padding-left:10px;margin:18px 0 10px;text-transform:uppercase}}

/* ── NOME/DATA CARD ── */
.nome-data{{display:grid;grid-template-columns:2fr 1fr;gap:12px}}
.nd-label{{font-weight:700;font-size:0.75rem;margin-bottom:3px;color:rgba(42,27,107,0.7)}}
.nd-val{{font-weight:900;font-size:clamp(0.9rem,3.5vw,1.05rem);color:#1a1464}}

/* ── RANKING ── */
.rank-status-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}}
.status-card{{border-radius:10px;padding:clamp(8px,2.5vw,12px);text-align:center;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05)}}
.status-card.enc{{border-color:rgba(0,156,59,0.5);background:rgba(0,156,59,0.12)}}
.status-jogo{{font-size:clamp(0.65rem,2.5vw,0.75rem);color:rgba(255,255,255,0.5);font-weight:700;letter-spacing:1px;text-transform:uppercase}}
.status-placar{{font-size:clamp(1rem,4vw,1.3rem);font-weight:900;color:#ffdf00;line-height:1.2}}
.status-tag{{font-size:clamp(0.62rem,2.2vw,0.72rem);font-weight:700}}

.rank-card{{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:clamp(10px,3vw,14px) clamp(12px,3.5vw,18px);margin-bottom:8px;cursor:pointer;transition:.2s}}
.rank-card:hover{{border-color:#ffdf00}}
.rank-card.r1{{border-color:#ffd700;background:rgba(255,215,0,0.08)}}
.rank-card.r2{{border-color:#c0c0c0;background:rgba(192,192,192,0.06)}}
.rank-card.r3{{border-color:#cd7f32;background:rgba(205,127,50,0.06)}}
.rank-pos{{font-weight:900;font-size:clamp(1.2rem,5vw,1.5rem);min-width:32px;text-align:center;color:rgba(255,255,255,0.3)}}
.r1 .rank-pos{{color:#ffd700}}.r2 .rank-pos{{color:#c0c0c0}}.r3 .rank-pos{{color:#cd7f32}}
.rank-nome{{flex:1;font-weight:900;font-size:clamp(0.88rem,3.5vw,1.05rem);color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.rank-pts-val{{font-weight:900;font-size:clamp(1.2rem,5vw,1.5rem);color:#ffdf00;text-align:right}}
.rank-pts-lbl{{font-size:clamp(0.6rem,2.2vw,0.7rem);color:rgba(255,255,255,0.4);text-align:right}}

.detail-panel{{background:rgba(255,255,255,0.04);border-radius:10px;padding:12px;margin-bottom:8px;display:none;font-size:clamp(0.78rem,3vw,0.88rem)}}
.detail-panel.open{{display:block}}
.detail-line{{padding:4px 0;color:rgba(255,255,255,0.8);border-bottom:1px solid rgba(255,255,255,0.06)}}
.detail-line:last-child{{border-bottom:none}}
.ok-tag{{color:#7fffb0;font-weight:700}}.err-tag{{color:#ffaaaa}}.pend-tag{{color:rgba(255,255,255,0.4)}}

/* ── CLASSIF FINAL ── */
.cf-row{{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 14px;margin-bottom:6px}}
.cf-pos{{font-size:1.1rem}}.cf-nome{{font-weight:900;font-size:clamp(0.88rem,3.5vw,1rem);color:#fff}}

/* ── ADMIN ── */
.admin-grid{{display:grid;grid-template-columns:1fr clamp(44px,12vw,64px) 20px clamp(44px,12vw,64px);align-items:center;gap:10px;margin:10px 0}}
.admin-input{{width:100%;padding:8px;border:1.5px solid rgba(255,255,255,0.2);border-radius:8px;background:rgba(255,255,255,0.1);color:#fff;font-size:1rem;font-weight:900;text-align:center;outline:none;-moz-appearance:textfield}}
.admin-input::-webkit-outer-spin-button,.admin-input::-webkit-inner-spin-button{{-webkit-appearance:none}}
.admin-section{{background:rgba(200,16,46,0.07);border:1px solid rgba(200,16,46,0.25);border-radius:12px;padding:14px;margin-bottom:14px}}
</style>
</head>
<body>

<div class="tabs">
  <button class="tab active" onclick="showTab('form')">📝 PARTICIPAR</button>
  <button class="tab"        onclick="showTab('rank')">🏆 RANKING</button>
  <button class="tab"        onclick="showTab('admin')">⚙️ ADMIN</button>
</div>

<!-- ════════════════ PARTICIPAR ════════════════ -->
<div id="page-form" class="page active">

  <div id="msg-box" class="msg"></div>

  <div class="titulo">
    <h1>Jogos do Brasil</h1>
    <span class="grupo-badge">GRUPO C</span>
  </div>

  <div class="brasil-banner">
    <div class="flag-side">
      <div class="diamond"><div class="circle">ORDEM E<br>PROGRESSO</div></div>
    </div>
    <div class="brasil-nome">BRASIL</div>
  </div>

  <div class="sec-title">IDENTIFICAÇÃO</div>
  <input id="nome" class="input-field" type="text" placeholder="Digite seu nome completo..."
         oninput="checkNome(this.value)">

  <div id="form-body" style="display:none">

    <div id="aviso-imut" style="background:rgba(255,215,0,0.07);border:1px solid rgba(255,215,0,0.25);border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:clamp(0.78rem,3vw,0.88rem);color:rgba(255,255,255,0.7);">
      ⚠️ <b>Atenção:</b> após confirmar, seu palpite <b>não poderá ser alterado</b>.
    </div>

    <!-- Jogos -->
    <div id="jogo-form-1" class="jogo-card">
      <div class="jogo-titulo">JOGO 1 (13/06)</div>
      <div class="jogo-body">
        <span class="jogo-time home">BRASIL</span>
        <input class="jogo-input" id="j1b" type="number" min="0" max="20" value="0">
        <span class="jogo-x">X</span>
        <input class="jogo-input" id="j1a" type="number" min="0" max="20" value="0">
        <span class="jogo-time away">MARROCOS</span>
      </div>
      <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <div id="jogo-form-2" class="jogo-card">
      <div class="jogo-titulo">JOGO 2 (19/06)</div>
      <div class="jogo-body">
        <span class="jogo-time home">BRASIL</span>
        <input class="jogo-input" id="j2b" type="number" min="0" max="20" value="0">
        <span class="jogo-x">X</span>
        <input class="jogo-input" id="j2a" type="number" min="0" max="20" value="0">
        <span class="jogo-time away">HAITI</span>
      </div>
      <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <div id="jogo-form-3" class="jogo-card">
      <div class="jogo-titulo">JOGO 3 (24/06)</div>
      <div class="jogo-body">
        <span class="jogo-time home">BRASIL</span>
        <input class="jogo-input" id="j3b" type="number" min="0" max="20" value="0">
        <span class="jogo-x">X</span>
        <input class="jogo-input" id="j3a" type="number" min="0" max="20" value="0">
        <span class="jogo-time away">ESCÓCIA</span>
      </div>
      <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>

    <!-- Desc + Pts -->
    <div class="desc-row">
      <div class="card">
        <h4 style="margin-bottom:8px;font-size:clamp(0.88rem,3.5vw,1rem);">DESCRIÇÃO:</h4>
        <p style="font-size:clamp(0.78rem,3vw,0.88rem);line-height:1.5;">Preencha os placares e ordene os times do Grupo C da 1ª à 4ª colocação. Ganha quem acertar os placares e a ordem final!</p>
      </div>
      <div class="card">
        <h4 style="margin-bottom:8px;font-size:clamp(0.88rem,3.5vw,1rem);">🏆 PONTUAÇÃO:</h4>
        <div class="pts-item"><span class="pts-num">50</span><span style="font-size:clamp(0.75rem,2.8vw,0.85rem)"><b>Placar exato</b> de cada jogo</span></div>
        <div class="pts-item"><span class="pts-num">30</span><span style="font-size:clamp(0.75rem,2.8vw,0.85rem)"><b>Colocado individual</b> correto</span></div>
        <div class="pts-item"><span class="pts-num">100</span><span style="font-size:clamp(0.75rem,2.8vw,0.85rem)"><b>Gabaritar</b> a classificação</span></div>
      </div>
    </div>

    <!-- Classificação — fundo roxo escuro para os selects ficarem visíveis -->
    <div style="background:#1e1560;border-radius:14px;padding:clamp(10px,3vw,16px);margin-bottom:14px;border:1px solid rgba(255,255,255,0.15);">
      <h3 style="text-align:center;margin-bottom:14px;font-size:clamp(0.9rem,4vw,1.1rem);color:#fff;font-weight:900;">🏆 CLASSIFICAÇÃO DO GRUPO C</h3>
      <div class="input-label">1º Colocado</div>
      <select id="c1" class="input-field"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="input-label">2º Colocado</div>
      <select id="c2" class="input-field"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="input-label">3º Colocado</div>
      <select id="c3" class="input-field"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
      <div class="input-label">4º Colocado</div>
      <select id="c4" class="input-field"><option value="">-- Selecione --</option><option>BRASIL</option><option>MARROCOS</option><option>HAITI</option><option>ESCÓCIA</option></select>
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
        💵<br><b style="font-size:0.7rem;">VALOR PARA<br>PARTICIPAR:</b><br>
        <span class="money-val">R$ 20,00</span>
        <b style="font-size:0.7rem;">POR PARTICIPANTE</b>
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

    <!-- Botão enviar -->
    <div id="btn-submit-area">
      <button class="btn btn-yellow" onclick="submitPalpite()">ENVIAR PALPITE 🇧🇷</button>
    </div>
    <div id="confirm-box" style="display:none">
      <div style="background:rgba(200,16,46,0.12);border:1px solid rgba(200,16,46,0.4);border-radius:10px;padding:12px;margin-bottom:10px;font-weight:700;color:#ffaaaa;">
        ⚠️ CONFIRME — esta ação é irreversível!
      </div>
      <div class="btn-row">
        <button class="btn btn-green" onclick="confirmSubmit()">✅ SIM, ENVIAR</button>
        <button class="btn btn-gray"  onclick="cancelConfirm()">✏️ EDITAR</button>
      </div>
    </div>
  </div>

  <!-- Palpite já salvo -->
  <div id="saved-view" style="display:none">
    <div style="background:rgba(0,156,59,0.15);border:1px solid #009c3b;border-radius:10px;padding:12px 16px;margin-bottom:16px;">
      <div id="saved-msg" style="color:#7fffb0;font-weight:700;font-size:clamp(0.9rem,3.5vw,1rem);"></div>
      <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-top:4px;">Os palpites são definitivos e não podem ser alterados.</div>
    </div>
    <div id="saved-jogos"></div>
  </div>
</div>

<!-- ════════════════ RANKING ════════════════ -->
<div id="page-rank" class="page">
  <div class="sec-title" style="margin-top:4px">PLACARES</div>
  <div class="rank-status-grid" id="status-grid"></div>
  <div class="sec-title">CLASSIFICAÇÃO GERAL</div>
  <div id="ranking-list"></div>
  <div id="classif-final-area"></div>
</div>

<!-- ════════════════ ADMIN ════════════════ -->
<div id="page-admin" class="page">
  <div style="background:rgba(200,16,46,0.08);border:1px solid rgba(200,16,46,0.25);border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:0.88rem;color:rgba(255,255,255,0.7);">
    ⚙️ Área exclusiva do organizador
  </div>
  <div class="input-label">Senha do administrador</div>
  <div style="display:flex;gap:10px;margin-bottom:6px;">
    <input id="admin-pwd" class="input-field" type="password" placeholder="••••••••" style="margin-bottom:0;flex:1" onkeydown="if(event.key==='Enter')checkAdminPwd()">
    <button class="btn btn-yellow" style="width:auto;padding:10px 20px;flex-shrink:0" onclick="checkAdminPwd()">ENTRAR</button>
  </div>
  <div id="admin-pwd-msg" style="display:none;color:#ffaaaa;font-size:0.85rem;margin-bottom:10px;font-weight:700;"></div>

  <!-- Conteúdo admin — oculto até senha correta -->
  <div id="admin-content" style="display:none">
    <div style="background:rgba(0,156,59,0.12);border:1px solid #009c3b;border-radius:10px;padding:10px 14px;margin-bottom:16px;color:#7fffb0;font-size:0.88rem;font-weight:700;">
      ✅ Acesso liberado
    </div>
    <div class="sec-title">PLACARES REAIS</div>
    <div id="admin-placares"></div>
    <button class="btn btn-green" onclick="adminSavePlacar()" style="margin-bottom:20px">💾 SALVAR PLACARES</button>

    <div class="sec-title">CLASSIFICAÇÃO FINAL</div>
    <div id="admin-classif"></div>
    <button class="btn btn-green" onclick="adminSaveClassif()">💾 SALVAR CLASSIFICAÇÃO</button>
  </div>
</div>

<script>
const DATA = {JS_DATA};

// ── Tabs ──────────────────────────────────────────────────
function showTab(id) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  event.target.classList.add('active');
}}

// ── Mensagem ──────────────────────────────────────────────
function showMsg(txt, ok) {{
  const el = document.getElementById('msg-box');
  el.textContent = txt;
  el.className = 'msg show ' + (ok ? 'ok' : 'err');
  setTimeout(() => el.classList.remove('show'), 6000);
}}

// ── Verifica nome ─────────────────────────────────────────
function checkNome(val) {{
  const nome = val.trim();
  document.getElementById('nome-display').textContent = nome || '—';

  if (!nome) {{
    document.getElementById('form-body').style.display  = 'none';
    document.getElementById('saved-view').style.display = 'none';
    return;
  }}

  const entry = DATA.ranking.find(r => r.nome.toLowerCase() === nome.toLowerCase());
  if (entry) {{
    document.getElementById('form-body').style.display  = 'none';
    document.getElementById('saved-view').style.display = 'block';
    document.getElementById('saved-msg').innerHTML = '✅ Palpite de <b>' + entry.nome + '</b> já registrado!';
    renderSavedJogos(entry);
  }} else {{
    document.getElementById('form-body').style.display  = 'block';
    document.getElementById('saved-view').style.display = 'none';
  }}
}}

function renderSavedJogos(entry) {{
  const advs  = ['MARROCOS','HAITI','ESCÓCIA'];
  const datas = ['13/06','19/06','24/06'];
  let html = '';
  entry.jogos.forEach((j,i) => {{
    const gb = j.palpite.length ? j.palpite[0] : '?';
    const ga = j.palpite.length ? j.palpite[1] : '?';
    html += `
    <div class="jogo-card">
      <div class="jogo-titulo">JOGO ${{i+1}} (${{datas[i]}})</div>
      <div class="jogo-body">
        <span class="jogo-time home">BRASIL</span>
        <span class="jogo-score">${{gb}}</span>
        <span class="jogo-x">X</span>
        <span class="jogo-score">${{ga}}</span>
        <span class="jogo-time away">${{advs[i]}}</span>
      </div>
      <div class="jogo-rodape">⭐ CRAVE O RESULTADO EXATO: <span class="red">50 PONTOS</span></div>
    </div>`;
  }});
  document.getElementById('saved-jogos').innerHTML = html;
}}

// ── Data de hoje ──────────────────────────────────────────
document.getElementById('data-display').textContent = new Date().toLocaleDateString('pt-BR');

// ── Submit ────────────────────────────────────────────────
function submitPalpite() {{
  const nome = document.getElementById('nome').value.trim();
  const c1 = document.getElementById('c1').value;
  const c2 = document.getElementById('c2').value;
  const c3 = document.getElementById('c3').value;
  const c4 = document.getElementById('c4').value;
  if (!nome) {{ showMsg('Informe seu nome!', false); return; }}
  if (!c1||!c2||!c3||!c4) {{ showMsg('Selecione os 4 colocados!', false); return; }}
  if (new Set([c1,c2,c3,c4]).size !== 4) {{ showMsg('Selecione times diferentes!', false); return; }}
  document.getElementById('btn-submit-area').style.display = 'none';
  document.getElementById('confirm-box').style.display = 'block';
}}

function cancelConfirm() {{
  document.getElementById('btn-submit-area').style.display = 'block';
  document.getElementById('confirm-box').style.display = 'none';
}}

function confirmSubmit() {{
  const p = new URLSearchParams({{
    action: 'submit',
    nome:   document.getElementById('nome').value.trim(),
    j1b:    document.getElementById('j1b').value,
    j1a:    document.getElementById('j1a').value,
    j2b:    document.getElementById('j2b').value,
    j2a:    document.getElementById('j2a').value,
    j3b:    document.getElementById('j3b').value,
    j3a:    document.getElementById('j3a').value,
    c1:     document.getElementById('c1').value,
    c2:     document.getElementById('c2').value,
    c3:     document.getElementById('c3').value,
    c4:     document.getElementById('c4').value,
  }});
  const _base = window.parent.location.href.split('?')[0]; window.parent.location.href = _base + '?' + p.toString();
}}

// ── Ranking ───────────────────────────────────────────────
function buildRanking() {{
  // Status dos jogos
  document.getElementById('status-grid').innerHTML = DATA.jogos.map(j => {{
    const enc = j.encerrado;
    return `<div class="status-card ${{enc?'enc':''}}">
      <div class="status-jogo">Jogo ${{j.key.slice(-1)}} · ${{j.data}}</div>
      ${{enc
        ? `<div class="status-placar">Brasil ${{j.brasil}} × ${{j.adversario}}</div><div class="status-tag" style="color:#7fffb0">✅ Encerrado</div>`
        : `<div class="status-placar" style="font-size:0.9rem;color:rgba(255,255,255,.3)">—</div><div class="status-tag" style="color:rgba(255,255,255,.3)">⏳ Pendente</div>`
      }}
    </div>`;
  }}).join('');

  const medals = ['🥇','🥈','🥉'];
  const rcs    = ['r1','r2','r3'];
  const rl     = document.getElementById('ranking-list');

  if (!DATA.ranking.length) {{
    rl.innerHTML = '<div style="text-align:center;padding:40px;color:rgba(255,255,255,.3);font-weight:700;">NENHUM PALPITE AINDA 🎯</div>';
    return;
  }}

  rl.innerHTML = `<div style="text-align:right;color:rgba(255,255,255,.35);font-size:0.78rem;margin-bottom:8px;">${{DATA.ranking.length}} participante(s)</div>`;

  DATA.ranking.forEach(e => {{
    const idx = e.pos - 1;
    const med = medals[idx] || (e.pos + '°');
    const cls = rcs[idx]    || '';

    // Card clicável
    const card = document.createElement('div');
    card.className = 'rank-card ' + cls;
    card.innerHTML = `
      <div class="rank-pos">${{med}}</div>
      <div class="rank-nome">${{e.nome.toUpperCase()}}</div>
      <div>
        <div class="rank-pts-val">${{e.total}}</div>
        <div class="rank-pts-lbl">PONTOS</div>
      </div>`;
    card.onclick = () => toggleDetail(e.pos);
    rl.appendChild(card);

    // Painel de detalhes
    const advs  = ['Marrocos','Haiti','Escócia'];
    const panel = document.createElement('div');
    panel.id        = 'detail-' + e.pos;
    panel.className = 'detail-panel';

    let dhtml = '';
    e.jogos.forEach((j, ji) => {{
      const adv = advs[ji];
      if (j.status === 'exato') {{
        dhtml += `<div class="detail-line">Brasil ${{j.palpite[0]}}×${{j.palpite[1]}} ${{adv}} <span class="ok-tag">✅ +50pts</span></div>`;
      }} else if (j.status === 'errado') {{
        dhtml += `<div class="detail-line">Brasil ${{j.palpite[0]}}×${{j.palpite[1]}} ${{adv}} <span class="err-tag">❌ (real: ${{j.real[0]}}×${{j.real[1]}})</span></div>`;
      }} else {{
        const pal = j.palpite.length ? j.palpite[0]+'×'+j.palpite[1] : '—';
        dhtml += `<div class="detail-line">Brasil ${{pal}} ${{adv}} <span class="pend-tag">⏳</span></div>`;
      }}
    }});

    if (e.classif_palpite.length) {{
      dhtml += '<div class="detail-line" style="margin-top:6px;font-weight:700;border-bottom:none;">Classificação palpitada:</div>';
      const posIcons = ['🥇','🥈','🥉','4°'];
      e.classif_palpite.forEach((t, ci) => {{
        const st  = e.classif_status[String(ci+1)];
        const tag = st === 'acerto'
          ? '<span class="ok-tag">✅ +30pts</span>'
          : st === 'errado'
            ? `<span class="err-tag">❌ (era ${{e.classif_real[ci]||'?'}})</span>`
            : '<span class="pend-tag">⏳</span>';
        dhtml += `<div class="detail-line">${{posIcons[ci]}} ${{t}} ${{tag}}</div>`;
      }});
      if (e.classif_status['gabarito'] === true) {{
        dhtml += '<div class="detail-line"><span class="ok-tag">🏆 GABARITO COMPLETO! +100pts bônus</span></div>';
      }}
    }}
    panel.innerHTML = dhtml;
    rl.appendChild(panel);
  }});

  // Classificação final publicada
  const cfa = document.getElementById('classif-final-area');
  if (DATA.classif_real.some(t => t)) {{
    const posIcons = ['🥇','🥈','🥉','4°'];
    cfa.innerHTML = '<div class="sec-title">CLASSIFICAÇÃO FINAL · GRUPO C</div>'
      + DATA.classif_real.map((t,i) =>
          `<div class="cf-row"><span class="cf-pos">${{posIcons[i]}}</span><span class="cf-nome">${{t}}</span></div>`
        ).join('');
  }}
}}

function toggleDetail(pos) {{
  const p = document.getElementById('detail-' + pos);
  if (p) p.classList.toggle('open');
}}

// ── Admin — senha client-side + submit server-side ────────
const ADMIN_PWD = 'brasil2026';

function checkAdminPwd() {{
  const pwd = document.getElementById('admin-pwd').value;
  const msg = document.getElementById('admin-pwd-msg');
  if (pwd === ADMIN_PWD) {{
    document.getElementById('admin-content').style.display = 'block';
    msg.style.display = 'none';
    buildAdmin();
  }} else {{
    msg.textContent      = '❌ Senha incorreta!';
    msg.style.display    = 'block';
    document.getElementById('admin-content').style.display = 'none';
  }}
}}

function buildAdmin() {{
  const advs = ['MARROCOS','HAITI','ESCÓCIA'];
  const keys = ['jogo1','jogo2','jogo3'];
  let ph = '';
  DATA.jogos.forEach((j, i) => {{
    const vb = j.brasil    ?? 0;
    const va = j.adversario ?? 0;
    ph += `
    <div class="admin-section">
      <b style="font-size:0.9rem;">Jogo ${{i+1}} (${{j.data}}) — Brasil × ${{advs[i]}}</b>
      ${{j.encerrado ? `<div style="color:#7fffb0;font-size:0.82rem;margin:6px 0;">✅ Salvo: Brasil ${{vb}} × ${{va}}</div>` : ''}}
      <div class="admin-grid">
        <span style="font-weight:700;font-size:0.88rem;">Brasil</span>
        <input class="admin-input" id="r${{i+1}}b" type="number" min="0" max="20" value="${{vb}}">
        <span style="text-align:center;font-weight:900;">×</span>
        <input class="admin-input" id="r${{i+1}}a" type="number" min="0" max="20" value="${{va}}">
      </div>
      <label style="font-size:0.82rem;color:rgba(255,255,255,.7);display:flex;align-items:center;gap:8px;margin-top:8px;cursor:pointer;">
        <input type="checkbox" id="enc_${{keys[i]}}" ${{j.encerrado?'checked':''}}>
        Marcar como encerrado
      </label>
    </div>`;
  }});
  document.getElementById('admin-placares').innerHTML = ph;

  const times = ['BRASIL','MARROCOS','HAITI','ESCÓCIA'];
  const cr    = DATA.classif_real;
  let ch = '';
  for (let i = 1; i <= 4; i++) {{
    const cur = (cr[i-1] || '').toUpperCase();
    ch += `<div class="input-label">${{i}}º Colocado</div>
    <select id="rc${{i}}" class="input-field">
      <option value="">-- Selecione --</option>
      ${{times.map(t => `<option value="${{t}}" ${{t===cur?'selected':''}}>${{t}}</option>`).join('')}}
    </select>`;
  }}
  document.getElementById('admin-classif').innerHTML = ch;
}}

function adminSavePlacar() {{
  const pwd = document.getElementById('admin-pwd').value;
  const p   = new URLSearchParams({{action:'admin_save_placar', pwd}});
  ['jogo1','jogo2','jogo3'].forEach((k, i) => {{
    p.set('r'+(i+1)+'b', document.getElementById('r'+(i+1)+'b').value || 0);
    p.set('r'+(i+1)+'a', document.getElementById('r'+(i+1)+'a').value || 0);
    if (document.getElementById('enc_'+k).checked) p.set('enc_'+k, '1');
  }});
  const _base = window.parent.location.href.split('?')[0]; window.parent.location.href = _base + '?' + p.toString();
}}

function adminSaveClassif() {{
  const pwd = document.getElementById('admin-pwd').value;
  const p   = new URLSearchParams({{action:'admin_save_classif', pwd}});
  for (let i = 1; i <= 4; i++) {{
    p.set('rc'+i, document.getElementById('rc'+i).value);
  }}
  const _base = window.parent.location.href.split('?')[0]; window.parent.location.href = _base + '?' + p.toString();
}}

// ── Init ──────────────────────────────────────────────────
buildRanking();
// Admin só é construído quando senha for validada — NÃO chamar buildAdmin() aqui

if (DATA.msg) showMsg(DATA.msg, DATA.msg_ok);
</script>
</body>
</html>"""

st.components.v1.html(HTML, height=3000, scrolling=True)
