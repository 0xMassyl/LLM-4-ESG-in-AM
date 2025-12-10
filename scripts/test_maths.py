import pandas as pd
import numpy as np
from src.engine.hrp_optimizer import HRPOptimizer

def test_hrp():
    print("--- 🧮 TEST UNITAIRE DU MOTEUR HRP ---")
    
    # 1. Génération de données synthétiques corrélées
    # Actif A et B très corrélés, C décorrélé et volatil
    np.random.seed(42)
    n = 1000
    
    a = np.random.normal(0, 0.01, n)
    b = a + np.random.normal(0, 0.002, n) # B suit A de très près
    c = np.random.normal(0, 0.02, n)      # C est indépendant et plus risqué
    
    returns = pd.DataFrame({'A': a, 'B': b, 'C': c})
    
    print("Corrélation des actifs (A et B doivent être proches de 1) :")
    print(returns.corr().round(2))
    
    # 2. Lancement de l'optimiseur
    optimizer = HRPOptimizer(returns)
    weights = optimizer.optimize()
    
    print("\n--- 🏆 RÉSULTAT HRP (Poids) ---")
    print(weights.apply(lambda x: f"{x:.2%}"))
    
    # 3. Vérification Logique
    # HRP devrait traiter (A+B) comme un cluster et C comme un autre.
    # C est très volatil, donc il devrait avoir moins de poids que le cluster (A+B).
    # Mais dans le cluster (A+B), A et B devraient se partager le risque.
    
    print("\n✅ Si les poids sont différents de 33.33%, le moteur marche.")

if __name__ == "__main__":
    test_hrp() # Correction ici : appel de la bonne fonction