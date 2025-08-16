
# Gerador de Certificados — Layout Fiel

- Sidebar com **Ajustes Globais** (posição, escala, alinhamento, fonte Bentosa via upload, cor).
- Upload **frente**, **verso** e **lista de nomes** em 3 colunas.
- **Previews** em 3 cartões com ajustes de `dx`, `dy` e tamanho **individuais**.
- Exporta **PDF/PNG/JPEG** (individual por pessoa) e baixa tudo em **ZIP**.
- Todo o processamento é feito no servidor.

## Rodar localmente
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
