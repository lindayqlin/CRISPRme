"""
"""

from crisprme.crisprme_commands import (
    CompleteSearch, GnomADConverter, TargetsIntegration, WebInterface
)
from crisprme.utils import exception_handler

import sys

# CRISPRme version
__version__ = "2.1.0"


def complete_search(args: CompleteSearch) -> None:
    """Launch CRISPRme complete search.

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


def gnomAD_converter(args: GnomADConverter) -> None:
    """Launch CRISPRme gnomAD converter command.

    ...

    Parameters
    ----------
    args : GnomADConverter
        GnomADConverter input arguments

    Returns
    -------
    None
    """

    if not isinstance(args, GnomADConverter):
        exception_handler(
            TypeError,
            f"Expected {GnomADConverter.__name__}, got {type(args).__name__}",
            args.debug
        )
    # job start message
    sys.stderr.write("Launching GnomAD VCF converter")
    try:
        print("Running gnomAD converter")
    except:
        pass


def targets_integration(args: TargetsIntegration) -> None:
    """Launch CRISPRme targets integration command.

    ...

    Parameters
    ----------
    args : TargetsIntegration
        TargetsIntegration input arguments

    Returns
    -------
    None
    """

    if not isinstance(args, TargetsIntegration):
        exception_handler(
            TypeError,
            f"Expected {TargetsIntegration.__name__}, got {type(args).__name__}",
            args.debug
        )
    # job start message
    sys.stderr.write("Launching Targets integration")
    try:
        print("Running targets integration")
    except:
        pass


def web_interface(args: WebInterface) -> None:
    """Launch CRISPRme web interface command.

    ...

    Parameters
    ----------
    args : WebInterface
        TargetsIntegration input arguments

    Returns
    -------
    None
    """

    if not isinstance(args, WebInterface):
        exception_handler(
            TypeError,
            f"Expected {WebInterface.__name__}, got {type(args).__name__}",
            args.debug
        )
    # job start message
    sys.stderr.write("Starting CRISPRme web interface")
    try:
        print("Running crisprme web interface")
    except:
        pass