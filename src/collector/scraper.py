import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Optional
from duckduckgo_search import DDGS # pip install duckduckgo-search

class SustainabilityScraper:
    """
    Agent autonome capable de :
    1. Chercher le rapport ESG d'une entreprise sur le web.
    2. Extraire le contenu textuel de la page trouvée.
    """

    def find_esg_url(self, ticker: str) -> str:
        """
        Utilise DuckDuckGo pour trouver l'URL du dernier rapport ESG.
        """
        query = f"{ticker} company sustainability report 2024 summary"
        print(f"[Agent] Recherche automatique pour : '{query}'...")

        try:
            # Utilisation du context manager pour DDGS
            with DDGS() as ddgs:
                # On force le cast en list pour récupérer les résultats
                results = list(ddgs.text(query, max_results=3))
                
            if results:
                # Le premier résultat est souvent le bon
                best_url = results[0]['href']
                print(f" URL Trouvée : {best_url}")
                return best_url
            else:
                print("Aucun résultat trouvé.")
                return ""
        except Exception as e:
            print(f"  Erreur de recherche : {e}")
            return ""

    # CORRECTION ICI : On utilise Optional[str] car la valeur par défaut est None
    def fetch_company_data(self, ticker: str, url: Optional[str] = None) -> str:
        """
        Logique principale : Cherche l'URL si nécessaire, puis scrape.
        """
        # 1. RECHERCHE AUTOMATIQUE
        # Si l'URL n'est pas fournie, on la cherche
        target_url = url
        if not target_url:
            target_url = self.find_esg_url(ticker)
        
        # Si après recherche on a toujours rien, on arrête
        if not target_url:
            return "Error: Auto-discovery failed. No URL found."

        # 2. SCRAPING (Lecture de la page)
        print(f"[Scraper] Lecture de {target_url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            time.sleep(random.uniform(1, 3)) # Pause anti-ban
            
            response = requests.get(target_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"Error: Access denied (HTTP {response.status_code}). Site protected."

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Stratégie d'extraction large
            text_blocks = []
            for tag in soup.find_all(['p', 'h2', 'h3', 'li']):
                txt = tag.get_text(strip=True)
                if len(txt) > 30:
                    text_blocks.append(txt)
            
            full_text = " ".join(text_blocks)
            
            if len(full_text) < 200:
                return "Error: Page content seems empty (Javascript required?)."
                
            print(f"  Extrait {len(full_text)} caractères.")
            return full_text[:12000] # Limite pour l'IA

        except Exception as e:
            return f"Error scraping: {str(e)}"