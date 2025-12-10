import json
import random
from typing import Dict, Any
from openai import OpenAI, APIConnectionError
from config.settings import get_settings

settings = get_settings()

class ESGAnalyzer:
    """
    Hybrid ESG analyzer.
    - Uses OpenAI (GPT models) when an API key is available.
    - Falls back to local inference (Ollama with Llama 3) when no key is provided.
    
    The design ensures the application remains functional even without cloud access.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        
        # Dynamically selects cloud or local inference depending on the API key.
        if self.api_key and self.api_key.startswith("sk-"):
            print("[AI] Mode: OpenAI Cloud (GPT)")
            self.client = OpenAI(api_key=self.api_key)
            self.model = "gpt-3.5-turbo"
        else:
            print("[AI] Mode: Local Inference (Ollama/Llama3)")
            # Points to a local Ollama server emulating the OpenAI API interface.
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"  # Dummy key required by the client library.
            )
            self.model = "llama3"

    def analyze_document(self, ticker: str, text_content: str) -> Dict[str, Any]:
        """
        Sends ESG-related text to the selected LLM (cloud or local).
        Automatically falls back to a mock analysis when data is insufficient.
        """
        if len(text_content) < 200 or "Error" in text_content[:20]:
            print(f"[AI] Insufficient text for {ticker}. Switching to mock analysis.")
            return self._mock_analysis(ticker)

        try:
            print(f"[AI] Analyzing {ticker} with model '{self.model}'")
            
            # Strict JSON output request to simplify downstream parsing.
            prompt = f"""
            Role: Expert ESG Analyst.
            Task: Analyze the following text from {ticker}'s sustainability report.

            TEXT START:
            {text_content[:3500]}
            TEXT END.

            Return only a JSON object in this format:
            {{
                "score": <int 0-100>,
                "rationale": "<string max 20 words>"
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for deterministic outputs.
            )
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from the AI model")

            clean_content = content.strip()

            # Removes surrounding formatting occasionally added by local models.
            if "```json" in clean_content:
                clean_content = clean_content.split("```json")[1].split("```")[0]
            elif "```" in clean_content:
                clean_content = clean_content.split("```")[1].split("```")[0]

            result = json.loads(clean_content.strip())

            return {
                "ticker": ticker,
                "esg_score": result.get("score", 50),
                "rationale": result.get("rationale", "AI analysis completed."),
                "status": f"real_ai_{self.model}"
            }

        except APIConnectionError:
            print("[AI] Connection to local Ollama server failed.")
            print("Ensure that 'ollama run llama3' is running in a terminal.")
            return self._mock_analysis(ticker)

        except Exception as e:
            print(f"[AI] Error from model '{self.model}': {e}")
            return self._mock_analysis(ticker)

    def _mock_analysis(self, ticker: str) -> Dict[str, Any]:
        """
        Backup mode used when inference fails. Ensures the pipeline remains operational.
        """
        return {
            "ticker": ticker,
            "esg_score": random.randint(40, 90),
            "rationale": "Fallback mode active (local model unavailable or parsing error).",
            "status": "mock"
        }
