import os

# Création du dossier si inexistant
os.makedirs(".streamlit", exist_ok=True)

# Le contenu du thème TradingView
config_content = """[theme]
primaryColor = "#2962ff"
backgroundColor = "#131722"
secondaryBackgroundColor = "#1e222d"
textColor = "#d1d4dc"
font = "sans serif"

[server]
headless = true
port = 8501
"""

# Écriture forcée en UTF-8 (C'est la clé du succès !)
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write(config_content)

print("✅ Fichier config.toml régénéré proprement en UTF-8.")

