# -*- coding: utf-8 -*-
"""
Gerador de Certificados — V3 (Streamlit)
Recursos:
- Upload frente/verso: PNG/JPG + SVG/EPS/PDF (preview: PNG/JPG direto; SVG via cairosvg; EPS/PDF fallback branco)
- Previews em 2 colunas
- Modo de âncora: Manual (X/Y) ou Canvas (clique/arrastar)
- Ajustes por nome: dx, dy e TAMANHO DE FONTE individual
- Ajustes globais gdx/gdy e tamanho base
- Exportação:
    * Raster: PNG/JPEG (qualidade: baixa/média/alta)
    * Vetores: PDF (texto vetorial), SVG (texto vetorial), EPS (texto vetorial)
- Tema: claro, escuro e automático (CSS)
- Rodapé com frase do Coelho
"""

import streamlit as st
from utils import (
    carregar_base_preview, ler_nomes, desenhar_preview_nome,
    exportar_zip,
    canvas_disponivel
)

# ================= TEMA ==================
tema = st.sidebar.radio("🎨 Tema", ["Automático", "Claro", "Escuro"], index=0, horizontal=True)

def _inject_theme(selected):
    if selected == "Automático":
        st.markdown("""
        <style>
        @media (prefers-color-scheme: dark) {
            :root { color-scheme: dark; }
            .stApp { background: #0e1117; color: #fafafa; }
        }
        </style>""", unsafe_allow_html=True)
    elif selected == "Escuro":
        st.markdown("""
        <style>
        :root { color-scheme: dark; }
        .stApp { background: #0e1117; color: #fafafa; }
        </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        :root { color-scheme: light; }
        .stApp { background: #ffffff; color: #111111; }
        </style>""", unsafe_allow_html=True)

_inject_theme(tema)

# ================= UPLOADS ==================
st.title("🏆 Gerador de Certificados")

st.header("📑 Certificados")
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    frente_file = st.file_uploader("📄 Frente", type=["png", "jpg", "jpeg", "svg", "eps", "pdf"])
with col2:
    verso_file = st.file_uploader("🪙 Verso (opcional)", type=["png", "jpg", "jpeg", "svg", "eps", "pdf"])
with col3:
    nomes_file = st.file_uploader("📜 Lista de nomes (.txt ou .csv)", type=["txt", "csv"])

# ================= AJUSTES GLOBAIS ==================
st.sidebar.header("⚙️ Ajustes Globais")
gdx = st.sidebar.slider("Deslocamento X global (gdx)", -1500, 1500, 0)
gdy = st.sidebar.slider("Deslocamento Y global (gdy)", -1500, 1500, 0)
tamanho_global = st.sidebar.slider("Tamanho base da fonte", 10, 300, 64)
cor_texto = st.sidebar.color_picker("Cor do texto", "#FFB900")

st.sidebar.header("📐 Qualidade (PNG/JPEG)")
qualidades = {
    "Baixa": (1280, 72, 50),
    "Média": (1920, 150, 85),
    "Alta": (3840, 300, 95),
}
qualidade_nome = st.sidebar.selectbox("Qualidade", list(qualidades.keys()), index=1)
px_largura, dpi_export, jpg_q = qualidades[qualidade_nome]

st.sidebar.header("💾 Exportação")
formato_saida = st.sidebar.selectbox(
    "Formato",
    ["PNG", "JPEG", "PDF (vetor)", "SVG (vetor)", "EPS (vetor)"],
    index=2
)
padrao_nome = st.sidebar.text_input("Padrão do nome do arquivo", "{name}")

# ================= PREVIEW ==================
if frente_file and nomes_file:
    base_img, base_meta = carregar_base_preview(frente_file)
    nomes = ler_nomes(nomes_file)

    # Seletor de modo âncora
    st.markdown("### 📍 Modo de âncora")
    modos = ["Manual (X/Y)"]
    if canvas_disponivel():
        modos.append("Canvas (clique)")
    modo = st.radio("Escolha como definir a âncora", modos, horizontal=True)

    if base_img is not None:
        W, H = base_img.size
    else:
        W, H = 1600, 1000

    if modo.startswith("Canvas"):
        st.caption("Clique no canvas para definir a âncora global (centro do nome).")
        try:
            from streamlit_drawable_canvas import st_canvas
            canvas = st_canvas(
                fill_color="rgba(0,0,0,0)",
                stroke_width=0,
                background_image=base_img if base_img is not None else None,
                update_streamlit=True,
                height=min(H, 700),
                width=min(W, 1000),
                drawing_mode="point",
                key="canvas_global_v3",
            )
            if canvas.json_data is not None and len(canvas.json_data.get("objects", [])) > 0:
                last = canvas.json_data["objects"][-1]
                if canvas.image_data is not None:
                    scale_x = W / canvas.image_data.shape[1]
                    scale_y = H / canvas.image_data.shape[0]
                    x_anchor = int(last["left"] * scale_x)
                    y_anchor = int(last["top"] * scale_y)
                else:
                    x_anchor, y_anchor = W//2, H//2
            else:
                x_anchor, y_anchor = W//2, H//2
        except Exception as e:
            st.warning(f"Canvas indisponível ({e}). Use o modo Manual.")
            x_anchor, y_anchor = W//2, H//2
    else:
        # Manual
        if base_img is not None:
            st.image(base_img, use_container_width=True)
        else:
            st.info("Pré-visualização não disponível para este formato. Use os valores numéricos abaixo.")
        x_anchor = st.number_input("Âncora X", 0, W, W//2)
        y_anchor = st.number_input("Âncora Y", 0, H, H//2)

    # Estado por-nome
    if "ajustes" not in st.session_state:
        st.session_state.ajustes = {}
    for n in nomes:
        if n not in st.session_state.ajustes:
            st.session_state.ajustes[n] = {"dx": 0, "dy": 0, "tamanho": int(tamanho_global)}

    # Previews em 2 colunas
    st.markdown("### 🔍 Previews individuais (2 por linha)")
    cols = st.columns(2)
    previews = []
    for idx, n in enumerate(nomes):
        a = st.session_state.ajustes[n]
        with cols[idx % 2]:
            st.markdown(f"**{n}**")
            # Sliders individuais
            a["dx"] = st.slider(f"dx — {n}", -1500, 1500, a["dx"], key=f"dx_{idx}")
            a["dy"] = st.slider(f"dy — {n}", -1500, 1500, a["dy"], key=f"dy_{idx}")
            a["tamanho"] = st.slider(f"Tamanho fonte — {n}", 10, 300, a["tamanho"], key=f"fs_{idx}")
            # Render preview real quando possível
            img_bytes = desenhar_preview_nome(
                base_img, (W, H), n, x_anchor, y_anchor, gdx, gdy, a["dx"], a["dy"], a["tamanho"], cor_texto
            )
            st.image(img_bytes, use_container_width=True)
            previews.append((n, img_bytes))

    # ============== EXPORTAR ==============
    st.markdown("---")
    if st.button("📦 Exportar (ZIP)"):
        zip_bytes = exportar_zip(
            frente_file, verso_file, nomes, st.session_state.ajustes,
            base_meta, (W, H), x_anchor, y_anchor, gdx, gdy, cor_texto,
            formato_saida, px_largura, dpi_export, jpg_q, padrao_nome
        )
        st.download_button("⬇️ Baixar ZIP", data=zip_bytes, file_name="certificados.zip", mime="application/zip")

# Rodapé com a frase pedida
st.markdown(
    """
    <div style='text-align:center; margin-top:40px; font-style:italic;'>
    "Toda grande invenção é, em essência, a resposta engenhosa a um problema de magnitude equivalente, nascendo da urgência e da complexidade que instigam o intelecto humano a transcender seus próprios limites. by: Coelho"
    </div>
    """,
    unsafe_allow_html=True
)
