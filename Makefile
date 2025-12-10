.PHONY: install up down logs pipeline api ui clean help

# Default target: show command list
.DEFAULT_GOAL := help

help: ## Displays all available Makefile commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# -------------------------------------------------------------------------
# INSTALLATION
# -------------------------------------------------------------------------
install: ## Installs all project dependencies (Python + Playwright)
	pip install poetry
	poetry install
	poetry run playwright install

# -------------------------------------------------------------------------
# DOCKER INFRASTRUCTURE
# -------------------------------------------------------------------------
up: ## Starts the PostgreSQL database in detached mode
	docker compose up -d

down: ## Stops and removes running containers
	docker compose down

logs: ## Streams logs from Docker services
	docker compose logs -f

# -------------------------------------------------------------------------
# PROJECT EXECUTION
# -------------------------------------------------------------------------
pipeline: ## Runs ESG ingestion pipeline (Scraping -> AI -> Database)
	py -m scripts.run_esg_pipeline

api: ## Runs the FastAPI engine on port 8000
	py -m uvicorn src.engine.api_server:app --reload --port 8000

ui: ## Launches the Streamlit interface
	py -m streamlit run app.py

# -------------------------------------------------------------------------
# MAINTENANCE
# -------------------------------------------------------------------------
clean: ## Removes temporary files and Python cache folders
	Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo -Recurse | Remove-Item -Force -Recurse
