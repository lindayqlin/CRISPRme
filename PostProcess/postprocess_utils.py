"""Define static variables and utilities functions used throughout CRISPRme's 
post processing steps. 
"""

import sys
import os


# define pandas read_csv chunks size
CHUNKSIZE = 5000000000000
# define alt_results format columns order
ALT_RESULTS_HEADER_REORDER = [
    "Real_Guide", 
    "Chromosome", 
    "Position", 
    "Direction", 
    "Cluster_Position", 
    "crRNA", 
    "Reference", 
    "DNA", 
    "Mismatches", 
    "Bulge_Size", 
    "Total",
    "#Bulge_type", 
    "PAM_gen", 
    "CFD", 
    "CFD_ref", 
    "Highest_CFD_Risk_Score", 
    "Highest_CFD_Absolute_Risk_Score", 
    "SNP", 
    "AF", 
    "rsID",
    "Samples", 
    "Var_uniq", 
    "#Seq_in_cluster", 
    "MMBLG_Real_Guide", 
    "MMBLG_Chromosome", 
    "MMBLG_Position", 
    "MMBLG_Cluster_Position", 
    "MMBLG_Direction", 
    "MMBLG_crRNA",
    "MMBLG_Reference", 
    "MMBLG_DNA", 
    "MMBLG_Mismatches", 
    "MMBLG_Bulge_Size", 
    "MMBLG_Total", 
    "MMBLG_#Bulge_type", 
    "MMBLG_PAM_gen", 
    "MMBLG_CFD", 
    "MMBLG_CFD_ref",
    "MMBLG_CFD_Risk_Score", 
    "MMBLG_CFD_Absolute_Risk_Score", 
    "MMBLG_Var_uniq", 
    "MMBLG_SNP", 
    "MMBLG_AF", 
    "MMBLG_rsID", 
    "MMBLG_Samples", 
    "MMBLG_#Seq_in_cluster",
    "MMBLG_Annotation_Type", 
    "Annotation_Type"
]
# define alt_results format header names
ALT_RESULTS_HEADER_NAMES = [
    "Spacer+PAM",
    "Chromosome", 
    "Start_coordinate_(highest_CFD)", 
    "Strand_(highest_CFD)", 
    "Aligned_spacer+PAM_(highest_CFD)", 
    "Aligned_protospacer+PAM_REF_(highest_CFD)", 
    "Aligned_protospacer+PAM_ALT_(highest_CFD)",
    "Mismatches_(highest_CFD)", 
    "Bulges_(highest_CFD)", 
    "Mismatches+bulges_(highest_CFD)", 
    "Bulge_type_(highest_CFD)", 
    "PAM_creation_(highest_CFD)", 
    "CFD_score_(highest_CFD)", 
    "CFD_score_REF_(highest_CFD)",
    "CFD_risk_score_(highest_CFD)", 
    "Variant_info_genome_(highest_CFD)", 
    "Variant_MAF_(highest_CFD)", 
    "Variant_rsID_(highest_CFD)", 
    "Variant_samples_(highest_CFD)", 
    "Not_found_in_REF", 
    "Other_motifs",
    "Start_coordinate_(fewest_mm+b)", 
    "Strand_(fewest_mm+b)", 
    "Aligned_spacer+PAM_(fewest_mm+b)", 
    "Aligned_protospacer+PAM_REF_(fewest_mm+b)", 
    "Aligned_protospacer+PAM_ALT_(fewest_mm+b)",
    "Mismatches_(fewest_mm+b)", 
    "Bulges_(fewest_mm+b)", 
    "Mismatches+bulges_(fewest_mm+b)", 
    "Bulge_type_(fewest_mm+b)", 
    "PAM_creation_(fewest_mm+b)", 
    "CFD_score_(fewest_mm+b)",
    "CFD_score_REF_(fewest_mm+b)", 
    "CFD_risk_score_(fewest_mm+b)", 
    "Variant_info_genome_(fewest_mm+b)", 
    "Variant_MAF_(fewest_mm+b)", 
    "Variant_rsID_(fewest_mm+b)",
    "Variant_samples_(fewest_mm+b)", 
    "Annotation"
]
# guide column in the results table
GUIDE_COLUMN = "Spacer+PAM"
# allowed filtering criteria
FILTERING_CRITERIA = ["CFD", "fewest", "CRISTA"]
# dictionary to map pandas datatypes to SQL datatypes
DTYPE_SQLTYPE_MAP = {"O": "TEXT", "int64": "INTEGER", "float64": "NUMERIC"}
# database column names
DB_COLNAMES = [
    "Spacer+PAM",
    "Mismatches_(highest_CFD)",
    "Bulges_(highest_CFD)",
    "Mismatches+bulges_(highest_CFD)",
    "CFD_score_(highest_CFD)",
    "CFD_risk_score_(highest_CFD)",
    "Start_coordinate_(highest_CFD)",
    "Variant_samples_(highest_CFD)",
    "Chromosome",
    "Bulge_type_(highest_CFD)",
]




