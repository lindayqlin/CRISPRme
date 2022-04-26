"""Convert old bestMerge file format to the more recent alt_results format, 
which is used to load and display the results within CRISPRme webpage.
"""


from .postprocess_utils import (
    CHUNKSIZE, ALT_RESULTS_HEADER_REORDER, ALT_RESULTS_HEADER_NAMES
)

import pandas as pd
import numpy as np

import sys
import warnings
import os


# set to ignore warnings
warnings.simplefilter(action="ignore", category=FutureWarning)


def convert_headers(original_file: str, out_file: str) -> None:
    """Convert old bestMerge results format to new alt_results format. 
    The change mainly regards the columns headers.

    ...

    Parameters
    ----------
    original_file : str
        Filename to convert
    out_file : str
        Output filename

    Returns
    -------
    None
    """

    if not isinstance(original_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(original_file).__name__}"
        )
    if not os.path.isfile(original_file):
        raise FileNotFoundError(f"Unable to locate {original_file}")
    if not isinstance(out_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(out_file).__name__}"
        )
    if not os.path.isfile(out_file):
        raise FileNotFoundError(f"Unable to locate {out_file}")
    chunks = pd.read_csv(
        original_file, sep="\t", chunksize=CHUNKSIZE, na_filter=False
    )
    # columns to remove from header
    drop_cols = [
        "Cluster_Position", 
        "Highest_CFD_Absolute_Risk_Score", 
        "MMBLG_Real_Guide", 
        "MMBLG_Chromosome", 
        "MMBLG_Cluster_Position",
        "MMBLG_CFD_Absolute_Risk_Score", 
        "MMBLG_Var_uniq", 
        "MMBLG_#Seq_in_cluster", 
        "MMBLG_Annotation_Type"
    ]
    for i, chunk in enumerate(chunks):
        chunk = chunk[ALT_RESULTS_HEADER_REORDER]
        chunk = chunk.drop(drop_cols, axis=1)
        chunk.columns = ALT_RESULTS_HEADER_NAMES
        chunk.replace("n", "NA")  # replace NA values
        # CFD scores
        chunk["Variant_rsID_(highest_CFD)"] = chunk[
            "Variant_rsID_(highest_CFD)"
        ].str.replace(".", "NA")
        mask = chunk["Aligned_protospacer+PAM_REF_(highest_CFD)"] == "NA"
        chunk["Aligned_protospacer+PAM_REF_corrected_(highest_CFD)"] = np.where(
            mask, 
            chunk["Aligned_protospacer+PAM_ALT_(highest_CFD)"],
            chunk["Aligned_protospacer+PAM_REF_(highest_CFD)"]
        )
        chunk["Aligned_protospacer+PAM_ALT_(highest_CFD)"] = np.where(
            mask, 
            chunk["Aligned_protospacer+PAM_REF_(highest_CFD)"],
            chunk["Aligned_protospacer+PAM_ALT_(highest_CFD)"]
        )
        chunk["Aligned_protospacer+PAM_REF_(highest_CFD)"] = chunk[
            "Aligned_protospacer+PAM_REF_corrected_(highest_CFD)"
        ]
        chunk.drop(
            "Aligned_protospacer+PAM_REF_corrected_(highest_CFD)", 
            axis=1, 
            inplace=True
        )
        # mismatches + bulges
        mask = chunk["Aligned_protospacer+PAM_REF_(fewest_mm+b)"] == "NA"
        chunk["Aligned_protospacer+PAM_REF_corrected_(fewest_mm+b)"] = np.where(
            mask,
            chunk["Aligned_protospacer+PAM_ALT_(fewest_mm+b)"],
            chunk["Aligned_protospacer+PAM_REF_(fewest_mm+b)"]
        )
        chunk["Aligned_protospacer+PAM_ALT_(fewest_mm+b)"] = np.where(
            mask,
            chunk["Aligned_protospacer+PAM_REF_(fewest_mm+b)"],
            chunk["Aligned_protospacer+PAM_ALT_(fewest_mm+b)"]
        )
        chunk["Aligned_protospacer+PAM_REF_(fewest_mm+b)"] = chunk[
            "Aligned_protospacer+PAM_REF_corrected_(fewest_mm+b)"
        ]
        chunk.drop(
            "Aligned_protospacer+PAM_REF_corrected_(fewest_mm+b)",
            axis=1,
            inplace=True
        )
        # store resulting table in TSV file
        header = False
        if i == 0:  # first loop
            header = True
        # write TSV file
        chunk.to_csv(
            out_file, header=header, mode="w", sep="\t", index=False, na_rep="NA"
        )
