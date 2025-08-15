# -*- coding: utf-8 -*-
import io, os, base64, zipfile
from typing import List, Dict
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
# Vetor/relatórios
import svgwrite
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

try:
    import cairosvg
    HAS_CAIROSVG = True
except Exception:
    HAS_CAIROSVG = False

# Canvas availability check
def canvas_disponivel() -> bool:
    try:
        import streamlit_drawable_canvas  # noqa: F401
        return True
    except Exception:
        return False

FONTE_BENTOSA = os.path.join(os.path.dirname(__file__), "fonts", "Bentosa.ttf")

def _font(size:int):
    try:
        return ImageFont.truetype(FONTE_BENTOSA, size)
    except Exception:
        return ImageFont.load_default()

def _text_size(draw, text, font):
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

def carregar_base_preview(uploaded_file):
    """Retorna (PIL.Image|None, meta_dict)"""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    if name.endswith((".png",".jpg",".jpeg")):
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return img, {"type":"raster", "raw":raw}
    if name.endswith(".svg"):
        if not HAS_CAIROSVG:
            st.warning("Instale 'cairosvg' para pré-visualizar SVG.")
            return None, {"type":"svg", "raw":raw}
        png = cairosvg.svg2png(bytestring=raw)
        img = Image.open(io.BytesIO(png)).convert("RGB")
        return img, {"type":"svg", "raw":raw}
    # EPS/PDF preview: fallback branco (mantém bytes para exportação vetorial)
    st.warning("Pré-visualização de PDF/EPS não disponível (sem poppler/ghostscript). Usando tamanho padrão.")
    img = None
    return img, {"type":"pdf" if name.endswith(".pdf") else "eps", "raw":raw}

def ler_nomes(nomes_file) -> List[str]:
    if nomes_file.name.endswith(".txt"):
        return [n.strip() for n in nomes_file.read().decode("utf-8").splitlines() if n.strip()]
    df = pd.read_csv(nomes_file)
    return df.iloc[:,0].dropna().astype(str).tolist()

def desenhar_preview_nome(base_img, base_size, nome, x_anchor, y_anchor, gdx, gdy, dx, dy, font_size, color):
    """Gera preview PNG bytes (usa base_img quando disponível, senão branco)."""
    W,H = base_size
    if base_img is None:
        img = Image.new("RGB", (W,H), "white")
    else:
        img = base_img.copy()
    draw = ImageDraw.Draw(img)
    font = _font(font_size)
    tw, th = _text_size(draw, nome, font)
    x = (x_anchor + gdx + dx) - tw//2
    y = (y_anchor + gdy + dy) - th//2
    draw.text((x,y), nome, font=font, fill=color)
    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out.getvalue()

def _safe_filename(name: str) -> str:
    import re, unicodedata
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z0-9_\-\. ]+", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name or "certificado"

# ---------------- EXPORTAÇÃO ----------------
def _export_pdf_vector(front_meta, verso_meta, names, ajustes, size, anchor, gdx, gdy, color):
    W,H = size; x_anchor,y_anchor = anchor
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        for nome in names:
            a = ajustes[nome]
            buf = io.BytesIO()
            c = pdf_canvas.Canvas(buf, pagesize=(W,H))
            # fundo
            if front_meta["type"] == "raster":
                ib = io.BytesIO(front_meta["raw"]); img = Image.open(ib).convert("RGB")
                pb = io.BytesIO(); img = img.resize((W,H)); img.save(pb, format="PNG"); pb.seek(0)
                c.drawImage(ImageReader(pb), 0, 0, width=W, height=H)
            elif front_meta["type"] == "svg" and HAS_CAIROSVG:
                png = cairosvg.svg2png(bytestring=front_meta["raw"], output_width=W, output_height=H)
                pb = io.BytesIO(png); c.drawImage(ImageReader(pb), 0, 0, width=W, height=H)
            # texto vetorial
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont("Bentosa", FONTE_BENTOSA))
                font_name = "Bentosa"
            except Exception:
                font_name = "Helvetica"
            c.setFont(font_name, a["tamanho"])
            c.setFillColor(HexColor(color))
            from reportlab.pdfbase import pdfmetrics
            tw = pdfmetrics.stringWidth(nome, font_name, a["tamanho"])
            x = (x_anchor + gdx + a["dx"]) - tw/2
            y = (y_anchor + gdy + a["dy"])
            c.drawString(x, y, nome)
            c.showPage()
            # verso (rasterizado) se existir
            if verso_meta is not None:
                c.setPageSize((W,H))
                if verso_meta["type"] == "raster":
                    vb = io.BytesIO(verso_meta["raw"]); vimg = Image.open(vb).convert("RGB")
                    vpb = io.BytesIO(); vimg = vimg.resize((W,H)); vimg.save(vpb, format="PNG"); vpb.seek(0)
                    c.drawImage(ImageReader(vpb), 0, 0, width=W, height=H)
                elif verso_meta["type"] == "svg" and HAS_CAIROSVG:
                    vpng = cairosvg.svg2png(bytestring=verso_meta["raw"], output_width=W, output_height=H)
                    c.drawImage(ImageReader(io.BytesIO(vpng)), 0, 0, width=W, height=H)
                c.showPage()
            c.save(); buf.seek(0)
            zf.writestr(f"{_safe_filename(nome)}.pdf", buf.getvalue())
    out.seek(0)
    return out.getvalue()

def _export_svg_vector(front_meta, names, ajustes, size, anchor, gdx, gdy, color):
    W,H = size; x_anchor,y_anchor = anchor
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        # fundo rasterizado (se houver)
        if front_meta["type"] == "raster":
            bg = Image.open(io.BytesIO(front_meta["raw"])).convert("RGB").resize((W,H))
            pbg = io.BytesIO(); bg.save(pbg, format="PNG"); pbg.seek(0)
            b64 = base64.b64encode(pbg.getvalue()).decode("ascii")
            bg_href = f"data:image/png;base64,{b64}"
        elif front_meta["type"] == "svg" and HAS_CAIROSVG:
            png = cairosvg.svg2png(bytestring=front_meta["raw"], output_width=W, output_height=H)
            b64 = base64.b64encode(png).decode("ascii"); bg_href = f"data:image/png;base64,{b64}"
        else:
            bg_href = None

        for nome in names:
            a = ajustes[nome]
            dwg = svgwrite.Drawing(size=(W,H))
            if bg_href:
                dwg.add(dwg.image(href=bg_href, insert=(0,0), size=(W,H)))
            # texto vetorial (aprox. centralizado)
            dwg.add(dwg.text(
                nome,
                insert=(x_anchor + gdx + a["dx"], y_anchor + gdy + a["dy"]),
                text_anchor="middle",
                font_size=a["tamanho"],
                font_family="Bentosa, Helvetica, Arial",
                fill=color
            ))
            zf.writestr(f"{_safe_filename(nome)}.svg", dwg.tostring())
    out.seek(0)
    return out.getvalue()

def _export_eps_vector(front_meta, names, ajustes, size, anchor, gdx, gdy, color):
    from reportlab.graphics.shapes import Drawing, Image as RLImage, String
    from reportlab.graphics import renderPS
    W,H = size; x_anchor,y_anchor = anchor
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        # preparar fundo como PNG se houver
        bg_png = None
        if front_meta["type"] == "raster":
            img = Image.open(io.BytesIO(front_meta["raw"])).convert("RGB").resize((W,H))
            buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0); bg_png = buf
        elif front_meta["type"] == "svg" and HAS_CAIROSVG:
            png = cairosvg.svg2png(bytestring=front_meta["raw"], output_width=W, output_height=H)
            bg_png = io.BytesIO(png)
        for nome in names:
            d = Drawing(W, H)
            if bg_png:
                d.add(RLImage(0,0,width=W,height=H,path=bg_png))
            d.add(String(x_anchor + gdx + ajustes[nome]["dx"], y_anchor + gdy + ajustes[nome]["dy"],
                         nome, textAnchor="middle", fontSize=ajustes[nome]["tamanho"], fillColor=HexColor(color)))
            b = io.BytesIO(); renderPS.drawToFile(d, b, fmt="EPS"); b.seek(0)
            zf.writestr(f"{_safe_filename(nome)}.eps", b.getvalue())
    out.seek(0)
    return out.getvalue()

def _export_raster(front_meta, names, ajustes, size, anchor, gdx, gdy, color, fmt, px_width, dpi, jpg_quality):
    W,H = size; x_anchor,y_anchor = anchor
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        # base rasterizada para esse tamanho
        if front_meta["type"] == "raster":
            base_img = Image.open(io.BytesIO(front_meta["raw"])).convert("RGB").resize((W,H))
        elif front_meta["type"] == "svg" and HAS_CAIROSVG:
            png = cairosvg.svg2png(bytestring=front_meta["raw"], output_width=W, output_height=H)
            base_img = Image.open(io.BytesIO(png)).convert("RGB")
        else:
            base_img = Image.new("RGB", (W,H), "white")
        for nome in names:
            a = ajustes[nome]
            img = base_img.copy(); draw = ImageDraw.Draw(img)
            font = _font(a["tamanho"])
            tw, th = draw.textbbox((0,0), nome, font=font)[2:]
            x = (x_anchor + gdx + a["dx"]) - tw/2
            y = (y_anchor + gdy + a["dy"]) - th//2
            draw.text((x,y), nome, font=font, fill=color)
            buf = io.BytesIO()
            if fmt == "PNG":
                img.save(buf, format="PNG", dpi=(dpi,dpi))
            else:
                img.save(buf, format="JPEG", quality=jpg_quality, dpi=(dpi,dpi))
            buf.seek(0)
            zf.writestr(f"{_safe_filename(nome)}.{fmt.lower()}", buf.getvalue())
    out.seek(0)
    return out.getvalue()

def exportar_zip(frente_file, verso_file, nomes, ajustes, base_meta, base_size, x_anchor, y_anchor,
                 gdx, gdy, color, formato, px_width, dpi, jpg_quality, padrao_nome):
    """Gera um ZIP contendo arquivos individuais no formato desejado.
       (padrao_nome é aplicado substituindo {name})
    """
    # Padrão de nomes
    nomes_safe = [ (padrao_nome or "{name}").format(name=_safe_filename(n)) for n in nomes ]
    # Ajustes com nomes já normalizados
    ajustes_safe = { nomes_safe[i]: ajustes[nomes[i]] for i in range(len(nomes)) }

    # Preparar meta do verso, se houver
    verso_meta = None
    if verso_file is not None:
        _, verso_meta = carregar_base_preview(verso_file)

    if formato == "PDF (vetor)":
        return _export_pdf_vector(base_meta, verso_meta, nomes_safe, ajustes_safe, base_size, (x_anchor,y_anchor), gdx, gdy, color)
    if formato == "SVG (vetor)":
        return _export_svg_vector(base_meta, nomes_safe, ajustes_safe, base_size, (x_anchor,y_anchor), gdx, gdy, color)
    if formato == "EPS (vetor)":
        return _export_eps_vector(base_meta, nomes_safe, ajustes_safe, base_size, (x_anchor,y_anchor), gdx, gdy, color)
    # Raster
    fmt = "PNG" if formato == "PNG" else "JPEG"
    return _export_raster(base_meta, nomes_safe, ajustes_safe, base_size, (x_anchor,y_anchor), gdx, gdy, color, fmt, px_width, dpi, jpg_quality)
