
# Gerador de Certificados (Streamlit)

Deploy amigável ao Streamlit Community Cloud. Use `runtime.txt` para Python 3.11 e
`requirements.txt` com versões amplas para evitar erros de build.

## Executar localmente
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run app.py
```
