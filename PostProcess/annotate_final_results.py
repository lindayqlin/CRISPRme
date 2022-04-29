"""Annotate the results obtained from CRISPRme off-target sites search using 
the genomic annotations chosen/provided by the user.
"""


from intervaltree import Interval, IntervalTree

import time
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def annotate_results(
    results_fname: str, annotation_file: str, annotated_file: str
) -> None:
    """Annotate the CRISPRme off-targets search results.

    ...

    Parameters
    ----------
    results_fname : str
        Results file
    annotation_file : str
        Annotation file
    annotated_file : str
        Annotated results file

    Returns
    -------
    None
    """

    if not isinstance(results_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(results_fname).__name__}"
        )
    if not os.path.isfile(results_fname):
        raise FileNotFoundError(f"Unable to locate {results_fname}")
    if not isinstance(annotation_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(annotation_file).__name__}"
        )
    if not os.path.isfile(annotation_file):
        raise FileNotFoundError(f"Unable to locate {annotation_file}")
    if not isinstance(annotated_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(annotated_file).__name__}"
        )
    start_time = time.time()  # begin annotation step
    annotations_tree = IntervalTree()
    annotations_set = set()
    # read annotation file
    try:
        handle = open(annotation_file, mode="r")
        for line in handle:
            line_split = line.split()
            annotations = str(line_split[3]).strip()
            annotations_tree[
                int(line_split[1]):int(line_split[2])
            ] = f"{line_split[0]}\t{annotations}"
            annotations_set.add(annotations)
    except OSError as e:
        raise e
    finally:
        handle.close()
    # annotate input file
    try:
        handle_res = open(results_fname, mode="r")
        handle_ann = open(annotated_file, mode="w")
        header = handle_res.readline()
        handle_ann.write(header)
        for line in handle_res:
            line_split = line.rstrip().split()
            guide_no_bulge = line_split[1].replace("-", "")
            # get annotations
            annotations = sorted(
                annotations_tree[
                    int(line_split[5]):(int(line_split[5]) + len(guide_no_bulge) + 1)
                ]
            )
            string_annotations = []
            found = False
            for i in range(len(annotations)):
                guide = annotations[i].data
                guides = guide.split()
                if (guides[0] == line_split[4]):
                    found = True
                    string_annotations.append(guides[1])
            ann_last = "n"  # N/A
            if found:
                ann_last = ",".join(list(set(string_annotations)))
            line_split[14] = ann_last  # update last annotation field
            handle_ann.write("".join(["\t".join(line_split), "\n"]))
    except OSError as e:
        raise e
    finally:
        handle_ann.close()
        handle_res.close()
    stop_time = time.time()
    print("Annotation completed in %.2fs" % (stop_time - start_time))


# TODO: avoid calling script
def main():
    results_fname = sys.argv[1]
    annotation_file = sys.argv[2] 
    annotated_file = sys.argv[3]
    annotate_results(results_fname, annotation_file, annotated_file)


if __name__ == "__main__":
    main()
