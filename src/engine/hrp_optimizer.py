import pandas as pd
import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


class HRPOptimizer:
    """
    Implements the Hierarchical Risk Parity (HRP) portfolio allocation method.
    
    HRP is designed to fix the main weaknesses of classical Markowitz
    (especially the unstable inverse covariance matrix). Instead of inverting
    anything, HRP uses:
        - hierarchical clustering
        - ordering of assets based on cluster distance
        - recursive risk splitting
    
    This produces allocations that are much more stable in practice,
    especially when assets are correlated.
    Reference: Lopez de Prado (2016).
    """

    def __init__(self, returns: pd.DataFrame):
        # Store historical returns and basic risk matrices
        self.returns = returns
        self.tickers = returns.columns.tolist()

        # Compute covariance and correlation matrices directly from returns
        self.cov_matrix = returns.cov()
        self.corr_matrix = returns.corr()

    def optimize(self) -> pd.Series:
        """
        Full HRP allocation pipeline.
        Steps:
          1. Build a clustering tree from correlations
          2. Sort assets according to the hierarchy (quasi-diagonalization)
          3. Allocate weights recursively based on cluster variances
        
        Returns:
            pd.Series of weights summing to 1.0
        """

        # Step 1: hierarchical clustering structure
        linkage_matrix = self._get_linkage_matrix()

        # Step 2: order assets following the tree
        sorted_indices = self._get_quasi_diag(linkage_matrix)

        # Reorder covariance matrix accordingly
        sorted_cov = self.cov_matrix.iloc[sorted_indices, sorted_indices]

        # Step 3: hierarchical allocation using recursive bisection
        hrp_weights = self._get_rec_bisection(sorted_cov, sorted_indices)

        # Convert to Series aligned with original tickers
        return pd.Series(hrp_weights, index=self.tickers).sort_index()

    def _get_linkage_matrix(self):
        """
        Converts the correlation matrix to a distance matrix and applies
        hierarchical clustering.

        HRP uses a specific correlation-to-distance transformation:
            d = sqrt(0.5 * (1 - correlation))
        """

        dist = np.sqrt(0.5 * (1 - self.corr_matrix))
        dist_condensed = squareform(dist, checks=False)  # required by SciPy
        linkage = sch.linkage(dist_condensed, method="ward")

        return linkage

    def _get_quasi_diag(self, linkage: np.ndarray) -> list[int]:
        """
        Orders assets so that similar ones appear next to each other.
        This makes the covariance matrix take a block structure, which is
        what enables HRP’s recursive splitting logic.
        """

        linkage = linkage.astype(int)

        # Start from the last merge in the linkage tree
        sort_ix = pd.Series([linkage[-1, 0], linkage[-1, 1]])
        num_items = linkage[-1, 3]  # original number of assets

        # Expand cluster indexes into actual asset indexes
        while sort_ix.max() >= num_items:

            # Prepare room to insert child nodes
            sort_ix.index = pd.Index(range(0, sort_ix.shape[0] * 2, 2))

            # Select items representing clusters (not leaf nodes)
            df0 = sort_ix[sort_ix >= num_items]
            i = df0.index
            j = df0.values - num_items

            # Replace cluster code with its left child
            sort_ix[i] = linkage[j, 0]

            # Insert right child
            df0 = pd.Series(linkage[j, 1], index=i + 1)

            # Merge and reindex cleanly
            sort_ix = pd.concat([sort_ix, df0]).sort_index()
            sort_ix.index = pd.Index(range(len(sort_ix)))

        return sort_ix.tolist()

    def _get_cluster_var(self, cov: pd.DataFrame, c_items: list[int]) -> float:
        """
        Computes the variance of a cluster using an Inverse Variance Portfolio (IVP).
        
        IVP logic:
            - assets with lower individual variance get higher weights
            - avoids inverting any matrix, which keeps the method stable
        """

        cov_slice = cov.iloc[c_items, c_items]

        # Compute IVP weights
        inv_diag = 1 / np.diag(cov_slice)
        weights = inv_diag / np.sum(inv_diag)

        # Cluster variance = w' Σ w
        return np.dot(np.dot(weights, cov_slice), weights)

    def _get_rec_bisection(self, sorted_cov: pd.DataFrame, sort_ix: list[int]) -> pd.Series:
        """
        Performs HRP's recursive allocation.
        At each step:
            - split cluster into left/right halves
            - compute each side’s variance
            - allocate less weight to the riskier side
        
        This mirrors how risk is naturally diversified across clusters.
        """

        # Initialize all assets with equal weight
        weights = pd.Series(1.0, index=sort_ix)

        # Begin with the entire set as the root cluster
        cluster_items = [sort_ix]

        while len(cluster_items) > 0:

            # Only clusters that can still be divided
            cluster_items = [cl for cl in cluster_items if len(cl) >= 2]

            for cluster in cluster_items:

                half = len(cluster) // 2
                left = cluster[:half]
                right = cluster[half:]

                # Compute variance of both halves
                left_var = self._get_cluster_var(sorted_cov, left)
                right_var = self._get_cluster_var(sorted_cov, right)

                # Allocation factor:
                # if left cluster has higher variance, alpha becomes smaller
                alpha = 1 - left_var / (left_var + right_var)

                # Apply allocation down the branch
                weights[left] *= alpha
                weights[right] *= 1 - alpha

            # Prepare next recursion level
            new_clusters = []
            for cluster in cluster_items:
                half = len(cluster) // 2
                if len(cluster) > 1:
                    new_clusters.append(cluster[:half])
                    new_clusters.append(cluster[half:])
            cluster_items = new_clusters

        return weights
