import streamlit as st
from utils.scoring import calculate_scores
from utils.database import get_placares_reais, get_classificacao_real

MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}
RANK_CLASS = {1: "rank-1", 2: "rank-2", 3: "rank-3"}

JOGOS_INFO = [
    ('jogo1', 'Jogo 1', '13/06', 'Marrocos'),
    ('jogo2', 'Jogo 2', '19/06', 'Haiti'),
    ('jogo3', 'Jogo 3', '24/06', 'Escócia'),
]


def render():
    placares_reais     = get_placares_reais()
    classificacao_real = get_classificacao_real()

    # ── Status dos jogos ───────────────────────────────────
    st.markdown('<div class="section-title">PLACARES</div>', unsafe_allow_html=True)
    st.markdown('<div class="jogo-status-grid">', unsafe_allow_html=True)

    for jkey, jlabel, jdata, jadv in JOGOS_INFO:
        real = placares_reais.get(jkey, {})
        if real.get('encerrado'):
            st.markdown(f"""
            <div class="jogo-status-card encerrado">
                <div class="jogo-status-title">{jlabel} · {jdata}</div>
                <div class="jogo-status-score">{real['brasil']} × {real['adversario']}</div>
                <div class="jogo-status-tag" style="color:#7fffb0;">✅ Encerrado</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="jogo-status-card">
                <div class="jogo-status-title">{jlabel} · {jdata}</div>
                <div style="font-family:'Barlow Condensed',sans-serif; font-size:0.9rem;
                            color:rgba(255,255,255,0.3);">Aguardando</div>
                <div class="jogo-status-tag" style="color:rgba(255,255,255,0.3);">⏳ Pendente</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabela de ranking ──────────────────────────────────
    st.markdown('<div class="section-title">CLASSIFICAÇÃO GERAL</div>', unsafe_allow_html=True)

    scores = calculate_scores()

    if not scores:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:rgba(255,255,255,0.35);
                    font-family:'Barlow Condensed',sans-serif; font-size:1rem; letter-spacing:1px;">
            NENHUM PALPITE REGISTRADO AINDA<br>
            <span style="font-size:0.85rem;">Seja o primeiro a participar! 🎯</span>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(
        f"<div style='text-align:right; color:rgba(255,255,255,0.35); font-size:0.78rem; "
        f"font-family:Barlow,sans-serif; margin-bottom:8px;'>"
        f"{len(scores)} participante(s)</div>",
        unsafe_allow_html=True)

    for i, entry in enumerate(scores, 1):
        rc    = RANK_CLASS.get(i, "")
        medal = MEDAL.get(i, f"{i}°")

        st.markdown(f"""
        <div class="rank-card {rc}">
            <div class="rank-pos">{medal}</div>
            <div class="rank-name">{entry['nome'].upper()}</div>
            <div style="text-align:right;">
                <div class="rank-pts">{entry['total']}</div>
                <div class="rank-pts-label">PONTOS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Detalhes — {entry['nome']}", expanded=False):
            det = entry['detail']
            adv_names = {'jogo1': 'Marrocos', 'jogo2': 'Haiti', 'jogo3': 'Escócia'}

            for jkey, jadv in adv_names.items():
                d = det.get(jkey, {})
                status = d.get('status')
                if status == 'exato':
                    p = d['palpite']
                    st.markdown(f"Brasil {p[0]}×{p[1]} {jadv} ✅ **+50 pts**")
                elif status == 'errado':
                    p, r = d['palpite'], d['real']
                    st.markdown(f"Brasil {p[0]}×{p[1]} {jadv} ❌ (real: {r[0]}×{r[1]})")
                elif status == 'pendente':
                    p = d.get('palpite', ('—','—'))
                    st.markdown(f"Brasil {p[0] if p else '?'}×{p[1] if p else '?'} {jadv} ⏳")
                else:
                    st.markdown(f"{jadv} — sem palpite")

            cl = det.get('classificacao', {})
            pal_cl = cl.get('palpite', [])
            if pal_cl:
                st.markdown("**Classificação:**")
                emojis = ["🥇","🥈","🥉","4️⃣"]
                st_cl  = cl.get('status', {})
                for j, time in enumerate(pal_cl):
                    acerto = st_cl.get(j+1)
                    if acerto == 'acerto':
                        st.markdown(f"  {emojis[j]} {time} ✅ +30 pts")
                    elif acerto == 'errado':
                        real_t = cl.get('real', ['?']*4)[j]
                        st.markdown(f"  {emojis[j]} {time} ❌ (era {real_t})")
                    else:
                        st.markdown(f"  {emojis[j]} {time} ⏳")
                if st_cl.get('gabarito'):
                    st.markdown("🏆 **GABARITO COMPLETO! +100 pts bônus**")

    # ── Classificação real (se publicada) ─────────────────
    if classificacao_real:
        st.markdown('<div class="section-title">CLASSIFICAÇÃO FINAL · GRUPO C</div>', unsafe_allow_html=True)
        for pos in range(1, 5):
            time  = classificacao_real.get(pos, "—")
            medal = MEDAL.get(pos, f"{pos}°")
            st.markdown(f"""
            <div class="saved-classif-row">
                <span style="font-size:1.1rem;">{medal}</span>
                <span style="font-family:'Barlow Condensed',sans-serif; color:#fff;
                             font-size:1rem; font-weight:700;">{time}</span>
            </div>
            """, unsafe_allow_html=True)
