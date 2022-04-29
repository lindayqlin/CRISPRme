"""Build the general CFD graph from previously computed CFD graphs summarizing
SNPs and indels.
"""

import pandas as pd
import numpy as np

import subprocess
import sys
import os


def build_cfd_graphs(outdir: str) -> None:
    """Build the CFD graphs.

    ...

    Parameters
    ----------
    outdir : str
        Output directory

    Returns
    -------
    None
    """

    if not isinstance(outdir, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outdir).__name__}")
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    # recover fake and real CFDGraph files
    cfd_fakes = [
        f for f in os.listdir(outdir) if ("CFDGraph" in f and "fake" in f)
    ]
    cfd_reals = [
        f for f in os.listdir(outdir) if ("CFDGraph" in f and "fake" not in f)
    ]
    if cfd_fakes:  # fake files found
        cumulative_graph_fake = pd.DataFrame(
            np.zeros([101,2]), columns=["ref", "var"]
        )  # 101 x 2 matrix (filled with 0s)
        for f in cfd_fakes:
            mat = pd.read_csv(f, sep="\t")  # TSV-like files
            cumulative_graph_fake.add(mat)
            # delete read file
            cmd = f"rm {f}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
        # force int64 type elements
        cumulative_graph_fake = cumulative_graph_fake.astype("int64")
        # store graph data
        cumulative_graph_fake.to_csv(
            "indels.CFDGraph.txt", sep="\t", index=False
        )
    if cfd_reals:  # real files found
        cumulative_graph_true = pd.DataFrame(
            np.zeros([101, 2]), columns=["ref", "var"]
        )  # 101 x 2 matrix (filled with 0s)
        for f in cfd_reals:
            mat = pd.read_csv(f, sep="\t")  # TSV-like files
            cumulative_graph_true = cumulative_graph_true.add(mat)
            cmd = f"rm {f}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
        # force int64 type elements
        cumulative_graph_true = cumulative_graph_true.astype("int64")
        # store graph data
        cumulative_graph_true.to_csv(
            "snps.CFDGraph.txt", sep="\t", index=False
        )


def main():
    outdir = sys.argv[1]
    build_cfd_graphs(outdir)


if __name__ == "__main__":
    main()
