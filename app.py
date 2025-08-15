
# -*- coding: utf-8 -*-
# App de geração de certificados (deploy-friendly)

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Gerador de Certificados", page_icon="🖨️", layout="wide")

def ler_lista_nomes(arquivo):
    if arquivo.name.lower().endswith(".txt"):
        content = arquivo.read()
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = content.decode(enc)
                break
            except Exception:
                continue
        nomes = [l.strip() for l in text.splitlines() if l.strip()]
    else:
        df = pd.read_csv(arquivo)
        nomes = df.iloc[:, 0].dropna().astype(str).tolist()
    return nomes

def desenhar_nome(img: Image.Image, nome: str, fonte_path: str, tamanho: int, cor_hex: str, x: int, y: int, anchor: str):
    im = img.copy()
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(fonte_path, tamanho)
    except Exception:
        font = ImageFont.load_default()
    draw.text((x, y), nome, fill=cor_hex, font=font, anchor=anchor)
    return im

def gerar_imagem(imagem_base_bytes, nome, fonte, tamanho, cor, x, y, anchor):
    base = Image.open(imagem_base_bytes).convert("RGB")
    return desenhar_nome(base, nome, fonte, tamanho, cor, x, y, anchor)

def pil_para_pdf_page(img: Image.Image) -> bytes:
    """Converte uma imagem PIL em uma página PDF (A4) usando ReportLab e retorna bytes."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    img_w, img_h = img.size
    ratio = min(w / img_w, h / img_h)
    new_w, new_h = img_w * ratio, img_h * ratio
    x = (w - new_w) / 2
    y = (h - new_h) / 2
    c.drawImage(ImageReader(img), x, y, width=new_w, height=new_h)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def compactar(certificados):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for nome_arquivo, data in certificados:
            z.writestr(nome_arquivo, data)
    zip_buffer.seek(0)
    return zip_buffer

st.title("Gerador de Certificados")

col1, col2 = st.columns(2)
with col1:
    img_frente_up = st.file_uploader("Certificado - Frente (PNG/JPG)", type=["png", "jpg", "jpeg"])
with col2:
    img_verso_up = st.file_uploader("Certificado - Verso (opcional)", type=["png", "jpg", "jpeg"])

lista_up = st.file_uploader("Lista de nomes (.txt ou .csv)", type=["txt", "csv"])

st.subheader("Ajustes do Texto")
c1, c2, c3, c4 = st.columns(4)
with c1:
    fonte_path = st.text_input("Fonte (.ttf disponível no servidor)", "arial.ttf")
with c2:
    tamanho = st.slider("Tamanho", 10, 180, 48)
with c3:
    cor = st.color_picker("Cor", "#FFB000")
with c4:
    anchor = st.selectbox("Alinhamento", ["mm", "la", "ma", "ra"], help="mm=centro; la=esq; ma=meio; ra=direita")

x = st.number_input("Posição X", value=1000, step=5)
y = st.number_input("Posição Y", value=600, step=5)

formato = st.selectbox("Formato de saída", ["PDF", "PNG", "JPEG"])

padrao_nome = st.text_input("Padrão do nome do arquivo", "{name}")
st.caption("Use {name} para o nome da pessoa. Ex: Certificado_{name}")

if st.button("Gerar e baixar ZIP", disabled=not (img_frente_up and lista_up)):
    nomes = ler_lista_nomes(lista_up)
    certificados = []

    for nome in nomes:
        img_out = gerar_imagem(img_frente_up, nome, fonte_path, tamanho, cor, int(x), int(y), anchor)
        if formato == "PNG":
            b = BytesIO(); img_out.save(b, "PNG", optimize=True); b.seek(0)
            certificados.append((f"{padrao_nome.format(name=nome)}.png", b.read()))
        elif formato == "JPEG":
            b = BytesIO(); img_out.save(b, "JPEG", quality=95, subsampling=0); b.seek(0)
            certificados.append((f"{padrao_nome.format(name=nome)}.jpg", b.read()))
        else:
            certificados.append((f"{padrao_nome.format(name=nome)}.pdf", pil_para_pdf_page(img_out)))

        if img_verso_up is not None:
            verso = Image.open(img_verso_up).convert("RGB")
            if formato == "PNG":
                b = BytesIO(); verso.save(b, "PNG", optimize=True); b.seek(0)
                certificados.append((f"{padrao_nome.format(name=nome)}_verso.png", b.read()))
            elif formato == "JPEG":
                b = BytesIO(); verso.save(b, "JPEG", quality=95, subsampling=0); b.seek(0)
                certificados.append((f"{padrao_nome.format(name=nome)}_verso.jpg", b.read()))
            else:
                certificados.append((f"{padrao_nome.format(name=nome)}_verso.pdf", pil_para_pdf_page(verso)))

    zip_bytes = compactar(certificados)
    st.download_button("📦 Baixar ZIP", zip_bytes, file_name="certificados.zip", mime="application/zip")

st.write("---")
st.caption("Todo processamento ocorre no servidor.")
