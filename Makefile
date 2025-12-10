.PHONY: install up down logs pipeline api ui clean help

# Par défaut, afficher l'aide
.DEFAULT_GOAL := help

help: ## Affiche la liste des commandes disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- INSTALLATION ---
install: ## Installe toutes les dépendances (Python + Playwright)
	pip install poetry
	poetry install
	poetry run playwright install

# --- INFRASTRUCTURE (DOCKER) ---
up: ## Démarre la base de données PostgreSQL en arrière-plan
	docker compose up -d

down: ## Arrête et supprime les conteneurs
	docker compose down

logs: ## Affiche les logs de la base de données
	docker compose logs -f

# --- EXÉCUTION DU PROJET ---
pipeline: ## Lance l'ingestion des données (Scraping -> IA -> DB)
	py -m scripts.run_esg_pipeline

api: ## Lance le moteur de calcul (FastAPI) sur le port 8000
	py -m uvicorn src.engine.api_server:app --reload --port 8000

ui: ## Lance l'interface graphique (Streamlit)
	py -m streamlit run app.py

# --- MAINTENANCE ---
clean: ## Nettoie les fichiers temporaires et caches (__pycache__)
	Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo -Recurse | Remove-Item -Force -Recurse