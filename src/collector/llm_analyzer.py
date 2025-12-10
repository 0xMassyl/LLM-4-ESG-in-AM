import json
import random
from typing import Dict, Any, Optional
from openai import OpenAI, APIConnectionError
from config.settings import get_settings

settings = get_settings()

class ESGAnalyzer:
    """
    Analyseur ESG Hybride.
    - Si une clé OpenAI est présente -> Utilise GPT-3.5/4 (Payant, Cloud)
    - Sinon -> Utilise OLLAMA (Llama 3) (Gratuit, Local)
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        
        # Configuration dynamique du client
        if self.api_key and self.api_key.startswith("sk-"):
            print("🚀 [IA] Mode: OpenAI Cloud (GPT)")
            self.client = OpenAI(api_key=self.api_key)
            self.model = "gpt-3.5-turbo"
        else:
            print("🏠 [IA] Mode: Local Inference (Ollama/Llama3)")
            # On pointe vers le serveur local Ollama qui imite l'API OpenAI
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" # Clé bidon requise par la lib mais ignorée par Ollama
            )
            self.model = "llama3" 

    def analyze_document(self, ticker: str, text_content: str) -> Dict[str, Any]:
        """
        Envoie le texte à l'IA (Locale ou Cloud).
        """
        # Sécurité : Si texte trop court ou erreur de scraping
        if len(text_content) < 200 or "Error" in text_content[:20]:
            print(f"⚠️ [IA] Texte insuffisant pour {ticker}. Passage en Mock.")
            return self._mock_analysis(ticker)

        try:
            print(f"🧠 [IA] Analyse de {ticker} avec {self.model}...")
            
            # Prompt optimisé pour Llama 3 (qui aime les instructions strictes)
            prompt = f"""
            Role: Expert ESG Analyst.
            Task: Analyze the following text from {ticker}'s sustainability report.
            
            TEXT START:
            {text_content[:3500]}
            TEXT END.
            
            Output strictly a JSON object with this format:
            {{
                "score": <int 0-100>,
                "rationale": "<string max 20 words>"
            }}
            Do not write anything else.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, # Très factuel
            )
            
            content = response.choices[0].message.content
            
            if content is None:
                raise ValueError("Réponse vide de l'IA")

            # Nettoyage si le modèle local est bavard (parfois Llama ajoute du texte autour)
            clean_content = content.strip()
            if "```json" in clean_content:
                clean_content = clean_content.split("```json")[1].split("```")[0]
            elif "```" in clean_content:
                clean_content = clean_content.split("```")[1].split("```")[0]

            result = json.loads(clean_content.strip())
            
            return {
                "ticker": ticker,
                "esg_score": result.get("score", 50),
                "rationale": result.get("rationale", "AI Analysis successful."),
                "status": f"real_ai_{self.model}"
            }

        except APIConnectionError:
            print(f"❌ [IA] Impossible de se connecter à Ollama sur http://localhost:11434.")
            print("👉 AVEZ-VOUS LANCÉ 'ollama run llama3' DANS UN TERMINAL ?")
            return self._mock_analysis(ticker)
            
        except Exception as e:
            print(f"❌ [IA] Erreur ({self.model}): {e}")
            return self._mock_analysis(ticker)

    def _mock_analysis(self, ticker: str) -> Dict[str, Any]:
        """Simulation ultime si tout échoue."""
        return {
            "ticker": ticker,
            "esg_score": random.randint(40, 90),
            "rationale": "Mode DÉMO (Ollama éteint ou erreur parsing).",
            "status": "mock"
        }