from src.engine.db_manager import init_db, save_score
from src.collector.scraper import SustainabilityScraper
from src.collector.llm_analyzer import ESGAnalyzer

def main():
    print("Starting ESG Autonomous Agent")
    
    # Initializing database and core components required for ingestion.
    print("1. Initializing database and service agents...")
    init_db()
    scraper = SustainabilityScraper()
    analyzer = ESGAnalyzer()
    
    # Target list used by the autonomous mode.
    # The scraper identifies the latest ESG report through a search-based approach.
    tickers_to_scan = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "XOM", "CVX", "PEP", "KO", "JNJ", "NVDA",
        # Ajouts recommandés pour les hauts scores ESG
        "UNH", "PG", "NSRGY", "ORAN", "VOD"
    ]
    
    print(f" Identified targets: {len(tickers_to_scan)} companies")
    
    # Main ingestion workflow. Each ticker is processed independently for better traceability.
    for ticker in tickers_to_scan:
        print(f"\n [Agent] Processing: {ticker}")
        
        # Fetches ESG-related text content. url=None forces the scraper to search online.
        text_content = scraper.fetch_company_data(ticker, url=None)
        
        # Logs collection failures and stores a neutral score for transparency.
        if isinstance(text_content, str) and text_content.startswith("Error"):
            print(f" Collection failed: {text_content}")
            save_score(
                ticker,
                50.0,  # Neutral fallback score when no analysis can be performed.
                f"Data collection failed: {text_content}",
                source="Auto-Search"
            )
            continue
        
        # Runs LLM-based ESG scoring on extracted text content.
        analysis = analyzer.analyze_document(ticker, text_content)
        
        # Extracts fields safely in case of partial or unexpected responses.
        score = analysis.get("esg_score", 50)
        rationale = analysis.get("rationale", "N/A")
        status = analysis.get("status", "unknown")
        
        print(f"  AI score ({status}): {score}/100")
        print(f"   Rationale preview: {rationale[:100]}...")
        
        # Saves ESG score and qualitative insights for downstream evaluation.
        save_score(ticker, score, rationale, source="Auto-Search Web")

    print("\n Mission complete. ESG database updated.")

if __name__ == "__main__":
    main()
