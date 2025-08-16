
# -*- coding: utf-8 -*-
# Gerador de Certificados - Layout fiel ao mock enviado
# Streamlit + Pillow + ReportLab (PDF), com previews e ajustes por preview

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import base64

st.set_page_config(page_title="Gerador de Certificados", page_icon="🎓", layout="wide")

# --------------------------
# Helpers
# --------------------------
def load_font(font_file, size):
    try:
        if font_file is not None:
            return ImageFont.truetype(font_file, size)
        # Tenta uma fonte 'Bentosa.ttf' se estiver no diretório do app
        try:
            return ImageFont.truetype("Bentosa.ttf", size)
        except Exception:
            return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def draw_name_on_image(img: Image.Image, name: str, x: int, y: int, font, color, align: str):
    im = img.copy()
    draw = ImageDraw.Draw(im)
    # Define âncora para alinhar conforme layout (esquerda/centro/direita)
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

def to_data_url(css):
    return f"<style>{css}</style>"

# --------------------------
# CSS para copiar o layout
# --------------------------
CSS = '''
:root {
  --bg: #1b1b1b;
  --panel: #202020;
  --panel-2: #0f0f0f;
  --accent: #ff9f0a;
  --text: #e9e9e9;
  --muted:#9a9a9a;
  --radius:22px;
}
html, body, [data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 800px at 30% -10%, #1f1f1f 0%, #111111 60%) !important;
  color: var(--text);
}
h1,h2,h3,h4{ color: var(--accent) !important; font-weight:800 }
.block{ background:#161616; border-radius:var(--radius); padding:18px 20px; border:1px solid #2a2a2a; }
.pill{ background:#0f0f0f; border:1px solid #2a2a2a; border-radius:40px; padding:10px 16px; }
.label{ color:var(--text); font-weight:600; text-align:center; margin-bottom:6px }
.center-h { display:flex; align-items:center; justify-content:center; }
.caption{ color:var(--muted); font-size:12px; }
.orange{ color:var(--accent); }
.small{ font-size:13px }
.preview-card{ background:#151515; border:1px solid #2a2a2a; border-radius:20px; padding:10px; }
.hr{ height:1px; background:#2a2a2a; margin:12px 0 }
footer{ visibility:hidden }
'''
st.markdown(to_data_url(CSS), unsafe_allow_html=True)

# --------------------------
# Sidebar - Ajustes Globais (fiel ao layout)
# --------------------------
with st.sidebar:
    st.markdown("## Ajustes Globais")
    with st.container(border=True):
        st.markdown("**Posição & Escala**", help="Ajustes aplicados inicialmente aos previews; cada preview pode sobrepor.")
        col_ps1, col_ps2 = st.columns(2)
        with col_ps1:
            g_x = st.number_input("Posição X", value=1000, step=5)
            g_align = st.radio("Alinhamento", ["Esquerda","Centro","Direita"], horizontal=True)
        with col_ps2:
            g_y = st.number_input("Posição Y", value=600, step=5)
            g_scale = st.slider("Escala da fonte", 0.5, 3.0, 1.0, 0.05)

    st.markdown("\n")
    with st.container(border=True):
        st.markdown("**Caracteres / Estilo da Fonte**")
        font_upload = st.file_uploader("Fonte (TTF) — padrão: Bentosa", type=["ttf"], key="font_up")
        base_font_size = st.number_input("Tamanho base (pt)", value=48, step=1)
        font_color = st.color_picker("Cor", "#FF9F0A")

    st.markdown("\n")
    st.markdown("## Exportar Arquivos")
    with st.container(border=True):
        out_fmt = st.selectbox("Formato de saída:", ["PDF (individual)", "PNG (individual)", "JPEG (individual)"])
        out_name_tpl = st.text_input("Padrão do nome do arquivo:", "{name}")
        st.caption("Use {name} para o nome da pessoa. Ex: Certificado_{name}")

# --------------------------
# Header central
# --------------------------
st.markdown("""<div class='center-h'><h1>Gerador de Certificados</h1></div>""", unsafe_allow_html=True)

# Linha de uploads (3 colunas)
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
# Previews - 3 cartões, cada um com seus ajustes
# --------------------------
names = read_names(up_names)[:3] if up_names is not None else []
if not names:
    names = ["nome da pessoa"]*3

def preview_card(idx, name, img_front):
    st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
    # Controles de dx/dy/size por preview (em relação aos globais)
    col_a, col_b, col_c = st.columns([1,1,1])
    with col_a:
        dx = st.number_input(f"dx", value=0, step=1, key=f"dx_{idx}")
    with col_b:
        dy = st.number_input(f"dy", value=0, step=1, key=f"dy_{idx}")
    with col_c:
        p_size = st.number_input(f"tamanho", value=base_font_size, step=1, key=f"size_{idx}")

    if img_front is not None:
        base = Image.open(img_front).convert("RGB")
    else:
        # placeholder preto
        base = Image.new("RGB", (1280, 720), "#111111")

    # Aplica fonte
    font = load_font(font_upload, int(p_size * g_scale))

    # Monta imagem de preview
    out = draw_name_on_image(
        base, name, int(g_x + dx), int(g_y + dy),
        font, font_color, g_align
    )

    st.image(out, use_column_width=True, caption=name)
    st.markdown("</div>", unsafe_allow_html=True)
    return (dx, dy, int(p_size))

# Renderiza 3 colunas de preview
pc1, pc2, pc3 = st.columns(3, gap="large")
with pc1: p1 = preview_card(1, names[0], up_front)
with pc2: p2 = preview_card(2, names[1], up_front)
with pc3: p3 = preview_card(3, names[2], up_front)

st.divider()

# --------------------------
# Botão de geração e download
# --------------------------
col_btn = st.columns([1,1,1])[1]
with col_btn:
    gen = st.button("Gerar e baixar .zip", use_container_width=True, type="primary", disabled=up_front is None or up_names is None)

if gen:
    all_names = read_names(up_names)
    files = []
    fmt = out_fmt.split(" ")[0]  # PDF/PNG/JPEG

    # carrega imagens
    front_img = Image.open(up_front).convert("RGB")
    back_img = Image.open(up_back).convert("RGB") if up_back is not None else None

    # fonte final
    # por simplicidade, usamos o tamanho base global para todos; cada nome/preview aplica dx/dy/size do cartão 1,2,3 ciclicamente
    adj = [p1, p2, p3]
    for i, nm in enumerate(all_names):
        dx, dy, sz = adj[i % 3]
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
        else:  # PDF
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
