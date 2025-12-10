Veritas Quant – AI-Driven ESG & HRP Allocation Engine

Next-generation Asset Management platform fusing Sovereign Generative AI (Local LLM) with Hierarchical Risk Parity (HRP) optimization.

1. Executive Summary

Veritas Quant (codenamed LLM-4-ESG-in-AM) addresses the two main failures of modern asset management: the instability of correlation matrices (Markowitz failure) and the superficiality of ESG ratings (Greenwashing).

This platform acts as an Autonomous Quant Factory:

Data Acquisition: An autonomous agent scrapes unstructured web data (Impact Reports, News) utilizing DuckDuckGo search heuristics without human input.

Semantic Analysis: A local Large Language Model (Llama 3) reads, understands, and scores ESG risks in real-time, enforcing a JSON schema for structured output.

Quantitative Allocation: A mathematically robust engine allocates capital using Hierarchical Risk Parity (HRP), utilizing graph theory and recursive bisection to prioritize diversification over naive return maximization.

2. Architectural Design

The system follows a Modular Monolith pattern orchestrated via Docker, ensuring strict separation between Data Engineering, Intelligence, and Quantitative Finance.

System Diagram

graph TD
    subgraph "Data Layer (The Collector)"
        Agent[Autonomous Scraper Agent]
        Web[(Unstructured Web Data)]
        LLM[Generative AI (Llama 3 / GPT)]
        DB[(PostgreSQL Governance)]
    end

    subgraph "Quant Layer (The Engine)"
        API[FastAPI Calculation Engine]
        Market[Market Data (YFinance)]
        HRP[HRP Optimizer (SciPy)]
    end

    subgraph "Presentation Layer"
        UI[Streamlit Pro Dashboard]
    end

    Agent -->|1. Search & Scrape| Web
    Web -->|2. Raw Text| LLM
    LLM -->|3. Structured ESG Score| DB
    UI -->|4. Request Optimization| API
    API -->|5. Fetch Filtered Universe| DB
    API -->|6. Fetch Prices| Market
    API -->|7. Cluster & Allocate| HRP
    HRP -->|8. Optimal Weights| UI


Why this Architecture?

Data Governance: All AI-generated scores are persisted in PostgreSQL for auditability. We never re-run expensive AI inference on the same document twice.

Sovereignty: The system supports Local Inference (Ollama), allowing sensitive financial analysis without data leaving the secure infrastructure.

Resilience: The Scraper uses an Autonomous Discovery Agent to find documents dynamically even if URLs change.

3. The Intelligence Layer: Autonomous AI Agent

Unlike traditional scrapers that require hardcoded URLs, Veritas Quant utilizes an Agentic Workflow.

Workflow Logic

Discovery: The agent generates search queries (e.g., "Tesla Sustainability Report 2024 pdf").

Extraction: Utilizes BeautifulSoup with user-agent rotation to extract readable text from investor relations pages.

Reasoning: The text is fed to Llama 3 (or OpenAI) with a strict prompt engineering template to enforce JSON output.

Prompt Strategy: "Act as a Senior ESG Analyst. Read the following 10k characters. Output a score from 0-100 and a 1-sentence rationale based on carbon intensity and governance."

4. Quantitative Framework (Mathematics)

The allocation engine moves beyond Mean-Variance optimization by implementing Hierarchical Risk Parity (HRP), as introduced by Marcos Lopez de Prado (2016).

A. Distance Metric Construction

We convert the correlation matrix into a distance matrix to prepare for clustering. This transforms financial correlation into a metric space satisfying triangular inequality.

$$d_{i,j} = \sqrt{0.5 \times (1 - \rho_{i,j})}$$

Where:

$\rho_{i,j}$ is the correlation coefficient between asset $i$ and $j$.

$d_{i,j}$ is the distance metric ($0 \le d \le 1$).

B. Hierarchical Clustering (Tree Structure)

We apply Ward’s Method to minimize the variance within clusters. This groups assets that behave similarly (e.g., Tech stocks vs. Oil stocks) into a Dendrogram.

graph BT
    AAPL --> TechCluster
    MSFT --> TechCluster
    XOM --> EnergyCluster
    CVX --> EnergyCluster
    TechCluster --> Market
    EnergyCluster --> Market


C. Quasi-Diagonalization

The covariance matrix is reordered based on the clustering tree. This places similar assets adjacent to each other, revealing the true hierarchical structure of risk (Matrix Diagonalization).

D. Recursive Bisection (Capital Allocation)

Capital is allocated top-down through the tree. At each split, weights are assigned inversely to the variance of the sub-clusters.

$$\alpha = 1 - \frac{Var_{left}}{Var_{left} + Var_{right}}$$

Result: A portfolio that is robust to correlation shocks and requires no inversion of the covariance matrix (numerically stable).

5. Visual Interface (TradingView Style)

The platform features a Dark-Mode Professional Dashboard built with Streamlit and Plotly.

1. Strategy Configuration

Define the universe, set the AI-filtering strictness threshold, and choose the time horizon.

2. HRP Allocation & AI Audit

Visualize the optimal HRP weights and audit the "Rationale" generated by the AI for each asset.

(Place your screenshots in docs/images/ to enable these previews)

6. Installation & Usage

Prerequisites

Docker Desktop (Required for Database & Environment)

Ollama (Optional, for free local AI) -> ollama run llama3

1. Setup Environment

# Clone repository
git clone [https://github.com/YOUR_USERNAME/Veritas-Quant-ESG-Engine.git](https://github.com/YOUR_USERNAME/Veritas-Quant-ESG-Engine.git)
cd Veritas-Quant-ESG-Engine

# Create environment file from template
# Windows
copy deployment\.env.example .env
# Linux/Mac
cp deployment/.env.example .env


2. Launch Infrastructure (Docker)

# Starts PostgreSQL and Python Environment
docker compose up --build -d


3. Run the Data Pipeline (Agent)

This step activates the autonomous agent to scrape the web and populate the database.

# Using the Makefile shortcut
make pipeline
# OR manual command
py -m scripts.run_esg_pipeline


4. Launch the Platform

Terminal 1: Calculation Engine

make api
# OR: py -m uvicorn src.engine.api_server:app --reload --port 8000


Terminal 2: User Interface

make ui
# OR: py -m streamlit run app.py


7. Project Structure (Detailed)

The codebase follows Clean Architecture principles to ensure scalability.

Veritas-Quant/
├── config/                 # [CONFIGURATION]
│   ├── esg_criteria.json   # Rules for the AI (Keywords, Exclusion sectors)
│   └── settings.py         # Pydantic Settings (DB Creds, API Keys) management
│
├── src/                    # [SOURCE CODE]
│   ├── collector/          # [DATA INGESTION LAYER]
│   │   ├── scraper.py      # AGENT: Autonomous Web Scraper (DuckDuckGo/BeautifulSoup)
│   │   ├── llm_analyzer.py # BRAIN: Hybrid Client (Ollama Local / OpenAI Cloud)
│   │   └── loader.py       # MARKET: Robust Data Fetcher (YFinance wrapper)
│   │
│   ├── engine/             # [QUANT CORE LAYER]
│   │   ├── hrp_optimizer.py # MATH: Implementation of Lopez de Prado's HRP Algo
│   │   ├── db_manager.py   # STORAGE: SQL Persistence (SQLAlchemy ORM)
│   │   ├── api_server.py   # EXPOSURE: FastAPI Entrypoint for the Frontend
│   │   └── utils.py        # TOOLS: Log-returns and Covariance calculations
│
├── deployment/             # [INFRASTRUCTURE]
│   ├── docker-compose.yml  # Container orchestration (Postgres + Python App)
│   └── Dockerfile          # Python environment definition (Playwright support)
│
├── scripts/                # [ORCHESTRATION]
│   └── run_esg_pipeline.py # Script connecting Scraper -> AI -> Database
│
├── app.py                  # [FRONTEND] Streamlit Application (TradingView Style)
└── Makefile                # [AUTOMATION] Shortcuts for dev commands


8. Continuous Integration

Reliability is ensured via GitHub Actions:

Type Safety: MyPy ensures strict typing for financial calculations.

Linting: Ruff enforces PEP8 standards.

Testing: Pytest validates the mathematical accuracy of the HRP engine.

9. License

Distributed under the MIT License.

Veritas Quant – Where Sovereign AI meets Convex Optimization.