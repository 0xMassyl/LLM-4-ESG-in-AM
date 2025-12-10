import pandas as pd
import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform

class HRPOptimizer:
    """
    Hierarchical Risk Parity (HRP) Implementation.
    Source: Lopez de Prado, M. (2016). Building Diversified Portfolios.
    """

    def __init__(self, returns: pd.DataFrame):
        self.returns = returns
        self.tickers = returns.columns.tolist()
        # Calcul de la matrice de covariance et corrélation
        self.cov = returns.cov()
        self.corr = returns.corr()

    def optimize(self) -> pd.Series:
        """
        Exécute l'optimisation HRP complète.
        """
        # 1. Clustering (Tree Structure)
        # On calcule la distance : d = sqrt(0.5 * (1 - rho))
        dist = np.sqrt(0.5 * (1 - self.corr))
        dist_condensed = squareform(dist, checks=False)
        linkage = sch.linkage(dist_condensed, 'single')

        # 2. Quasi-Diagonalisation (Tri des actifs)
        sort_ix = self._get_quasi_diag(linkage)
        sort_ix = self.corr.index[sort_ix].tolist() # Récupère les noms des tickers triés

        # 3. Réorganisation de la covariance selon le cluster
        df_cov = self.cov.loc[sort_ix, sort_ix]

        # 4. Recursive Bisection (Allocation)
        # On initialise les poids à 1.0
        weights = pd.Series(1.0, index=sort_ix)
        weights = self._get_rec_bisection(weights, df_cov, sort_ix)

        # Vérification finale : Somme = 1.0
        return weights.sort_index()

    def _get_quasi_diag(self, linkage: np.ndarray) -> list:
        """
        Trie les éléments du cluster pour que les actifs similaires soient adjacents.
        """
        linkage = linkage.astype(int)
        sort_ix = pd.Series([linkage[-1, 0], linkage[-1, 1]])
        num_items = linkage[-1, 3] # Nombre total d'éléments originaux

        while sort_ix.max() >= num_items:
            # Replace clusters with their children
            # FIX: Conversion explicite en pd.Index pour satisfaire Pylance
            sort_ix.index = pd.Index(range(0, sort_ix.shape[0] * 2, 2)) # Make space
            df0 = sort_ix[sort_ix >= num_items] # Clusters
            i = df0.index
            j = df0.values - num_items
            sort_ix[i] = linkage[j, 0] # Left child
            df0 = pd.Series(linkage[j, 1], index=i + 1) # Right child
            sort_ix = pd.concat([sort_ix, df0]).sort_index() # Re-merge
            # FIX: Conversion explicite en pd.Index
            sort_ix.index = pd.Index(range(len(sort_ix))) # Re-index

        return sort_ix.tolist()

    def _get_cluster_var(self, cov: pd.DataFrame, c_items: list) -> float:
        """
        Calcule la variance d'un cluster en utilisant l'Inverse Variance Portfolio (IVP).
        """
        cov_slice = cov.loc[c_items, c_items]
        # Poids IVP intra-cluster = 1 / diag(cov)
        inv_diag = 1 / np.diag(cov_slice)
        weights = inv_diag / np.sum(inv_diag)
        
        # Variance du cluster = w' * Cov * w
        return np.dot(np.dot(weights, cov_slice), weights)

    def _get_rec_bisection(self, weights: pd.Series, cov: pd.DataFrame, sort_ix: list) -> pd.Series:
        """
        Allocation récursive du capital (Top-Down).
        """
        w = weights.copy()
        c_items = [sort_ix] # Liste de listes (clusters)

        while len(c_items) > 0:
            # On découpe les clusters en 2 tant qu'ils contiennent plus d'1 actif
            c_items = [i for i in c_items if len(i) >= 2]
            
            for i in range(0, len(c_items), 2):
                c_items0 = c_items[i] # Cluster complet
                
                # Coupe en deux
                half = len(c_items0) // 2
                c_items1 = c_items0[:half] # Gauche
                c_items2 = c_items0[half:] # Droite
                
                # Calcul des variances des sous-clusters
                var1 = self._get_cluster_var(cov, c_items1)
                var2 = self._get_cluster_var(cov, c_items2)
                
                # Facteur d'allocation (Alpha)
                alpha = 1 - var1 / (var1 + var2)
                
                # Application des poids
                w[c_items1] *= alpha
                w[c_items2] *= 1 - alpha
                
            # Préparation niveau suivant
            new_c_items = []
            for item in c_items:
                half = len(item) // 2
                if len(item) > 1:
                    new_c_items.append(item[:half])
                    new_c_items.append(item[half:])
            c_items = new_c_items
            
        return w