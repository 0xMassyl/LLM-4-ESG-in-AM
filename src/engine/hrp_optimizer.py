# -------------------------------------------------
# Numerical and data handling libraries
# -------------------------------------------------
import pandas as pd
import numpy as np

# -------------------------------------------------
# SciPy clustering tools
# Used to build the hierarchical tree (dendrogram)
# -------------------------------------------------
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


class HRPOptimizer:
    """
    Hierarchical Risk Parity (HRP) portfolio optimizer.

    This implementation follows the methodology introduced by
    Marcos López de Prado (2016).

    Key idea:
    - Do NOT invert the covariance matrix (unlike Markowitz)
    - Use clustering to structure diversification
    - Allocate risk recursively, not asset by asset
    """

    def __init__(self, returns: pd.DataFrame):
        # Store asset returns (rows = time, columns = assets)
        self.returns = returns

        # Extract asset identifiers once for reuse
        self.tickers = returns.columns.tolist()

        # Precompute covariance matrix
        # Used later for variance and allocation calculations
        self.cov = returns.cov()

        # Precompute correlation matrix
        # Used only for clustering (distance computation)
        self.corr = returns.corr()

    def optimize(self) -> pd.Series:
        """
        Runs the full HRP pipeline and returns portfolio weights.

        Output:
        - pandas Series indexed by ticker
        - weights sum to 1
        """

        # -------------------------------------------------
        # Step 1: Convert correlation to distance matrix
        # -------------------------------------------------

        # HRP uses a distance metric derived from correlation:
        # d(i, j) = sqrt(0.5 * (1 - corr(i, j)))
        #
        # Properties:
        # - perfectly correlated assets → distance = 0
        # - uncorrelated assets → distance ~ 0.707
        # - negatively correlated assets → larger distance
        dist = np.sqrt(0.5 * (1 - self.corr))

        # Convert square distance matrix to condensed form
        # Required by SciPy clustering algorithms
        dist_condensed = squareform(dist, checks=False)

        # Perform hierarchical clustering
        # "single" linkage = nearest-neighbor clustering
        # This preserves local similarity structures
        linkage = sch.linkage(dist_condensed, method="single")

        # -------------------------------------------------
        # Step 2: Quasi-diagonalization
        # -------------------------------------------------

        # Extract asset ordering implied by the dendrogram
        sort_ix = self._get_quasi_diag(linkage)

        # Convert integer positions to actual ticker names
        sort_ix = self.corr.index[sort_ix].tolist()

        # -------------------------------------------------
        # Step 3: Reorder covariance matrix
        # -------------------------------------------------

        # Reordering aligns similar assets next to each other
        # This structure is required for recursive bisection
        df_cov = self.cov.loc[sort_ix, sort_ix]

        # -------------------------------------------------
        # Step 4: Recursive bisection allocation
        # -------------------------------------------------

        # Start with equal weights (will be adjusted recursively)
        weights = pd.Series(1.0, index=sort_ix)

        # Recursively allocate capital across clusters
        weights = self._get_rec_bisection(weights, df_cov, sort_ix)

        # Return weights sorted by original ticker order
        return weights.sort_index()

    def _get_quasi_diag(self, linkage: np.ndarray) -> list:
        """
        Reorders assets so that similar assets are adjacent.

        Why this matters:
        - hierarchical clustering produces a tree, not an order
        - HRP needs a linear ordering that respects the tree structure
        """

        # Ensure linkage matrix uses integer indices
        linkage = linkage.astype(int)

        # Start from the final merge (root of the tree)
        sort_ix = pd.Series([linkage[-1, 0], linkage[-1, 1]])

        # Number of original items (leaf nodes)
        num_items = linkage[-1, 3]

        # Loop until all cluster references are expanded into leaf nodes
        while sort_ix.max() >= num_items:

            # Reindex to make space for child insertions
            sort_ix.index = pd.Index(range(0, sort_ix.shape[0] * 2, 2))

            # Identify cluster nodes (internal tree nodes)
            clusters = sort_ix[sort_ix >= num_items]

            # Locations in linkage matrix
            idx = clusters.index
            loc = clusters.values - num_items

            # Replace cluster node with its left child
            sort_ix[idx] = linkage[loc, 0]

            # Insert right child immediately after
            new_right = pd.Series(linkage[loc, 1], index=idx + 1)
            sort_ix = pd.concat([sort_ix, new_right]).sort_index()

            # Reset index to be continuous
            sort_ix.index = pd.Index(range(len(sort_ix)))

        # Final ordered list of asset indices
        return sort_ix.tolist()

    def _get_cluster_var(self, cov: pd.DataFrame, c_items: list) -> float:
        """
        Computes the variance of a cluster using an
        Inverse Variance Portfolio (IVP).

        Why IVP:
        - avoids inverting covariance matrices
        - robust to estimation noise
        - consistent with HRP philosophy
        """

        # Extract sub-covariance matrix for the cluster
        cov_slice = cov.loc[c_items, c_items]

        # Inverse of diagonal variances
        inv_diag = 1 / np.diag(cov_slice)

        # Normalize to get portfolio weights
        weights = inv_diag / np.sum(inv_diag)

        # Portfolio variance = w' * Cov * w
        return float(np.dot(weights, np.dot(cov_slice, weights)))

    def _get_rec_bisection(
        self,
        weights: pd.Series,
        cov: pd.DataFrame,
        sort_ix: list
    ) -> pd.Series:
        """
        Core HRP allocation logic.

        The algorithm:
        - splits clusters into two halves
        - compares their variances
        - allocates more weight to lower-risk clusters
        """

        # Work on a copy to avoid side effects
        w = weights.copy()

        # Initialize with full ordered list
        clusters = [sort_ix]

        # Continue until no cluster can be split further
        while len(clusters) > 0:

            # Only split clusters with at least 2 assets
            clusters = [c for c in clusters if len(c) >= 2]

            for c in clusters:
                # Split cluster into left/right halves
                half = len(c) // 2
                left = c[:half]
                right = c[half:]

                # Compute variance of each sub-cluster
                var_left = self._get_cluster_var(cov, left)
                var_right = self._get_cluster_var(cov, right)

                # Allocation factor:
                # higher variance → lower allocation
                alpha = 1 - var_left / (var_left + var_right)

                # Apply allocation recursively
                w[left] *= alpha
                w[right] *= (1 - alpha)

            # Prepare next level of recursion
            new_level = []
            for c in clusters:
                half = len(c) // 2
                if len(c) > 1:
                    new_level.append(c[:half])
                    new_level.append(c[half:])
            clusters = new_level

        return w
