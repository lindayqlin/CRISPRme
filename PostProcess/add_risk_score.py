"""Compute the risk scores from scores stored in the input scores file. The 
resulting risk scores are stored in the output file along with the other info
stored in the original input file.
"""

import numpy as np

import sys
import os


def assign_risk_score(
    score_fname: str, outfile: str, alternate_genome: bool
) -> None:
    """Compute risk score and create a new scores file with the computed risk
    scores.

    ...

    Parameters
    ----------
    score_fname : str
        Scores file
    outfile : str
        Outfile
    alternate_genome : bool

    Returns
    -------
    None
    """
    
    if not isinstance(score_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(score_fname).__name__}"
        )
    if not os.path.isfile(score_fname):
        raise FileNotFoundError(f"Unable to locate {score_fname}")
    if not isinstance(outfile, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(outfile).__name__}"
        )
    # read score file
    try:
        handle_in = open(score_fname, mode="r") 
        handle_out = open(outfile, mode="w")
        header = handle_in.readline().strip().split()
        # add risk score columns
        header.append("Highest_CFD_Risk_Score")
        header.append("Highest_CFD_Absolute_Risk_Score")
        if alternate_genome:
            header.append("CLUSTER_ID")  # add guide cluster column
        header = "\t".join(header)
        handle_out.write(f"{header}\n")
        # read data from scores file
        for line in handle_in:
            line_split = line.strip().split()
            diff = float(line_split[20]) - float(line_split[21])
            line = "\t".join(line_split)
            handle_out.write(f"{line}\t{diff}\t{np.abs(diff)}\n")
    except OSError as e:
        raise e
    finally:
        handle_in.close()
        handle_out.close()


# TODO: remove main and use directly the function
def main():
    scores_file = sys.argv[1]
    outfile = sys.argv[2]
    alternate = sys.argv[3]
    if alternate == "True":
        alternate = True
    else:
        alternate = False
    assign_risk_score(scores_file, outfile, alternate)


if __name__ == "__main__":
    main()
