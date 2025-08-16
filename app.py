
# -*- coding: utf-8 -*-
# Gerador de Certificados - Previews dinâmicos + sliders e compatibilidade Streamlit

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Gerador de Certificados", page_icon="🎓", layout="wide")

# --------------------------
# Helpers
# --------------------------
def load_font(font_file, size):
    # Tenta fonte enviada; se não houver, usa Bentosa.ttf incluída no projeto; por fim, fallback
    try:
        if font_file is not None:
            return ImageFont.truetype(font_file, size)
        return ImageFont.truetype("Bentosa.ttf", size)
    except Exception:
        return ImageFont.load_default()

def draw_name_on_image(img: Image.Image, name: str, x: int, y: int, font, color, align: str):
    im = img.copy()
    draw = ImageDraw.Draw(im)
    anchor = {"Esquerda":"la", "Centro":"mm", "Direita":"ra"}.get(align, "mm")
    draw.text((x, y), name, fill=color, font=font, anchor=anchor)
    return im

def fit_on_a4(img: Image.Image):
    w, h = A4
    img_w, img_h = img.size
    ratio = min(w / img_w, h / img_h)
    return (img_w * ratio, img_h * ratio, ratio)

def pil_to_pdf_page(img: Image.Image) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    new_w, new_h, _ = fit_on_a4(img)
    x = (w - new_w) / 2
    y = (h - new_h) / 2
    c.drawImage(ImageReader(img), x, y, width=new_w, height=new_h)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

def read_names(file):
    if file is None: return []
    if file.name.lower().endswith(".txt"):
        content = file.read()
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = content.decode(enc)
                break
            except Exception:
                continue
        names = [l.strip() for l in text.splitlines() if l.strip()]
    else:
        df = pd.read_csv(file)
        names = df.iloc[:,0].dropna().astype(str).tolist()
    return names

def zip_bytes(files):
    zbuf = BytesIO()
    with zipfile.ZipFile(zbuf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname, fbytes in files:
            z.writestr(fname, fbytes)
    zbuf.seek(0)
    return zbuf

def css_inject(css):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --------------------------
# CSS
# --------------------------
CSS = '''
:root {
  --accent: #ff9f0a;
}
h1,h2{ color: var(--accent) !important; font-weight:800 }
.preview-card{ background:#151515; border:1px solid #2a2a2a; border-radius:20px; padding:10px; }
.caption{ color:#9a9a9a; font-size:12px; }
.center-h { display:flex; align-items:center; justify-content:center; }
'''
css_inject(CSS)

# --------------------------
# Sidebar - Ajustes Globais
# --------------------------
with st.sidebar:
    st.markdown("## Ajustes Globais")
    with st.container(border=True):
        st.markdown("**Posição & Escala**")
        col_ps1, col_ps2 = st.columns(2)
        with col_ps1:
            g_x = st.slider("Posição X", min_value=0, max_value=5000, value=1000, step=1)
            g_align = st.radio("Alinhamento", ["Esquerda","Centro","Direita"], horizontal=True)
        with col_ps2:
            g_y = st.slider("Posição Y", min_value=0, max_value=3000, value=600, step=1)
            g_scale = st.slider("Escala da fonte", 0.5, 3.0, 1.0, 0.01)

    st.markdown("\n")
    with st.container(border=True):
        st.markdown("**Caracteres / Estilo da Fonte**")
        font_upload = st.file_uploader("Fonte (TTF) — padrão: Bentosa", type=["ttf"], key="font_up")
        base_font_size = st.number_input("Tamanho base (pt)", value=48, step=1)
        font_color = st.color_picker("Cor", "#000000")  # PRETO padrão

    st.markdown("\n")
    st.markdown("## Exportar Arquivos")
    with st.container(border=True):
        out_fmt = st.selectbox("Formato de saída:", ["PDF (individual)", "PNG (individual)", "JPEG (individual)"])
        out_name_tpl = st.text_input("Padrão do nome do arquivo:", "{name}")
        st.caption("Use {name} para o nome da pessoa. Ex: Certificado_{name}")

# --------------------------
# Header e uploads
# --------------------------
st.markdown("<div class='center-h'><h1>Gerador de Certificados</h1></div>", unsafe_allow_html=True)

c1,c2,c3 = st.columns([1,1,1], gap="large")
with c1:
    st.markdown("<div class='label'>Certificado - Frente</div>", unsafe_allow_html=True)
    up_front = st.file_uploader("", type=["png","jpg","jpeg"], key="front")
with c2:
    st.markdown("<div class='label'>Certificado - Verso (opcional)</div>", unsafe_allow_html=True)
    up_back = st.file_uploader("", type=["png","jpg","jpeg"], key="back")
with c3:
    st.markdown("<div class='label'>Lista de nomes</div>", unsafe_allow_html=True)
    up_names = st.file_uploader("", type=["txt","csv"], key="names")

st.markdown("<div class='center-h'><h2>Previews</h2></div>", unsafe_allow_html=True)

# --------------------------
# Previews dinâmicos (um por nome)
# --------------------------
names = read_names(up_names)
if not names:
    names = ["nome da pessoa"]

# Inicializa estados por nome
for idx, nm in enumerate(names):
    if f"dx_{idx}" not in st.session_state: st.session_state[f"dx_{idx}"] = 0
    if f"dy_{idx}" not in st.session_state: st.session_state[f"dy_{idx}"] = 0
    if f"size_{idx}" not in st.session_state: st.session_state[f"size_{idx}"] = base_font_size

def render_preview(idx, nm, front_bytes):
    st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
    cA,cB,cC = st.columns(3)
    with cA:
        st.session_state[f"dx_{idx}"] = st.slider("dx", min_value=-2000, max_value=2000, value=st.session_state[f"dx_{idx}"], step=1, key=f"ctrl_dx_{idx}")
    with cB:
        st.session_state[f"dy_{idx}"] = st.slider("dy", min_value=-2000, max_value=2000, value=st.session_state[f"dy_{idx}"], step=1, key=f"ctrl_dy_{idx}")
    with cC:
        st.session_state[f"size_{idx}"] = st.slider("tamanho", min_value=6, max_value=300, value=st.session_state[f"size_{idx}"], step=1, key=f"ctrl_size_{idx}")

    if front_bytes is not None:
        base = Image.open(front_bytes).convert("RGB")
    else:
        base = Image.new("RGB", (1280, 720), "#111111")

    font = load_font(font_upload, int(st.session_state[f"size_{idx}"] * g_scale))
    out = draw_name_on_image(
        base, nm, int(g_x + st.session_state[f"dx_{idx}"]), int(g_y + st.session_state[f"dy_{idx}"]),
        font, font_color, g_align
    )
    st.image(out, use_container_width=True, caption=nm)  # atualizado para use_container_width
    st.markdown("</div>", unsafe_allow_html=True)

# Grid em colunas de 3 para exibir todos os previews
cols = st.columns(3, gap="large")
for i, nm in enumerate(names):
    with cols[i % 3]:
        render_preview(i, nm, up_front)

st.divider()

# --------------------------
# Geração de arquivos
# --------------------------
gen = st.button("Gerar e baixar .zip", type="primary", use_container_width=True, disabled=up_front is None or up_names is None)

if gen:
    fmt = out_fmt.split(" ")[0]  # PDF/PNG/JPEG
    front_img = Image.open(up_front).convert("RGB")
    back_img = Image.open(up_back).convert("RGB") if up_back is not None else None
    files = []

    for i, nm in enumerate(read_names(up_names)):
        dx = st.session_state.get(f"dx_{i}", 0)
        dy = st.session_state.get(f"dy_{i}", 0)
        sz = st.session_state.get(f"size_{i}", base_font_size)
        font = load_font(font_upload, int(sz * g_scale))

        out_img = draw_name_on_image(front_img, nm, int(g_x + dx), int(g_y + dy), font, font_color, g_align)
        fname_base = out_name_tpl.format(name=nm)

        if fmt == "PNG":
            b = BytesIO(); out_img.save(b, "PNG", optimize=True); b.seek(0)
            files.append((f"{fname_base}.png", b.read()))
            if back_img is not None:
                b2 = BytesIO(); back_img.save(b2, "PNG", optimize=True); b2.seek(0)
                files.append((f"{fname_base}_verso.png", b2.read()))
        elif fmt == "JPEG":
            b = BytesIO(); out_img.save(b, "JPEG", quality=95, subsampling=0); b.seek(0)
            files.append((f"{fname_base}.jpg", b.read()))
            if back_img is not None:
                b2 = BytesIO(); back_img.save(b2, "JPEG", quality=95, subsampling=0); b2.seek(0)
                files.append((f"{fname_base}_verso.jpg", b2.read()))
        else:
            files.append((f"{fname_base}.pdf", pil_to_pdf_page(out_img)))
            if back_img is not None:
                files.append((f"{fname_base}_verso.pdf", pil_to_pdf_page(back_img)))

    z = zip_bytes(files)
    st.download_button("📦 Baixar ZIP", data=z, file_name="certificados.zip", mime="application/zip", use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='center-h'><div style='max-width:900px;text-align:center' class='caption'>
<b>Toda grande invenção é, em essência, a resposta engenhosa a um problema de magnitude equivalente, nascendo da urgência e da complexidade que instigam o intelecto humano a transcender seus próprios limites.</b><br/>
by: Coelho<br/><br/>
<b>Deus seja louvado.</b>
</div></div>""", unsafe_allow_html=True)
