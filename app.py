
# -*- coding: utf-8 -*-
# Gerador de Certificados - PDF no tamanho ORIGINAL do certificado (sem A4)

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Gerador de Certificados", page_icon="🎓", layout="wide")

# --------------------------
# Helpers
# --------------------------
def load_font(font_file, size):
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

def pil_list_to_pdf_original(images):
    '''Gera PDF multipágina usando o TAMANHO ORIGINAL de cada imagem.'''
    if not images:
        return b""
    buf = BytesIO()
    # Canvas inicial com o tamanho da primeira imagem
    first = images[0].convert("RGB")
    w0, h0 = first.size  # pixels tratados como points (sem margens)
    c = canvas.Canvas(buf, pagesize=(w0, h0))
    def draw_page(img):
        im = img.convert("RGB")
        w, h = im.size
        c.setPageSize((w, h))
        c.drawImage(ImageReader(im), 0, 0, width=w, height=h)
        c.showPage()
    for im in images:
        draw_page(im)
    c.save()
    buf.seek(0)
    return buf.read()

def read_names(file):
    if file is None: return []
    try:
        file.seek(0)
    except Exception:
        pass
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
        names = pd.read_csv(file).iloc[:,0].dropna().astype(str).tolist()
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
:root { --accent:#ff9f0a; }
h1,h2{ color:var(--accent) !important; font-weight:800 }
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
        g_x_slider = st.slider("Posição X (slider)", min_value=0, max_value=5000, value=1000, step=1)
        g_y_slider = st.slider("Posição Y (slider)", min_value=0, max_value=3000, value=600, step=1)
        col_xy = st.columns(2)
        with col_xy[0]:
            g_x_num = st.number_input("Posição X (numérico)", value=g_x_slider, step=1)
        with col_xy[1]:
            g_y_num = st.number_input("Posição Y (numérico)", value=g_y_slider, step=1)
        g_x = int(g_x_num)
        g_y = int(g_y_num)

        g_align = st.radio("Alinhamento", ["Esquerda","Centro","Direita"], horizontal=True)
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
st.session_state["__names__"] = names  # cache para exportação
if not names:
    names = ["nome da pessoa"]

# Estados por nome
for idx, nm in enumerate(names):
    if f"dx_{idx}" not in st.session_state: st.session_state[f"dx_{idx}"] = 0
    if f"dy_{idx}" not in st.session_state: st.session_state[f"dy_{idx}"] = 0
    if f"size_{idx}" not in st.session_state: st.session_state[f"size_{idx}"] = base_font_size

def render_preview(idx, nm, front_bytes):
    st.markdown("<div class='preview-card'>", unsafe_allow_html=True)
    cA,cB,cC = st.columns(3)
    with cA:
        st.session_state[f"dx_{idx}"] = st.slider("dx (slider)", min_value=-2000, max_value=2000, value=st.session_state[f"dx_{idx}"], step=1, key=f"ctrl_dx_{idx}")
    with cB:
        st.session_state[f"dy_{idx}"] = st.slider("dy (slider)", min_value=-2000, max_value=2000, value=st.session_state[f"dy_{idx}"], step=1, key=f"ctrl_dy_{idx}")
    with cC:
        st.session_state[f"size_{idx}"] = st.slider("tamanho (slider)", min_value=6, max_value=300, value=st.session_state[f"size_{idx}"], step=1, key=f"ctrl_size_{idx}")
    cn1, cn2, cn3 = st.columns(3)
    with cn1:
        st.session_state[f"dx_{idx}"] = st.number_input("dx (numérico)", value=st.session_state[f"dx_{idx}"], step=1, key=f"num_dx_{idx}")
    with cn2:
        st.session_state[f"dy_{idx}"] = st.number_input("dy (numérico)", value=st.session_state[f"dy_{idx}"], step=1, key=f"num_dy_{idx}")
    with cn3:
        st.session_state[f"size_{idx}"] = st.number_input("tamanho (numérico)", value=st.session_state[f"size_{idx}"], step=1, key=f"num_size_{idx}")

    if front_bytes is not None:
        try: front_bytes.seek(0)
        except Exception: pass
        base = Image.open(front_bytes).convert("RGB")
    else:
        base = Image.new("RGB", (1280, 720), "#111111")

    font = load_font(font_upload, int(st.session_state[f"size_{idx}"] * g_scale))
    out = draw_name_on_image(
        base, nm, int(g_x + st.session_state[f"dx_{idx}"]), int(g_y + st.session_state[f"dy_{idx}"]),
        font, font_color, g_align
    )
    st.image(out, use_container_width=True, caption=nm)
    st.markdown("</div>", unsafe_allow_html=True)

# Grid 3 colunas
cols = st.columns(3, gap="large")
for i, nm in enumerate(names):
    with cols[i % 3]:
        render_preview(i, nm, up_front)

st.divider()

# --------------------------
# Geração de arquivos
# --------------------------
gen = st.button("Gerar e baixar .zip", type="primary", use_container_width=True, disabled=up_front is None or len(st.session_state.get("__names__", [])) == 0)

if gen:
    fmt = out_fmt.split(" ")[0]  # PDF/PNG/JPEG
    try: up_front.seek(0)
    except Exception: pass
    front_img = Image.open(up_front).convert("RGB")
    back_img = None
    if up_back is not None:
        try: up_back.seek(0)
        except Exception: pass
        back_img = Image.open(up_back).convert("RGB")

    files = []
    names_all = st.session_state.get("__names__", [])
    if not names_all and up_names is not None:
        names_all = read_names(up_names)

    for i, nm in enumerate(names_all):
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
            # PDF: frente + verso no MESMO arquivo, no tamanho ORIGINAL das imagens
            pages = [out_img]
            if back_img is not None:
                pages.append(back_img)
            pdf_bytes = pil_list_to_pdf_original(pages)
            files.append((f"{fname_base}.pdf", pdf_bytes))

    z = zip_bytes(files)
    st.download_button("📦 Baixar ZIP", data=z, file_name="certificados.zip", mime="application/zip", use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='center-h'><div style='max-width:900px;text-align:center' class='caption'>
<b>Toda grande invenção é, em essência, a resposta engenhosa a um problema de magnitude equivalente, nascendo da urgência e da complexidade que instigam o intelecto humano a transcender seus próprios limites.</b><br/>
by: Coelho<br/><br/>
<b>Deus seja louvado.</b>
</div></div>""", unsafe_allow_html=True)
