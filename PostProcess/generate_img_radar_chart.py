"""Compute the radar charts displayed in the graphical report tab of the results
webpage of CRISPRme.
"""


from typing import Dict, List, Optional
from matplotlib import pyplot as plt

import numpy as np
from math import pi
import pandas as pd

import matplotlib
import warnings
import random
import json
import os


# set static parameters
matplotlib.use("Agg")
warnings.filterwarnings("ignore")
plt.style.use("seaborn-poster")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
random.seed(a=None, version=2)
# static vars
POPULATION = False
FILE_EXTENSION = "png"  # images are in PNG format


def compute_radar_chart(
    guide: str, 
    guide_dict_fname: str, 
    motif_dict_fname: str,
    mismatch: str,
    bulge: int,
    elem: str,
    outdir: str,
    web_server: Optional[bool]=False,
) -> None:
    """Read and check the input parameters for the function creating the 
    radar charts, summarizing CRISPRme results.

    ...

    Parameters
    ----------
    guide : str
        Guide
    guide_dict_fname : str
        Guide dictionary filename
    motif_dict_fname : str
        Motif dictionary filename
    mismatch : str
        Mismatches
    bulge : int
        Bulges
    elem : str
        Filtering criterion
    outdir : str
        Output directory
    web_server : Optional[bool]

    Returns
    -------
    None
    """

    if not isinstance(guide, str):
        raise TypeError(f"Expected {str.__name__}, got {type(guide).__name__}")
    if not isinstance(guide_dict_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(guide_dict_fname).__name__}"
        )
    if not os.path.isfile(guide_dict_fname):
        raise FileNotFoundError(f"Unable to locate {guide_dict_fname}")
    if not isinstance(motif_dict_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(motif_dict_fname).__name__}"
        )
    if not os.path.isfile(motif_dict_fname):
        raise FileNotFoundError(f"Unable to locate {motif_dict_fname}")
    if not isinstance(mismatch, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(mismatch).__name__}"
        )
    if int(mismatch) < 0:
        raise ValueError(f"Forbidden mismatch value ({mismatch})")
    if not isinstance(bulge, int):
        raise TypeError(
            f"Expected {int.__name__}, got {type(bulge).__name__}"
        )
    if bulge < 0:
        raise ValueError(f"Forbidden bulges value ({bulge})")
    if not isinstance(outdir, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outdir).__name__}")
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    file_extension = FILE_EXTENSION if web_server else "png"
    guide = guide.strip()
    try:
        handle_guide_dict = open(guide_dict_fname)
        handle_motif_dict = open(motif_dict_fname)
        guide_dict = json.load(handle_guide_dict)
        motif_dict = json.load(handle_motif_dict)
    except OSError as e:
        raise e
    finally:
        handle_guide_dict.close()
        handle_motif_dict.close()
    total_count = str(int(mismatch) + bulge)
    # skip creation if no target in global category
    if guide_dict[total_count]["General"] == 0:
        return
    try:
        generate_plot(
            guide, 
            guide_dict[total_count], 
            motif_dict[total_count], 
            int(mismatch), 
            bulge, 
            elem, 
            outdir, 
            file_extension
        )
    except OSError as e:
        raise e


def chunks(lst: List, n: int):
    """Yield successive n-sized chunks from lst.
    
    ...
    
    Parameters
    ----------
    lst : List
        List
    n : int
        Chunks size

    Returns
    -------
    List
    """

    assert isinstance(lst, list)
    assert isinstance(n, int)
    for i in range(0, len(lst), n):
        yield lst[i:(i + n)]


def generate_plot(
    guide: str, 
    guide_dict: Dict, 
    motif_dict: Dict, 
    mismatch: int, 
    bulge: int, 
    source: str,
    outdir: str,
    file_extension: str,
)-> None:
    """Compute and generate the radar charts.

    ...

    Parameters
    ----------
    guide : str
        Guide
    guide_dict : Dict
        Guide dictionary
    motif_dict : Dict
        Motif dictionary
    mismatch : int
        Mismatches
    bulge : int
        Bulges
    source : str
        Filter criterion
    outdir : str
        Output directory
    file_extension : str
        File extension

    Returns
    -------
    None
    """

    # check if no targets are found for that combination source/totalcount 
    # and eventually skip the execution
    if guide_dict["General"] == 0:
        return
    total = mismatch + bulge  # total count of mismatch and bulge required
    # plots parameters
    titlesize = 18
    fontsize = 17
    # pct list
    pct_list = [
        round(((float(guide_dict[e]) * 100) / float(guide_dict["General"])), 2)
        if float(guide_dict["General"] != 0)
        else round(float(0), 0)
        for e in guide_dict.keys()
    ]
    # create guides dataframe
    guides_df = pd.DataFrame.from_dict(guide_dict, orient="index")
    guides_df["Percentage"] = pct_list
    guides_df.columns = ["Count", "Percentage"]
    try:
        keep_cols = [
            "General", 
            "three_prime_UTR", 
            "five_prime_UTR", 
            "exon", 
            "CDS", 
            "gene",
            "DNase-H3K4me3",
            "CTCF-only",
            "dELS",
            "pELS",
            "PLS",
        ]
        data_table = guides_df.loc[keep_cols]
        data_table.rename(
            index={
                "CTCF-only": "CTCF", 
                "General": "Total", 
                "three_prime_UTR": "3'UTR", 
                "five_prime_UTR": "5'UTR",
            }, 
            inplace=True,
        )
        data_table.sort_values(by=["Percentage"], ascending=False, inplace=True)  
    except:
        data_table = guides_df.loc[["General"]]
        data_table.rename(index={"General": "Total"}, inplace=True)
    radar_chart_df = data_table.copy()
    if radar_chart_df.shape[0] > 1:
        radar_chart_df.drop(["Total"], inplace=True)
    radar_chart_df = radar_chart_df.T  # transpose data table
    radar_chart_cats = radar_chart_df.columns.tolist()
    data_table_cats = data_table.T.columns.tolist()  # categories still on rows
    radar_cats_count = len(radar_chart_cats)
    # plot first line of df 
    # NB: to close the circular graph we have to repeat the first value
    radar_chart_values = radar_chart_df.loc["Percentage"].values.flatten().tolist()
    radar_chart_values += radar_chart_values[:1]
    # define plot's angles
    radar_chart_angles = [
        n / float(radar_cats_count) * 2 * pi for n in range(radar_cats_count)
    ]
    radar_chart_angles += radar_chart_angles[:1]
    # initialize the spider plot
    ax = plt.subplot(2, 2, 1, polar=True)
    for label, rot in zip(ax.get_xticklabels(), radar_chart_angles):
        if rot == 0:
            label.set_horizontalalignment("center")
        if rot > 0:
            label.set_horizontalalignment("left")
        if rot > 3:
            label.set_horizontalalignment("center")
        if rot > 4:
            label.set_horizontalalignment("right")
    # draw one axe per variable + add labels labels yet
    plt.xticks(
        radar_chart_angles[:-1], radar_chart_cats, color="black", size=fontsize
    )
    # draw y labels
    ax.set_rlabel_position(0)
    radar_chart_max_value = round(max(radar_chart_values))
    # round to the closest multiple of 10
    while int(radar_chart_max_value % 10):
        radar_chart_max_value += 1
    radar_chart_yticks = [e for e in range(0, radar_chart_max_value, 10)]
    radar_chart_yticks_labels = [
        str(e) for e in range(0, radar_chart_max_value, 10)
    ]
    plt.yticks(
        radar_chart_yticks, radar_chart_yticks_labels, color="black", size=fontsize
    )
    plt.ylim(0, radar_chart_max_value)
    # fill plot area
    ax.fill(radar_chart_angles, radar_chart_values, color="b", alpha=.1)
    # y-axis position offset
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    # plot data
    ax.plot(
        radar_chart_angles, radar_chart_values, linewidth=1, linestyle="solid"
    )
    plt.subplot(2, 2, 2)
    transpose_list = [data_table.loc[cat].tolist() for cat in data_table_cats]
    tmplist = []
    for pair in transpose_list:
        pair[0] = int(pair[0])
        tmplist.append(pair)
    transpose_list = tmplist
    plt.axis("off")
    table = plt.table(
        cellText=transpose_list, 
        rowLabels=data_table_cats, 
        colLabels=["Count", "Percentage"],
        loc="best", 
        colWidths=[0.25, 0.35]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.5)
    total_motif = [0] * len(guide)
    for count in range(len(guide)):
        for nuc in motif_dict.keys():
            total_motif[count] += motif_dict[nuc][count]
    count_max = max(total_motif)
    for count in range(len(guide)):
        for nuc in motif_dict.keys():
            if count_max != 0:
                motif_dict[nuc][count] = float(
                    motif_dict[nuc][count] / float(count_max)
                )
    ind = np.arange(0, len(guide), 1)
    width = 0.7  # bars' width 
    motif = plt.subplot(2, 1, 2, frameon=False)
    a = np.array(motif_dict["A"], dtype=float)
    c = np.array(motif_dict["C"], dtype=float)
    g = np.array(motif_dict["G"], dtype=float)
    t = np.array(motif_dict["T"], dtype=float)
    rna = np.array(motif_dict["RNA"], dtype=float)
    dna = np.array(motif_dict["DNA"], dtype=float)
    p1 = plt.bar(ind, a, width, align="center")
    p2 = plt.bar(ind, c, width, bottom=a, align="center")
    p3 = plt.bar(ind, g, width, bottom=a+c, align="center")
    p4 = plt.bar(ind, t, width, bottom=c+g+a, align="center")
    p5 = plt.bar(ind, rna, width, bottom=c+g+a+t, align="center")
    p6 = plt.bar(ind, dna, width, bottom=c+g+a+t+rna, align="center")
    plt.xticks(ticks=ind, labels=[guide], size=fontsize)
    plt.yticks(size=fontsize)
    # add legend
    plt.legend(
        (p1[0], p2[0], p3[0], p4[0], p5[0], p6[0]),
        ("A", "C", "G", "T", "bRNA", "bDNA"), 
        fontsize=fontsize, 
        loc="upper left", 
        ncol=6
    )
    # add plot title
    plt.title(
        str(
            f"Mismatch and bulge distribution for targets with up to {total} "
            "mismatches and/or bulges"
        ), 
        color="black", 
        size=titlesize
    )
    # plots sup title
    plt.suptitle(
        str(
            f"Targets with up to {total} mismatches and/or bulges by "
            "ENCODE/GENCODE annotations"
        ),
        horizontalalignment="center", 
        color="black", 
        size=titlesize
    )
    plt.tight_layout()
    # store figures --> downloaded with results
    figname = str(
        f"summary_single_guide_{guide}_{mismatch}.{bulge}_{source}."
        f"ENCODE+GENCODE.{file_extension}"
    )
    plt.savefig(os.path.join(outdir, figname), format=file_extension)
    plt.close("all")  # close figure channel
    