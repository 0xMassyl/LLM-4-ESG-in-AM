import os

# Ensures the Streamlit configuration directory exists.
os.makedirs(".streamlit", exist_ok=True)

# TradingView-inspired dark theme for Streamlit.
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



# Writes the configuration file explicitly in UTF-8 to avoid encoding issues.
with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write(config_content)

print("Streamlit config.toml successfully regenerated with UTF-8 encoding.")
