import pandas as pd
import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


class HRPOptimizer:
    """
    Implementation of the Hierarchical Risk Parity (HRP) allocation algorithm.

    HRP avoids the instability of classical Markowitz optimization by:
        - building a hierarchical clustering tree based on correlations,
        - reordering assets according to the tree structure,
        - allocating capital recursively across cluster splits.

    This produces more stable and interpretable weights, particularly when
    asset correlations are high.
    Reference: Lopez de Prado (2016).
    """

    def __init__(self, returns: pd.DataFrame):
        """
        Initializes the optimizer with historical returns and computes
        covariance and correlation matrices used throughout the pipeline.
        """
        self.returns = returns
        self.tickers = returns.columns.tolist()

        # Core risk matrices
        self.cov_matrix = returns.cov()
        self.corr_matrix = returns.corr()

    def optimize(self) -> pd.Series:
        """
        Executes the full HRP workflow:
            1. Build hierarchical clustering from correlations.
            2. Apply quasi-diagonalization to reorder assets.
            3. Run recursive bisection to allocate cluster-based weights.

        Returns:
            weights (pd.Series): Allocation weights summing to 1.0
        """
        linkage_matrix = self._get_linkage_matrix()
        sorted_indices = self._get_quasi_diag(linkage_matrix)

        # Reorder covariance matrix according to hierarchical structure
        sorted_cov = self.cov_matrix.iloc[sorted_indices, sorted_indices]

        hrp_weights = self._get_rec_bisection(sorted_cov, sorted_indices)

        # Final weights aligned to original column names
        return pd.Series(hrp_weights, index=self.tickers).sort_index()

    # ------------------------------------------------------------------
    # Clustering utilities
    # ------------------------------------------------------------------

    def _get_linkage_matrix(self) -> np.ndarray:
        """
        Converts the correlation matrix into a distance matrix and performs
        hierarchical clustering.

        HRP distance metric:
            d_ij = sqrt(0.5 * (1 - corr_ij))
        """
        dist = np.sqrt(0.5 * (1 - self.corr_matrix))
        dist_condensed = squareform(dist, checks=False)
        linkage = sch.linkage(dist_condensed, method="ward")
        return linkage

    def _get_quasi_diag(self, linkage: np.ndarray) -> list[int]:
        """
        Produces an ordering of assets that groups similar ones together.
        This determines the block structure used during recursive splitting.
        """
        linkage = linkage.astype(int)

        # Initialize with the last merge
        sort_ix = pd.Series([linkage[-1, 0], linkage[-1, 1]])
        num_items = linkage[-1, 3]

        # Expand cluster indices into leaf indices
        while sort_ix.max() >= num_items:

            sort_ix.index = pd.Index(range(0, sort_ix.shape[0] * 2, 2))
            cluster_nodes = sort_ix[sort_ix >= num_items]

            i = cluster_nodes.index
            j = cluster_nodes.values - num_items

            # Replace cluster with left child
            sort_ix[i] = linkage[j, 0]

            # Insert right child
            right_child = pd.Series(linkage[j, 1], index=i + 1)

            sort_ix = pd.concat([sort_ix, right_child]).sort_index()
            sort_ix.index = pd.Index(range(len(sort_ix)))

        return sort_ix.tolist()

    # ------------------------------------------------------------------
    # Variance and allocation utilities
    # ------------------------------------------------------------------

    def _get_cluster_var(self, cov: pd.DataFrame, c_items: list[int]) -> float:
        """
        Computes the variance of a cluster using an Inverse Variance Portfolio (IVP).

        Inverse variance weights:
            w_i = 1 / var_i  normalized across the cluster.
        """
        cov_slice = cov.iloc[c_items, c_items]

        inv_diag = 1 / np.diag(cov_slice)
        weights = inv_diag / np.sum(inv_diag)

        return np.dot(np.dot(weights, cov_slice), weights)

    def _get_rec_bisection(self, sorted_cov: pd.DataFrame, sort_ix: list[int]) -> pd.Series:
        """
        Performs HRP recursive allocation.

        At each iteration:
            - Split cluster into left/right halves,
            - Compute cluster variances,
            - Allocate proportionally to the inverse of risk.
        """
        weights = pd.Series(1.0, index=sort_ix)
        cluster_items = [sort_ix]

        while cluster_items:
            cluster_items = [c for c in cluster_items if len(c) >= 2]

            for cluster in cluster_items:
                half = len(cluster) // 2
                left = cluster[:half]
                right = cluster[half:]

                left_var = self._get_cluster_var(sorted_cov, left)
                right_var = self._get_cluster_var(sorted_cov, right)

                alpha = 1 - left_var / (left_var + right_var)

                weights[left] *= alpha
                weights[right] *= 1 - alpha

            # Prepare deeper recursion
            next_level = []
            for cluster in cluster_items:
                half = len(cluster) // 2
                next_level.append(cluster[:half])
                next_level.append(cluster[half:])
            cluster_items = next_level

        return weights
