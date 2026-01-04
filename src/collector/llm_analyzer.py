# -------------------------------------------------
# Standard library imports
# -------------------------------------------------
import json
import random
from typing import Dict, Any

# -------------------------------------------------
# OpenAI-compatible client
# Works both with OpenAI cloud and local Ollama server
# -------------------------------------------------
from openai import OpenAI, APIConnectionError

# -------------------------------------------------
# Project configuration loader
# -------------------------------------------------
from config.settings import get_settings

# Load application settings (API keys, environment config)
settings = get_settings()


class ESGAnalyzer:
    """
    ESG text analyzer.

    Important clarification:
    - This class does NOT compute a true ESG score.
    - It produces a qualitative proxy based on text analysis.
    - It is designed to be resilient, not academically perfect.

    Design choice:
    - Cloud LLM when API key is available
    - Local LLM fallback when offline
    """

    def __init__(self):
        # Retrieve API key from environment/settings
        self.api_key = settings.OPENAI_API_KEY

        # Decide inference mode based on API key presence
        # This allows the app to run:
        # - with OpenAI cloud
        # - with a local Ollama server
        # - with no external connectivity
        if self.api_key and self.api_key.startswith("sk-"):
            print("[AI] Mode: OpenAI Cloud (GPT)")

            # Initialize OpenAI client for cloud usage
            self.client = OpenAI(api_key=self.api_key)

            # Explicitly select a lightweight and cheap model
            self.model = "gpt-3.5-turbo"

        else:
            print("[AI] Mode: Local Inference (Ollama/Llama3)")

            # Connect to a local Ollama server.
            # Ollama exposes an OpenAI-compatible API.
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",

                # A dummy key is still required by the SDK
                api_key="ollama"
            )

            # Model name must match the locally available model
            self.model = "llama3"

    def analyze_document(self, ticker: str, text_content: str) -> Dict[str, Any]:
        """
        Main ESG analysis method.

        Workflow:
        1. Validate input text
        2. Send text to selected LLM
        3. Parse structured JSON output
        4. Fallback to mock result on failure
        """

        # Early exit if text is too short or already an error message.
        # Sending garbage to an LLM produces garbage outputs.
        if len(text_content) < 200 or "Error" in text_content[:20]:
            print(f"[AI] Insufficient text for {ticker}. Switching to mock analysis.")
            return self._mock_analysis(ticker)

        try:
            print(f"[AI] Analyzing {ticker} with model '{self.model}'")

            # Prompt is explicitly constrained.
            # Why:
            # - reduces hallucinations
            # - simplifies JSON parsing
            # - avoids verbose outputs
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

            # Call the LLM using the chat completion API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],

                # Low temperature ensures repeatability and stability.
                temperature=0.1,
            )

            # Extract text content from model response
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from the AI model")

            # Normalize output formatting
            clean_content = content.strip()

            # Local models sometimes wrap JSON in markdown code blocks.
            # This logic removes those wrappers safely.
            if "```json" in clean_content:
                clean_content = clean_content.split("```json")[1].split("```")[0]
            elif "```" in clean_content:
                clean_content = clean_content.split("```")[1].split("```")[0]

            # Parse JSON output
            result = json.loads(clean_content.strip())

            # Return normalized result for downstream processing
            return {
                "ticker": ticker,

                # Default to 50 if model output is malformed
                "esg_score": result.get("score", 50),

                "rationale": result.get(
                    "rationale",
                    "AI analysis completed."
                ),

                # Status flag used for auditability
                "status": f"real_ai_{self.model}"
            }

        except APIConnectionError:
            # Specific handling for local inference failures.
            # Common when Ollama server is not running.
            print("[AI] Connection to local Ollama server failed.")
            print("Ensure that 'ollama run llama3' is running.")

            return self._mock_analysis(ticker)

        except Exception as e:
            # Catch-all for:
            # - malformed JSON
            # - unexpected model output
            # - SDK errors
            print(f"[AI] Error from model '{self.model}': {e}")
            return self._mock_analysis(ticker)

    def _mock_analysis(self, ticker: str) -> Dict[str, Any]:
        """
        Backup analysis mode.

        Purpose:
        - keep the ESG pipeline running
        - avoid hard crashes
        - make demo mode explicit

        Important:
        - this output is NOT a real ESG score
        """
        return {
            "ticker": ticker,

            # Random score to simulate variability
            "esg_score": random.randint(40, 90),

            "rationale": (
                "Fallback mode active "
                "(local model unavailable or parsing error)."
            ),

            # Explicit status flag for transparency
            "status": "mock"
        }
