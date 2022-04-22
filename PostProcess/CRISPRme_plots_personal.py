"""Compute personal risk plots for the top 100 private off-targets found for each 
sample considered in the input search. For each individual, the plots are 
computed using the top 100 off-targets according to mismatches and bulges, CFD,
or CRISTA scores. The sorting criterion is selected by the user through the 
general dropdown bar of the results webpage.

The plots are displayed under the Personal Risk Cards tab in the results webpage.

(Note: will get runtime warnings but all are fine to ignore)
"""


import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.colors as mcolors
import pandas as pd
import numpy as np

import math
import sys
import matplotlib
import warnings
import os


# ignore all warnings
warnings.filterwarnings("ignore")

# set matplotlib to not use X11 server
matplotlib.use("Agg")


def plot_with_MMvBUL(df: pd.DataFrame, outdir: str, guide: str) -> None:
    """Plot the top 100 personal targets filtered by mismatch and bulges
    (filtering criterion selected by the user via the drop-down bar).

    ...

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with the found targets
    outdir : str
        Output directory
    guide : str
        Guide

    Returns
    -------
    None
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected {type(pd.DataFrame).__name__}, got {type(df).__name__}"
        )
    if not isinstance(outdir, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outdir).__name__}")
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    if not isinstance(guide, str):
        raise TypeError(f"Expected {str.__name__}, got {type(guide).__name__}")
    # Remove targets ref with mm+bul<=1 for on-targets and on-targets variant-induced
    df = df.loc[df["Mismatches+bulges_(fewest_mm+b)"] > 1]
    # new col to store the scoring value for non-SpCas9 targets
    df["Mismatches+bulges_REF_(fewest_mm+b)"] = 0
    df["Mismatches+bulges_ALT_(fewest_mm+b)"] = 0
    # if col is alt calculate score for ref and alt, if ref skip
    for index in df.index:
        if df.loc[index, "REF/ALT_origin_(fewest_mm+b)"] == "alt":
            ref_target = str(
                df.loc[index, "Aligned_protospacer+PAM_REF_(fewest_mm+b)"]
            )
            countMM = 0
            for nt in ref_target:
                if nt.islower():
                    countMM += 1
            df.loc[
                index, "Mismatches+bulges_REF_(fewest_mm+b)"
            ] = countMM + int(df.loc[index, "Bulges_(fewest_mm+b)"])
            df.loc[
                index, "Mismatches+bulges_ALT_(fewest_mm+b)"
            ] = df.loc[index, "Mismatches+bulges_(fewest_mm+b)"]
        else:
            df.loc[
                index, "Mismatches+bulges_REF_(fewest_mm+b)"
            ] = df.loc[index, "Mismatches+bulges_(fewest_mm+b)"]
            df.loc[
                index, "Mismatches+bulges_ALT_(fewest_mm+b)"
            ] = df.loc[index, "Mismatches+bulges_(fewest_mm+b)"]

    # sort in order to have highest REF mm+bul on top
    df.sort_values(
        "Mismatches+bulges_(fewest_mm+b)", ascending=True, inplace=True
    )
    # top 100 targets
    df = df.head(100)
    # Make index column that numbers the OTs starting from 1
    df.reset_index(inplace=True)
    df["index"] = np.array(df.index.tolist()) + 1
    # If prim_AF = 'n', then it's a ref-nominated site, so we enter a fake numerical AF
    # This will cause a warning of invalid sqrt later on, but that's fine to ignore
    # df["prim_AF"] = df["prim_AF"].fillna(-1)
    df["Variant_MAF_(fewest_mm+b)"] = df["Variant_MAF_(fewest_mm+b)"].fillna(-1)
    # If multiple AFs (haplotype with multiple SNPs), take min AF
    # Approximation until we have haplotype frequencies
    df["AF"] = df["Variant_MAF_(fewest_mm+b)"].astype(str).str.split(",")
    df["AF"] = df["AF"].apply(lambda x: min(x))
    df["AF"] = pd.to_numeric(df["AF"])
    # Adjustments for plotting purposes so haplotypes that got rounded down to 
    # AF = 0 (min AF = 0.01) still appear in the plot
    df["plot_AF"] = df["AF"] + 0.001
    df["plot_AF"] *= 1000  # make points larger
    df["plot_AF"] = np.sqrt(df["plot_AF"])  # so size increase is linear
    # Calculate ref_AF as (1 – alt_AF)
    # Not precisely correct because there can be other non-ref haplotypes, but approximation should be accurate in most cases
    df["ref_AF"] = 1 - df["AF"]
    df["ref_AF"] *= 1000  # make points larger
    df["ref_AF"] = np.sqrt(df["ref_AF"])  # so size increase is linear
    # Transparent colors
    transparent_red = mcolors.colorConverter.to_rgba("red", alpha=0.5)
    transparent_blue = mcolors.colorConverter.to_rgba("blue", alpha=0.5)
    transparent_gray = mcolors.colorConverter.to_rgba("gray", alpha=0.5)
    # Size legend
    s1 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((1 + 0.001) * 1000)), 
        color="black"
    )
    s01 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.1 + 0.001) * 1000)), 
        color="black"
    )
    s001 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.01", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.01 + 0.001) * 1000)), 
        color="black"
    )
    # Log, ref/alt, top 1000: for main text
    # matplotlib plot settings
    plt.rcParams["figure.dpi"] = 600
    plt.rcParams["figure.figsize"] = 7.5, 2.25
    plt.rcParams.update({"font.size": 7})
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    # Plot data
    ax = df.plot.scatter(
        x="index", 
        y="Mismatches+bulges_REF_(fewest_mm+b)",
        s="ref_AF", 
        c=transparent_red, 
        zorder=1
    )
    df.plot.scatter(
        x="index", 
        y="Mismatches+bulges_ALT_(fewest_mm+b)",
        s="plot_AF", 
        c=transparent_blue, 
        zorder=2, 
        ax=ax
    )
    ax.set_xscale("log")
    plt.xlabel("Candidate off-target site")
    plt.ylabel("Mismatches+Bulges")
    # Boundaries
    plt.xlim(xmin=0.9, xmax=100)
    # Arrows
    for x, y, z in zip(
        df["index"], 
        df["Mismatches+bulges_REF_(fewest_mm+b)"], 
        df["Mismatches+bulges_ALT_(fewest_mm+b)"] - df["Mismatches+bulges_REF_(fewest_mm+b)"]
    ):
        plt.arrow(
            x, 
            y + 0.02, 
            0, 
            z - 0.04, 
            color="gray", 
            head_width=(x * (10**0.005 - 10**(-0.005))),
            head_length=0.02, 
            length_includes_head=True, 
            zorder=0, 
            alpha=0.5
        )
        # +/- to avoid overlap of arrow w/ points, head_width calculated to remain constant despite log scale of x-axis
    # Size legend
    plt.gca().add_artist(
        plt.legend(
            handles=[s1, s01, s001], title="Allele frequency", ncol=3, loc=9
        )
    )
    # Color legend
    red = mpatches.Patch(color=transparent_red, label="Reference")
    blue = mpatches.Patch(color=transparent_blue, label="Alternative")
    plt.legend(handles=[red, blue])
    # Save figure
    plt.tight_layout()
    figname = f"CRISPRme_fewest_top_1000_log_for_main_text_{guide}.png"
    plt.savefig(os.path.join(outdir, figname))
    plt.clf()


def plot_with_CRISTA_score(df: pd.DataFrame, outdir: str, guide: str) -> None:
    """Plot the top 100 personal targets filtered by CRISTA scores
    (filtering criterion selected by the user via the drop-down bar).

    ...

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with the found targets
    outdir : str
        Output directory
    guide : str
        Guide

    Returns
    -------
    None
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected {type(pd.DataFrame).__name__}, got {type(df).__name__}"
        )
    if not isinstance(outdir, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outdir).__name__}")
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    if not isinstance(guide, str):
        raise TypeError(f"Expected {str.__name__}, got {type(guide).__name__}")
    # Remove targets with mm+bul<=1 since they are probably on-target introduced 
    # by variants
    df = df.loc[df["Mismatches+bulges_(highest_CRISTA)"] > 1]
    # sort values to have highest scored target on top
    df.sort_values(
        "CRISTA_score_(highest_CRISTA)", ascending=False, inplace=True
    )
    # keep top1000 targets
    df = df.head(100)
    # Make index column that numbers the OTs starting from 1
    df.reset_index(inplace=True)
    df["index"] = np.array(df.index.tolist()) + 1
    # If prim_AF = 'n', then it's a ref-nominated site, so we enter a fake numerical AF
    # This will cause a warning of invalid sqrt later on, but that's fine to ignore
    df["Variant_MAF_(highest_CRISTA)"] = df["Variant_MAF_(highest_CRISTA)"].fillna(-1)
    # If multiple AFs (haplotype with multiple SNPs), take min AF
    # Approximation until we have haplotype frequencies
    df["AF"] = df["Variant_MAF_(highest_CRISTA)"].astype(str).str.split(",")
    df["AF"] = df["AF"].apply(lambda x: min(x))
    df["AF"] = pd.to_numeric(df["AF"])
    # Adjustments for plotting purposes
    # so haplotypes that got rounded down to AF = 0 (min AF = 0.01) still appear in the plot
    df["plot_AF"] = df["AF"] + 0.001
    df["plot_AF"] *= 1000  # make points larger
    df["plot_AF"] = np.sqrt(df["plot_AF"])  # so size increase is linear
    # Calculate ref_AF as (1 – alt_AF)
    # Not precisely correct because there can be other non-ref haplotypes, but approximation should be accurate in most cases
    df["ref_AF"] = 1 - df["AF"]
    df["ref_AF"] *= 1000  # make points larger
    df["ref_AF"] = np.sqrt(df["ref_AF"])  # so size increase is linear
    # Transparent colors
    transparent_red = mcolors.colorConverter.to_rgba("red", alpha=0.5)
    transparent_blue = mcolors.colorConverter.to_rgba("blue", alpha=0.5)
    transparent_gray = mcolors.colorConverter.to_rgba("gray", alpha=0.5)
    # # Size legend
    s1 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((1 + 0.001) * 1000)), 
        color="black"
    )
    s01 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.1 + 0.001) * 1000)), 
        color="black"
    )
    s001 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.01", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.01 + 0.001) * 1000)), 
        color="black"
    )
    # Log, ref/alt, top 1000: for main text
    # matplotlib plot settings
    plt.rcParams["figure.dpi"] = 600
    plt.rcParams["figure.figsize"] = 7.5, 2.25
    plt.rcParams.update({"font.size": 7})
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    # Plot data CFD SCORE
    ax = df.plot.scatter(
        x="index", 
        y="CRISTA_score_REF_(highest_CRISTA)",
        s="ref_AF", 
        c=transparent_red, 
        zorder=1
    )
    df.plot.scatter(
        x="index", 
        y="CRISTA_score_ALT_(highest_CRISTA)",
        s="plot_AF", 
        c=transparent_blue, 
        zorder=2, 
        ax=ax
    )
    ax.set_xscale("log")
    plt.xlabel("Candidate off-target site")
    plt.ylabel("CRISTA score")
    # Boundaries
    plt.xlim(xmin=0.9, xmax=100)
    plt.ylim(ymin=0, ymax=1)
    # Arrows
    for x, y, z in zip(
        df["index"], 
        df["CRISTA_score_REF_(highest_CRISTA)"], 
        df["CRISTA_score_ALT_(highest_CRISTA)"] - df["CRISTA_score_REF_(highest_CRISTA)"]
    ):
        plt.arrow(
            x, 
            y + 0.02, 
            0, 
            z - 0.04, 
            color="gray", 
            head_width=(x * (10**0.005 - 10**(-0.005))),
            head_length=0.02, 
            length_includes_head=True, 
            zorder=0, 
            alpha=0.5
        )
        # +/- to avoid overlap of arrow w/ points, head_width calculated to 
        # remain constant despite log scale of x-axis
    # Size legend
    plt.gca().add_artist(
        plt.legend(
            handles=[s1, s01, s001], title="Allele frequency", ncol=3, loc=9
        )
    )
    # Color legend
    red = mpatches.Patch(color=transparent_red, label="Reference")
    blue = mpatches.Patch(color=transparent_blue, label="Alternative")
    plt.legend(handles=[red, blue])
    # Save figure
    plt.tight_layout()
    figname = f"CRISPRme_CRISTA_top_1000_log_for_main_text_{guide}.png"
    plt.savefig(os.path.join(outdir, figname))
    plt.clf()


def plot_with_CFD_score(df: pd.DataFrame, outdir: str, guide: str) -> None:
    """Plot the top 100 personal targets filtered by CFD scores
    (filtering criterion selected by the user via the drop-down bar).

    ...

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with the found targets
    outdir : str
        Output directory
    guide : str
        Guide

    Returns
    -------
    None
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected {type(pd.DataFrame).__name__}, got {type(df).__name__}"
        )
    if not isinstance(outdir, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outdir).__name__}")
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    if not isinstance(guide, str):
        raise TypeError(f"Expected {str.__name__}, got {type(guide).__name__}")
    # Remove targets with mm+bul<=1 since they are probably on-target introduced 
    # by variants
    df = df.loc[df["Mismatches+bulges_(highest_CFD)"] > 1]
    # sort values to have highest scored target on top
    df.sort_values(
        "CFD_score_(highest_CFD)", ascending=False, inplace=True
    )
    # keep top1000 targets
    df = df.head(100)
    # Make index column that numbers the OTs starting from 1
    df.reset_index(inplace=True)
    df["index"] = np.array(df.index.tolist()) + 1
    # If prim_AF = 'n', then it's a ref-nominated site, so we enter a fake numerical AF
    # This will cause a warning of invalid sqrt later on, but that's fine to ignore
    df["Variant_MAF_(highest_CFD)"] = df["Variant_MAF_(highest_CFD)"].fillna(-1)
    # If multiple AFs (haplotype with multiple SNPs), take min AF
    # Approximation until we have haplotype frequencies
    df["AF"] = df["Variant_MAF_(highest_CFD)"].astype(str).str.split(",")
    df["AF"] = df["AF"].apply(lambda x: min(x))
    df["AF"] = pd.to_numeric(df["AF"])
    # Adjustments for plotting purposes
    # so haplotypes that got rounded down to AF = 0 (min AF = 0.01) still appear 
    # in the plot
    df["plot_AF"] = df["AF"] + 0.001
    df["plot_AF"] *= 1000  # make points larger
    df["plot_AF"] = np.sqrt(df["plot_AF"])  # so size increase is linear
    # Calculate ref_AF as (1 – alt_AF)
    # Not precisely correct because there can be other non-ref haplotypes, but approximation should be accurate in most cases
    df["ref_AF"] = 1 - df["AF"]
    df["ref_AF"] *= 1000  # make points larger
    df["ref_AF"] = np.sqrt(df["ref_AF"])  # so size increase is linear
    # Transparent colors
    transparent_red = mcolors.colorConverter.to_rgba("red", alpha=0.5)
    transparent_blue = mcolors.colorConverter.to_rgba("blue", alpha=0.5)
    transparent_gray = mcolors.colorConverter.to_rgba("gray", alpha=0.5)
    # Linear, annotated, top 100 (for supplement)
    # Size legend
    s1 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((1 + 0.001) * 1000)), 
        color="black"
    )
    s01 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.1", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.1 + 0.001) * 1000)), 
        color="black"
    )
    s001 = mlines.Line2D(
        [], 
        [], 
        marker="o", 
        label="0.01", 
        linestyle="None",
        markersize=math.sqrt(math.sqrt((0.01 + 0.001) * 1000)), 
        color="black"
    )
    # Log, ref/alt, top 1000: for main text
    # matplotlib plot settings
    plt.rcParams["figure.dpi"] = 600
    plt.rcParams["figure.figsize"] = 7.5, 2.25
    plt.rcParams.update({"font.size": 7})
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    # Plot data CFD SCORE
    ax = df.plot.scatter(
        x="index", 
        y="CFD_score_REF_(highest_CFD)",
        s="ref_AF", 
        c=transparent_red, 
        zorder=1
    )
    df.plot.scatter(
        x="index", 
        y="CFD_score_ALT_(highest_CFD)",
        s="plot_AF", 
        c=transparent_blue, 
        zorder=2, 
        ax=ax
    )
    ax.set_xscale("log")
    plt.xlabel("Candidate off-target site")
    plt.ylabel("CFD score")
    # Boundaries
    plt.xlim(xmin=0.9, xmax=100)
    plt.ylim(ymin=0, ymax=1)
    # Arrows
    for x, y, z in zip(
        df["index"], 
        df["CFD_score_REF_(highest_CFD)"], 
        df["CFD_score_ALT_(highest_CFD)"] - df["CFD_score_REF_(highest_CFD)"]
    ):
        plt.arrow(
            x, 
            y + 0.02, 
            0, 
            z - 0.04, 
            color="gray", 
            head_width=(x * (10**0.005 - 10**(-0.005))),
            head_length=0.02, 
            length_includes_head=True, 
            zorder=0, 
            alpha=0.5
        )
        # +/- to avoid overlap of arrow w/ points, head_width calculated to 
        # remain constant despite log scale of x-axis
    # Size legend
    plt.gca().add_artist(
        plt.legend(
            handles=[s1, s01, s001], title="Allele frequency", ncol=3, loc=9
        )
    )
    # Color legend
    red = mpatches.Patch(color=transparent_red, label="Reference")
    blue = mpatches.Patch(color=transparent_blue, label="Alternative")
    plt.legend(handles=[red, blue])
    # Save figure
    plt.tight_layout()
    figname = f"CRISPRme_CFD_top_1000_log_for_main_text_{guide}.png"
    plt.savefig(os.path.join(outdir, figname))
    plt.clf()


# ---> entry point <---
# read input args
df_guide = pd.read_csv(sys.argv[1], sep="\t", index_col=False, na_values=["n"])
outdir = sys.argv[2]
guide = sys.argv[3]
# for guide in df['Spacer+PAM'].unique():
# reset df temp after every process to avoid memory problems
# df_guide = df.loc[df["Spacer+PAM"] == guide]
# takes df in input and produces the correlated plot, guide is used to save with 
# correct name
plot_with_CFD_score(df_guide, outdir, guide)
plot_with_CRISTA_score(df_guide, outdir, guide)
plot_with_MMvBUL(df_guide, outdir, guide)
