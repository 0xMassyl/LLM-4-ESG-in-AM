Veritas Quant
AI-Driven ESG Scoring and Hierarchical Risk Parity Allocation Engine

Veritas Quant (codename: LLM-4-ESG-in-AM) is a next-generation asset-management platform unifying three disciplines:

Autonomous Data Engineering

Generative AI-based ESG Scoring

Hierarchical Risk Parity (HRP) Portfolio Optimization

The system delivers explainable ESG intelligence and mathematically stable portfolio allocation, addressing structural weaknesses in both modern ESG research and traditional Markowitz frameworks.

1. Executive Summary

Modern asset management faces two persistent issues:

Instability and overfitting in covariance inversion models (Markowitz failure).

Shallow and inconsistent ESG ratings leading to greenwashing.

Veritas Quant tackles these problems through a fully autonomous architecture:

Data Acquisition
An agentic scraper dynamically discovers corporate sustainability reports using DuckDuckGo heuristics without requiring static URLs.

Semantic Intelligence
A local or cloud-based LLM (Llama 3 or GPT) reads sustainability disclosures and converts them into structured ESG scores with enforced JSON schemas.

Quantitative Allocation
A Hierarchical Risk Parity optimizer allocates capital through clustering, quasi-diagonalization, and recursive variance-based bisection.

The result is a pipeline capable of ingesting raw unstructured text and outputting a mathematically robust portfolio.

2. Architectural Design

The platform follows a modular monolith design with clearly separated data, intelligence, and quant layers, orchestrated through Docker.

graph TD
    subgraph "Data Layer (Collector)"
        Agent[Autonomous Scraper Agent]
        Web[(Unstructured Web Data)]
        LLM[Generative AI Engine]
        DB[(PostgreSQL Database)]
    end

    subgraph "Quant Layer (Engine)"
        API[FastAPI Engine]
        Market[YFinance Market Data]
        HRP[HRP Optimizer]
    end

    subgraph "Presentation Layer"
        UI[Streamlit Dashboard]
    end

    Agent -->|1. Search & Scrape| Web
    Web -->|2. Raw Text| LLM
    LLM -->|3. ESG Score| DB
    UI -->|4. Request Optimization| API
    API -->|5. Filter Universe| DB
    API -->|6. Fetch Prices| Market
    API -->|7. Optimize| HRP
    HRP -->|8. Allocation| UI

Why this Architecture?

Data governance
All AI-generated outputs are persisted for auditability and reproducibility. Expensive LLM inference is never repeated unnecessarily.

Sovereignty
Local inference via Ollama ensures full operational capability without sending sensitive corporate data to external providers.

Resilience
The agent can rediscover sustainability documents even when corporate websites change structure.

3. The Intelligence Layer: Autonomous AI Agent

Unlike static scrapers, Veritas Quant uses an agentic workflow capable of:

Generating domain-specific queries such as
"Tesla sustainability report 2024 summary".

Extracting semantic text from investor-relations pages using BeautifulSoup and heuristic filtering.

Applying strict prompt engineering to produce normalized JSON output.

Prompt Strategy (simplified):
Act as a Senior ESG Analyst.
Read the following document.
Output a score from 0–100 and a one-sentence rationale.

The system supports both:

Cloud inference (OpenAI GPT models).

Local inference (Llama 3 via Ollama).

4. Quantitative Framework

The engine implements Hierarchical Risk Parity as proposed by Marcos López de Prado (2016).

A. Distance Metric

Correlation is mapped to a distance satisfying metric properties:

𝑑
𝑖
,
𝑗
=
0.5
×
(
1
−
𝜌
𝑖
,
𝑗
)
d
i,j
	​

=
0.5×(1−ρ
i,j
	​

)
	​

B. Hierarchical Clustering

Assets are grouped using Ward’s method to minimize intra-cluster variance.

graph BT
    AAPL --> TechCluster
    MSFT --> TechCluster
    XOM --> EnergyCluster
    CVX --> EnergyCluster
    TechCluster --> Market
    EnergyCluster --> Market

C. Quasi-Diagonalization

The covariance matrix is reordered based on the hierarchical tree, exposing block-diagonal risk structures.

D. Recursive Bisection

Weights are allocated recursively through the tree:

𝛼
=
1
−
𝑉
𝑎
𝑟
𝑙
𝑒
𝑓
𝑡
𝑉
𝑎
𝑟
𝑙
𝑒
𝑓
𝑡
+
𝑉
𝑎
𝑟
𝑟
𝑖
𝑔
ℎ
𝑡
α=1−
Var
left
	​

+Var
right
	​

Var
left
	​

	​


This avoids covariance inversion entirely, providing numerical stability and robust diversification.

5. Visual Frontend (TradingView-Inspired)

A dark-mode professional dashboard built with Streamlit and Plotly provides:

Universe selection

ESG filtering controls

HRP allocation visualization

ESG audit tables

Real-time model explanations

Screenshots can be added in docs/images/.

6. Installation & Usage Guide
Prerequisites

Docker Desktop

Python 3.11

(Optional) Ollama for local AI inference:

ollama run llama3

Step 1. Clone Repository
git clone https://github.com/YOUR_USERNAME/Veritas-Quant-ESG-Engine.git
cd Veritas-Quant-ESG-Engine


Create environment file:

Windows

copy deployment\.env.example .env


Linux/Mac

cp deployment/.env.example .env

Step 2. Start Infrastructure
docker compose up --build -d

Step 3. Run Autonomous ESG Pipeline
make pipeline


Or:

py -m scripts.run_esg_pipeline

Step 4. Launch the Platform

Backend:

make api


Frontend:

make ui

7. Project Structure
Veritas-Quant/
├── config/
│   ├── esg_criteria.json
│   └── settings.py
│
├── src/
│   ├── collector/
│   │   ├── scraper.py
│   │   ├── llm_analyzer.py
│   │   └── loader.py
│   │
│   ├── engine/
│   │   ├── hrp_optimizer.py
│   │   ├── db_manager.py
│   │   ├── api_server.py
│   │   └── utils.py
│
├── deployment/
│   ├── docker-compose.yml
│   └── Dockerfile
│
├── scripts/
│   └── run_esg_pipeline.py
│
├── app.py
└── Makefile

8. Continuous Integration

GitHub Actions ensure:

Static typing via MyPy

Linting via Ruff

Unit tests via Pytest

Security scanning for Python dependencies

9. License

Distributed under the MIT License.