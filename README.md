
# Gerador de Certificados

Este projeto é um aplicativo web desenvolvido com Streamlit para a geração automática de certificados personalizados. O usuário pode:

- Carregar uma imagem base para o certificado (frente e verso).
- Fazer upload de uma lista de nomes (em formato `.txt` ou `.csv`).
- Configurar a fonte, tamanho e cor do texto para o nome nos certificados.
- Gerar e exportar os certificados em PDF, PNG ou JPEG.
- Baixar todos os certificados gerados em um único arquivo `.zip`.

## Como Usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/gerador_certificados.git
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

## Tecnologias Usadas

- Python 3.x
- Streamlit
- Pillow (para edição de imagens)
- ReportLab (para geração de PDFs)
