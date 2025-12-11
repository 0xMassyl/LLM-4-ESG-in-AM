from src.engine.db_manager import get_latest_scores
import pandas as pd

def check_database():
    print("--- 🕵️‍♂️ INSPECTION DE LA BASE DE DONNÉES ---")
    
    try:
        # On appelle la fonction que l'API utilise
        scores = get_latest_scores()
        
        if not scores:
            print("❌ LA BASE EST VIDE ! (Dictionnaire vide retourné)")
            print("👉 Lancez 'py -m scripts.run_esg_pipeline' pour la remplir.")
            return

        print(f"✅ {len(scores)} entreprises trouvées en base.")
        
        # Affichage propre
        print("\n--- DÉTAIL DES SCORES ---")
        df = pd.DataFrame(list(scores.items()), columns=["Ticker", "Score"])
        print(df.to_string(index=False))
        
        # Analyse rapide
        print("\n--- ANALYSE ---")
        if "GOOGL" not in scores:
            print("⚠️ ATTENTION : GOOGL manque à l'appel (il sera à 50 par défaut).")
        else:
            print(f"👍 GOOGL est présent avec un score de {scores['GOOGL']}.")

    except Exception as e:
        print(f"💥 Erreur de connexion : {e}")
        print("👉 Vérifiez que Docker tourne : 'docker ps'")

if __name__ == "__main__":
    check_database()

