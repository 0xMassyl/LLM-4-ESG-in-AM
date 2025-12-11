from src.engine.db_manager import get_latest_scores
import pandas as pd

def check_database():
    print("--- DATABASE INSPECTION ---")
    
    try:
        # Fetches the latest ESG scores using the same function the API relies on.
        scores = get_latest_scores()
        
        # Handles the case where the database returns nothing or an empty dictionary.
        if not scores:
            print("The database is empty (an empty dictionary was returned).")
            print("Run 'py -m scripts.run_esg_pipeline' to populate it.")
            return

        # Displays how many companies were retrieved.
        print(f"{len(scores)} companies found in the database.")
        
        print("\n--- SCORE DETAILS ---")
        # Converts the dictionary into a DataFrame for clearer, structured display.
        df = pd.DataFrame(list(scores.items()), columns=["Ticker", "Score"])
        print(df.to_string(index=False))
        
        print("\n--- ANALYSIS ---")
        # Minimal integrity check: ensures a key ticker expected elsewhere is present.
        if "GOOGL" not in scores:
            print("Warning: GOOGL is missing (it will default to 50).")
        else:
            # If present, confirms its score.
            print(f"GOOGL is present with a score of {scores['GOOGL']}.")

    except Exception as e:
        # Catches database connection issues or any unexpected failure.
        print(f"Connection error: {e}")
        print("Check that Docker is running with 'docker ps'.")

# Allows the script to be executed directly for debugging or manual inspection.
if __name__ == "__main__":
    check_database()
