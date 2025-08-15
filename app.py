
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import zipfile
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Função para gerar certificados em PNG/JPEG/PDF
def gerar_certificados(imagem_frente, imagem_verso, lista_nomes, fonte, tamanho_fonte, cor_texto, formato_saida):
    certificados = []
    
    for nome in lista_nomes:
        # Criar imagem do certificado
        imagem = imagem_frente.copy()  # Copiar a imagem da frente
        
        # Adicionar nome na posição configurada
        draw = ImageDraw.Draw(imagem)
        font = ImageFont.truetype(fonte, tamanho_fonte)
        largura_texto, altura_texto = draw.textsize(nome, font)
        posicao = ((imagem.width - largura_texto) // 2, 400)  # Exemplo de posição (ajuste conforme necessário)
        draw.text(posicao, nome, font=font, fill=cor_texto)
        
        # Gerar verso, se necessário
        if imagem_verso:
            imagem_verso_copia = imagem_verso.copy()
            # Adicionar o nome ou outras informações na parte de verso, se desejar.
            certificados.append(imagem_verso_copia)
        
        # Salvar a imagem gerada em um arquivo temporário para exportação
        if formato_saida == "PNG":
            img_byte_array = BytesIO()
            imagem.save(img_byte_array, format="PNG")
            img_byte_array.seek(0)
            certificados.append(img_byte_array)
        elif formato_saida == "JPEG":
            img_byte_array = BytesIO()
            imagem.save(img_byte_array, format="JPEG")
            img_byte_array.seek(0)
            certificados.append(img_byte_array)
        elif formato_saida == "PDF":
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawImage(imagem, 0, 0, width=imagem.width, height=imagem.height)
            c.save()
            buffer.seek(0)
            certificados.append(buffer)

    return certificados

# Função para compactar os arquivos gerados em um .zip
def zip_certificados(certificados, formato_saida):
    with zipfile.ZipFile(f"certificados_gerados.{formato_saida.lower()}.zip", "w") as zipf:
        for i, cert in enumerate(certificados):
            nome_arquivo = f"certificado_{i + 1}.{formato_saida.lower()}"
            zipf.writestr(nome_arquivo, cert.read())
    
    return f"certificados_gerados.{formato_saida.lower()}.zip"

# Interface com Streamlit
def app():
    st.title("Gerador de Certificados")
    
    # Upload das imagens de frente e verso
    imagem_frente = st.file_uploader("Upload da Imagem da Frente do Certificado", type=["png", "jpeg", "jpg"])
    imagem_verso = st.file_uploader("Upload da Imagem do Verso do Certificado (Opcional)", type=["png", "jpeg", "jpg"])
    
    if imagem_frente is not None:
        imagem_frente = Image.open(imagem_frente)
        
        if imagem_verso is not None:
            imagem_verso = Image.open(imagem_verso)
        
        # Upload do arquivo de nomes
        arquivo_nomes = st.file_uploader("Upload do Arquivo de Nomes (.txt ou .csv)", type=["txt", "csv"])
        
        if arquivo_nomes is not None:
            if arquivo_nomes.name.endswith("txt"):
                lista_nomes = [line.strip() for line in arquivo_nomes.readlines()]
            elif arquivo_nomes.name.endswith("csv"):
                df = pd.read_csv(arquivo_nomes)
                lista_nomes = df.iloc[:, 0].tolist()  # Supondo que a coluna de nomes seja a primeira
            
            # Configuração do texto
            fonte = st.text_input("Fonte do Texto", "arial.ttf")
            tamanho_fonte = st.slider("Tamanho da Fonte", 10, 50, 18)
            cor_texto = st.color_picker("Cor do Texto", "#FFFFFF")
            formato_saida = st.selectbox("Formato de Saída", ["PDF", "PNG", "JPEG"])
            
            # Geração dos certificados
            if st.button("Gerar Certificados"):
                certificados = gerar_certificados(imagem_frente, imagem_verso, lista_nomes, fonte, tamanho_fonte, cor_texto, formato_saida)
                
                # Compactar os certificados em um arquivo .zip
                arquivo_zip = zip_certificados(certificados, formato_saida)
                
                # Oferecer o download do arquivo .zip
                with open(arquivo_zip, "rb") as f:
                    st.download_button(
                        label="Baixar Certificados",
                        data=f,
                        file_name=arquivo_zip,
                        mime=f"application/zip"
                    )

# Executar o app
if __name__ == "__main__":
    app()
