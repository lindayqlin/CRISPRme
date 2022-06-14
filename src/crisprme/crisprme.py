"""
"""

from crisprme.crisprme_commands import CompleteSearch
from crisprme.utils import exception_handler

import sys

# CRISPRme version
__version__ = "2.1.0"


def complete_search(args: CompleteSearch) -> None:
    """launch CRISPRme complete search.

    ...

    Parameters
    ----------
    args : CompleteSearch
        Complete search input arguments

    Returns
    -------
    None
    """

    if not isinstance(args, CompleteSearch):
        exception_handler(
            TypeError,
            f"Exepected {CompleteSearch.__name__}, got {type(args).__name__}",
            args.debug
        )
    # job start message to stderr
    sys.stderr.write(
        f"Launching job {args.outname}. Stdout is redirected to log_verbose.txt. "
        "Stderr is redirected to log_error.txt"
    )
    try:
        # TODO: create log_verbose.txt and log_error.txt
        # TODO: launch crisprme complete-search function
        print("Running CRISPRme...")
    except:
        pass