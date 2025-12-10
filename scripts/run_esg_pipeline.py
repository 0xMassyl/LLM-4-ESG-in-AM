from src.engine.db_manager import init_db, save_score
from src.collector.scraper import SustainabilityScraper
from src.collector.llm_analyzer import ESGAnalyzer

def main():
    print("Démarrage de l'Agent Autonome ESG")
    
    # 1. Initialisation des services
    print("1. Initialisation de la Base de Données et des Agents...")
    init_db()
    scraper = SustainabilityScraper()
    analyzer = ESGAnalyzer()
    
    # 2. LISTE DE CIBLES (Mode "Agent Autonome")
    # Plus besoin de chercher les PDF manuellement. Donnez juste le nom.
    tickers_to_scan = [
        "TSLA",  # Tesla
        "XOM",   # Exxon Mobil
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "BP",    # BP
        "SHEL",  # Shell
        "NVDA"   # Nvidia
    ]
    
    print(f" Cibles identifiées : {len(tickers_to_scan)} entreprises")
    
    # 3. Exécution de la boucle d'ingestion
    for ticker in tickers_to_scan:
        print(f"\n [Agent] Traitement pour : {ticker}")
        
        # A. COLLECTE INTELLIGENTE
        # On passe url=None, ce qui force le scraper à utiliser DuckDuckGo
        # pour trouver le dernier rapport ESG disponible.
        text_content = scraper.fetch_company_data(ticker, url=None)
        
        # Gestion des échecs (Site protégé, pas de résultat, etc.)
        if text_content.startswith("Error"):
            print(f" Échec collecte : {text_content}")
            # On log l'échec en base pour garder une trace (Score 50 = Neutre/Inconnu)
            save_score(ticker, 50.0, f"Data collection failed: {text_content}", source="Auto-Search")
            continue
        
        # B. ANALYSE IA (Cerveau)
        # L'IA lit le texte trouvé et attribue un score
        analysis = analyzer.analyze_document(ticker, text_content)
        
        score = analysis.get("esg_score", 50)
        rationale = analysis.get("rationale", "N/A")
        status = analysis.get("status", "unknown")
        
        print(f"  Score IA ({status}) : {score}/100")
        print(f"   Avis : {rationale[:100]}...")
        
        # C. SAUVEGARDE (Gouvernance)
        save_score(ticker, score, rationale, source="Auto-Search Web")

    print("\nMission terminée. La base de données ESG est à jour.")

if __name__ == "__main__":
    main()