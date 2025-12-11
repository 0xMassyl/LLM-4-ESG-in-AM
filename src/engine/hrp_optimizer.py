import pandas as pd
import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform

class HRPOptimizer:
    """
    Hierarchical Risk Parity (HRP) implementation.
    Based on Lopez de Prado (2016), "Building Diversified Portfolios".

    Steps:
    1. Compute distance matrix from correlations
    2. Perform hierarchical clustering
    3. Quasi-diagonalize the covariance matrix
    4. Allocate capital recursively using cluster variances
    """

    def __init__(self, returns: pd.DataFrame):
        self.returns = returns
        self.tickers = returns.columns.tolist()

        # Precompute covariance and correlation matrices
        self.cov = returns.cov()
        self.corr = returns.corr()

    def optimize(self) -> pd.Series:
        """
        Executes the full HRP optimization pipeline.
        Returns normalized weights (sum = 1).
        """
        # 1. Distance matrix used for clustering
        dist = np.sqrt(0.5 * (1 - self.corr))
        dist_condensed = squareform(dist, checks=False)
        linkage = sch.linkage(dist_condensed, method="single")

        # 2. Quasi-diagonal ordering of assets
        sort_ix = self._get_quasi_diag(linkage)
        sort_ix = self.corr.index[sort_ix].tolist()

        # 3. Reorder covariance according to clustering structure
        df_cov = self.cov.loc[sort_ix, sort_ix]

        # 4. Recursive bisection (top-down allocation)
        weights = pd.Series(1.0, index=sort_ix)
        weights = self._get_rec_bisection(weights, df_cov, sort_ix)

        return weights.sort_index()

    def _get_quasi_diag(self, linkage: np.ndarray) -> list:
        """
        Rearranges the hierarchical tree so similar assets appear adjacent.
        Produces the ordering used for recursive bisection.
        """
        linkage = linkage.astype(int)
        sort_ix = pd.Series([linkage[-1, 0], linkage[-1, 1]])
        num_items = linkage[-1, 3]

        while sort_ix.max() >= num_items:
            # Expand index to insert children in correct order
            sort_ix.index = pd.Index(range(0, sort_ix.shape[0] * 2, 2))

            # Identify cluster nodes (values >= num_items)
            clusters = sort_ix[sort_ix >= num_items]
            idx = clusters.index
            loc = clusters.values - num_items

            # Replace cluster node with its left child
            sort_ix[idx] = linkage[loc, 0]

            # Add right child
            new_right = pd.Series(linkage[loc, 1], index=idx + 1)
            sort_ix = pd.concat([sort_ix, new_right]).sort_index()

            # Ensure continuous indexing
            sort_ix.index = pd.Index(range(len(sort_ix)))

        return sort_ix.tolist()

    def _get_cluster_var(self, cov: pd.DataFrame, c_items: list) -> float:
        """
        Computes the variance of a cluster using the Inverse Variance Portfolio (IVP).
        Formula: w = 1/diag(Cov), normalized; var = w' * Cov * w
        """
        cov_slice = cov.loc[c_items, c_items]
        inv_diag = 1 / np.diag(cov_slice)
        weights = inv_diag / np.sum(inv_diag)
        return float(np.dot(weights, np.dot(cov_slice, weights)))

    def _get_rec_bisection(self, weights: pd.Series, cov: pd.DataFrame, sort_ix: list) -> pd.Series:
        """
        Recursively allocates capital between clusters.
        Higher-variance clusters receive lower allocations.
        """
        w = weights.copy()
        clusters = [sort_ix]

        while len(clusters) > 0:
            # Only continue splitting clusters with 2+ items
            clusters = [c for c in clusters if len(c) >= 2]

            for c in clusters:
                half = len(c) // 2
                left = c[:half]
                right = c[half:]

                # Compute cluster variances
                var_left = self._get_cluster_var(cov, left)
                var_right = self._get_cluster_var(cov, right)

                # Allocation factor (alpha)
                alpha = 1 - var_left / (var_left + var_right)

                # Apply weights
                w[left] *= alpha
                w[right] *= (1 - alpha)

            # Prepare next recursion level
            new_level = []
            for c in clusters:
                half = len(c) // 2
                if len(c) > 1:
                    new_level.append(c[:half])
                    new_level.append(c[half:])
            clusters = new_level

        return w
