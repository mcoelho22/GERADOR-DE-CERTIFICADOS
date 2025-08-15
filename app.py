
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import zipfile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def gerar_certificados(imagem_frente, imagem_verso, lista_nomes, fonte, tamanho_fonte, cor_texto, formato_saida):
    certificados = []
    for nome in lista_nomes:
        imagem = imagem_frente.copy()
        draw = ImageDraw.Draw(imagem)
        font = ImageFont.truetype(fonte, tamanho_fonte)
        largura_texto, altura_texto = draw.textsize(nome, font)
        posicao = ((imagem.width - largura_texto) // 2, 400)
        draw.text(posicao, nome, font=font, fill=cor_texto)
        if formato_saida == "PNG":
            img_byte_array = BytesIO()
            imagem.save(img_byte_array, format="PNG")
            img_byte_array.seek(0)
            certificados.append((f"{nome}.png", img_byte_array))
        elif formato_saida == "JPEG":
            img_byte_array = BytesIO()
            imagem.save(img_byte_array, format="JPEG")
            img_byte_array.seek(0)
            certificados.append((f"{nome}.jpg", img_byte_array))
        elif formato_saida == "PDF":
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            imagem_path = BytesIO()
            imagem.save(imagem_path, format="PNG")
            imagem_path.seek(0)
            c.drawImage(Image.open(imagem_path), 0, 0, width=imagem.width, height=imagem.height)
            c.save()
            buffer.seek(0)
            certificados.append((f"{nome}.pdf", buffer))
    return certificados

def zip_certificados(certificados):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for nome_arquivo, arquivo in certificados:
            zipf.writestr(nome_arquivo, arquivo.read())
    zip_buffer.seek(0)
    return zip_buffer

def app():
    st.title("Gerador de Certificados")
    imagem_frente = st.file_uploader("Imagem Frente", type=["png", "jpeg", "jpg"])
    imagem_verso = st.file_uploader("Imagem Verso (Opcional)", type=["png", "jpeg", "jpg"])
    if imagem_frente:
        imagem_frente = Image.open(imagem_frente)
        if imagem_verso:
            imagem_verso = Image.open(imagem_verso)
        arquivo_nomes = st.file_uploader("Lista de nomes (.txt ou .csv)", type=["txt", "csv"])
        if arquivo_nomes:
            if arquivo_nomes.name.endswith("txt"):
                lista_nomes = [line.decode("utf-8").strip() for line in arquivo_nomes.readlines()]
            else:
                df = pd.read_csv(arquivo_nomes)
                lista_nomes = df.iloc[:, 0].tolist()
            fonte = st.text_input("Fonte", "arial.ttf")
            tamanho_fonte = st.slider("Tamanho da Fonte", 10, 50, 18)
            cor_texto = st.color_picker("Cor do Texto", "#FFFFFF")
            formato_saida = st.selectbox("Formato de Saída", ["PDF", "PNG", "JPEG"])
            if st.button("Gerar Certificados"):
                certificados = gerar_certificados(imagem_frente, imagem_verso, lista_nomes, fonte, tamanho_fonte, cor_texto, formato_saida)
                zip_buffer = zip_certificados(certificados)
                st.download_button(
                    label="Baixar Certificados (.zip)",
                    data=zip_buffer,
                    file_name="certificados.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    app()
