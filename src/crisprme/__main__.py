#!/usr/bin/env python
#
# GNU AFFERO GENERAL PUBLIC LICENSE
# Version 3, 19 November 2007
#
# CRISPRme
# 
# CRISPRme is a web based tool dedicated to perform predictive analysis and 
# result assessement on CRISPR/Cas experiments with a user-friendly GUI and the 
# precise scope of searching individual variant in VCF dateset.
#
# Copyright (C) 2022  Pinello Lab
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# If you plan to use the CRISRPme for-profit, YOU WILL NEED TO PURCHASE A LICENSE. 
# 
# Please contact rosalba.giugno@univr.it and lpinello@mgh.harvard.edu for more 
# information.


"""
CRISPRme version {version}

Copyright (C) 2022 Pinello Lab <lpinello@mgh.harvard.edu> <rosalba.giugno@univr.it>

CRISPRme

CRISPRme is a web based tool dedicated to perform predictive analysis and 
result assessement on CRISPR/Cas experiments with a user-friendly GUI and the 
precise scope of searching individual variant in VCF dateset.

Usage:
TODO: add usage examples

TODO: brief description on how CRISPRme works + output

Citation:
TODO: add citation

Run "crisprme --help" to see all command-line options.
See https://github.com/pinellolab/CRISPRme for the full documentation.
"""


from crisprme.crisprme_argsparser import CrisprmeArgumentParser 
from crisprme.crisprme import __version__
from crisprme.utils import (
    CRISPRme_COMMANDS, 
    CRISPRme_COMMANDS_ARGS,
    IUPAC_ALPHABET, 
    CRISPRme_DIRS,
    sigint_handler, 
    merge_annotation_files,
    check_directories_consistency,
    exception_handler, 
    parse_PAM_sequence_file,
)
from crisprme_location import CURRENT_WORKING_DIRECTORY, ORIGIN_PATH
from crisprme_commands import CompleteSearch

from typing import List, Optional
from argparse import Namespace
from time import time

import multiprocessing
import subprocess
import sys
import os

from src.crisprme.utils import parse_guide_sequences_file


def get_parser() -> CrisprmeArgumentParser:
    """Read command-line arguments.

    ...

    Parameters
    ----------
    None

    Returns
    -------
    CrisprmeArgumentParser
        Parsed command-line arguments
    """

    # parse command-line args
    parser = CrisprmeArgumentParser(usage=__doc__, add_help=False)
    # crisprme options shared by all commands
    group = parser.add_argument_group("General options")
    group.add_argument(
        "-h", "--help", action="help", help="Show the help and exit."
    )
    group.add_argument(
        "--version", 
        action="version", 
        help="Show CRISPRme version and exit.", 
        version=__version__
    )
    group.add_argument(
        "-j", 
        "--threads",
        type=int,
        default=8,
        metavar="NTHREADS",
        nargs="?",
        const=8,
        dest="threads",
        help="Number of threads used by CRISPRme. Use 0 to autodetect the "
             "maximum number of available threads. Default: %(default)."
    )
    group.add_argument(
        "command",
        type=str,
        default="",
        help="CRISPRme operation to perform. The argument must be place "
             "immediately after \"crisprme\". Available commands: "
             "\n\t- complete-search"
             "\n\t\tautomated complete off-targets search."
             "\n\t- gnomAD-converter"
             "\n\t\tVCF gnomAD converter to convert gnomADv3.1 VCFs to VCFs "
             "supported by CRIPRme."
             "\n\t- targets-integration"
             "\n\t\tresults integration process to generate target panels."
             "\n\t- web-interface"
             "\n\t\tstarts a local server to use the web interface."
             "\n\t- generate-personal-card"
             "\n\t\trecover and store all the private targets for the input sample."
    )
    # group.add_argument(
    #     "--wd",
    #     type=str,
    #     metavar="WORKING-DIRECTORY",
    #     default=os.getcwd(),
    #     dest="working_directory",
    #     help="Set CRISPRme root working directory. By default is set to the "
    #          "current directory."
    # )
    group.add_argument(
        "--verbose",
        default=False,
        action="store_true",
        help="Print additional information during CRISPRme run."
    )
    group.add_argument(
        "--debug",
        default=False,
        action="store_true",
        dest="debug",
        help="Enable error traceback."
    )
    # complete-search arguments
    group = parser.add_argument_group("complete-search options")
    group.add_argument(
        "-g", 
        "--genome", 
        type=str,
        nargs="?",
        default="",
        metavar="REF-GENOME-DIR",
        dest="genome",
        help="Reference genome directory."
    )
    group.add_argument(
        "-v",
        "--vcf",
        type=str, 
        nargs="?",
        default="_",
        metavar="VCF-FILE",
        dest="vcf",
        help="File containing a list of VCF directories (one per line)."
    )
    group.add_argument(
        "-u",
        "--guide",
        type=str,
        default="",
        metavar="GUIDE-FILE",
        dest="guide_file",
        help="File containing the guides used during the search (cannot be used "
             "if --sequence argument has been selected)."
    )
    group.add_argument(
        "-s",
        "--sequence",
        type=str,
        nargs="?",
        default="",
        metavar="VCF-FILE",
        dest="sequence_guides",
        help="File containing DNA sequences or BED coordinates to extract guides."
    )
    group.add_argument(
        "-p",
        "--pam",
        type=str,
        default="",
        metavar="PAM",
        dest="pam",
        help="File containing PAM."
    )
    group.add_argument(
        "--be-window",
        type=str,
        nargs="?",
        default="",
        metavar="START,STOP",
        dest="be_window",
        help="Window to search for susceptibilty to certain base editor."
    )
    group.add_argument(
        "--be-base",
        type=str,
        default="",
        metavar="BASE1, BASE2, ...",
        dest="be_nucleotide",
        help="Specify the base(s) to check for the choosen editor."
    )
    group.add_argument(
        "-a",
        "--annotation",
        type=str,
        nargs="?",
        default="",
        metavar="ANNOTATION-FILE",
        dest="annotation",
        help="File containing annotations for the reference genome."
    )
    group.add_argument(
        "--personal-annotation",
        type=str,
        nargs="?",
        default="",
        metavar="PERSONAL-ANNOTATION-FILE",
        dest="personal_annotation",
        help="File containing personal annotations for the reference genome."
    )
    group.add_argument(
        "--samples",
        type=str,
        nargs="?",
        default="",
        metavar="SAMPLES-FILE",
        dest="samples_file",
        help="File containing a list of files (one per line) storing the "
             "information about samples in the input VCFs."
    )
    group.add_argument(
        "--gene-annotation",
        type=str,
        nargs="?",
        default="",
        metavar="GENE-ANNOTATION",
        dest="gene_annotation",
        help="Specify annotation to find nearest gene for each found target "
             "(E.g. Gencode)"
    )
    group.add_argument(
        "--mm",
        type=str,
        nargs="?",
        default="",
        metavar="MISMATCHES",
        dest="mm",
        help="Number of allowed mismatches during off-targets search."
    )
    group.add_argument(
        "--bDNA",
        type=int,
        nargs="?",
        default=0,
        metavar="BULGES",
        dest="bdna",
        help="Number of allowed DNA bulges during off-targets search."
    )
    group.add_argument(
        "--bRNA",
        type=int,
        nargs="?",
        default=0,
        metavar="BULGES",
        dest="brna",
        help="Number of allowed RNA bulges during off-targets search."
    )
    group.add_argument(
        "--merge",
        type=int,
        nargs="?",
        default=3,
        metavar="MERGE-THRESHOLD",
        dest="merge",
        help="Specify the threshold (number of close nucleotides) used to merge "
             "close targets"
    )
    group.add_argument(
        "-o",
        "--output",
        type=str,
        nargs="?",
        metavar="OUTPUT-NAME",
        dest="output_name",
        help="Output name for the results."
    )


def complete_search_input_check(
    args: Namespace, parser: CrisprmeArgumentParser
) -> None:
    """Check arguments consistency for complete search CRISPRme command.

    ...

    Parameters
    ----------
    args : Namespace
        Complete search input arguments 
    parser : CrisprmeArgumentParser
        Parsed input arguments
    
    Returns
    -------
    None
    """

    if not isinstance(args, Namespace):
        exception_handler(
            TypeError,
            f"Exepcted {Namespace.__name__}, got {type(args).__name__}",
            args.debug
        )
    if not isinstance(parser, CrisprmeArgumentParser):
        exception_handler(
            TypeError,
            f"Expected {CrisprmeArgumentParser.__name__}, got {type(parser).__name__}",
            args.debug
        )
    # check if only complete-search arguments have been given
    if any(
        [
            a not in CRISPRme_COMMANDS[CRISPRme_COMMANDS[0]] for a in vars(args).keys()
        ]
    ):
        # if found something, raise error
        parser.error("Wrong arguments given to \"complete-search\" command")
    # check base editing
    if bool(args.be_window) and not args.be_nucleotide:
        parser.error(
            f"Unspecified base(s) editor to check within the specified window"
        )
    if bool(args.be_nucleotide) and not args.be_window:
        parser.error(f"Unspecified base window to check for the input base")
    # check base editor input check
    base_start = 1
    base_stop = 0
    be_nucleotide = "_"
    if args.be_window:
        be_window = args.be_window
        try:
            base_start, base_stop = be_window.strip().split(",")
            base_start = int(base_start)
            base_stop = int(base_stop)
        except:
            parser.error("Wrong base editor window given")
    if args.be_nucleotide:
        be_nucleotide = args.be_nucleotide
        for nt in be_nucleotide.strip().split(","):
            if nt not in IUPAC_ALPHABET:
                parser.error(f"Forbidden IUPAC character found ({nt})")
    # check guide and sequence existence
    if not args.guide_file and not args.sequence_guides:
        parser.error(f"Missing both guides file and sequence file.")
    if args.guide_file and args.sequence_guides:
        parser.error(
            "Only one argument between \"--guide\" and \"--sequence\" is allowed"
        )
    if args.guide_file:
        guide_file = os.path.abspath(args.guide_file)
    if not os.path.isfile(guide_file):
        parser.error(f"Unable to locate {args.guide_file}")
    useseqs = False
    if args.sequence_guides:
        sequence_guides = os.path.abspath(args.sequence_guides)
        useseqs = True
    if not os.path.isfile(sequence_guides):
        parser.error(f"Unable to locate {args.sequence_guides}")
    # check input genome
    if not args.genome:
        parser.error("Missing reference genome")
    else:
        genome = os.path.abspath(args.genome)
        if not os.path.isdir(genome):
            parser.error(f"Unable to locate {args.genome}")
    # check VCF input file
    variant = True
    if args.vcf == "_":  # no VCF provided
        variant = False
    else:
        vcf = os.path.abspath(args.vcf)
        if not os.path.isfile(vcf):
            parser.error(f"Unable to locate {args.vcf}")
    # check functional annotation
    if not args.annotation:
        if args.verbose:
            sys.stderr.write("WARNING: --annotation not used")
        annotation = os.path.join(ORIGIN_PATH, "empty.txt")
    else:
        annotation = os.path.abspath(args.annotation)
        if not os.path.isfile(annotation):
            parser.error(f"Unable to locate {args.annotation}")
        if args.personal_annotation:
            personal_annotation = os.path.abspath(args.personal_annotation)
            if not os.path.isfile(personal_annotation):
                parser.error(f"Unable to locate {args.personal_annotation}")
            # merge functional annotation and personal annotation files
            annotation = merge_annotation_files(annotation, personal_annotation)
    # check gene annotation input
    if not args.gene_annotation:
        gene_annotation = os.path.join(ORIGIN_PATH, "empty.txt")
    else:
        gene_annotation = os.path.abspath(args.gene_annotation)
        if not os.path.isfile(gene_annotation):
            parser.error(f"Unable to locate {args.gene_annotation}")
    # check personal annotation input
    if args.personal_annotation and not args.annotation:
        personal_annotation = os.path.abspath(args.personal_annotation)
        if not os.path.isfile(personal_annotation):
            parser.error(f"Unable to locate {args.personal_annotation}")
        # merge functional annotation and personal annotation files
        annotation = merge_annotation_files(annotation, personal_annotation)
    # check input PAM
    if not args.pam:
        parser.error("Missing PAM file")
    else:
        pam = os.path.abspath(args.pam)
        if not os.path.isfile(pam):
            parser.error(f"Unable to locate {args.pam}")
    # check input data for variant search (check the existence of all files)
    samples_file = os.path.join(ORIGIN_PATH, "empty.txt")  # use empty files by default
    if variant and args.samples_file:
        parser.error(
            "Samples are required to perform CRISPRme search accounting for variants"
        )
    elif not variant and args.samples_file:
        parser.error("Samples provided, but VCF is missing")
    elif args.samples_file:
        samples_file = os.path.abspath(args.samples_file)
        if not os.path.isfile(samples_file):
            parser.error(f"Unable to locate {args.samples_file}") 
    # check input mismatches
    if not args.mm:
        parser.error("Missing number of mismatches")
    else:
        try:
            mm = int(args.mm)
        except ValueError as verr:
            parser.error(
                f"Forbidden number of mismatches provided ({args.mm})"
            )
        except Exception as e:
            parser.error(
                "A problem occurred while reading the number of mismatches"
            )
        if mm < 0:
            parser.error(f"Forbidden number of mismatches given ({mm})")
    # check input DNA bulges
    if args.bdna != 0:
        assert isinstance(args.bdna, int)
        if args.bdna < 0:
            parser.error(f"Forbidden number of DNA bulges given {args.bdna}")
        bdna = args.bdna
    # check input RNA bulges
    if args.brna != 0:
        assert isinstance(args.brna, int)
        if args.brna < 0:
            parser.error(f"Forbidden number of DNA bulges given {args.rdna}")
        brna = args.brna
    # set bmax to generate index as maximum value between DNA and RNA bulges
    bmax = max(bdna, brna)
    # check input for merge window
    if args.merge != 3:
        assert isinstance(args.merge, int)
        if args.merge < 0:
            parser.error(f"Forbidden merge threshold value ({args.merge})")
        merge_thresh = args.merge
    # TODO: maybe move output directory check on top
    if not args.output_name:
        parser.error("Missing results name")
    else:
        outname = args.output_name
        outdir = os.path.join(
            CURRENT_WORKING_DIRECTORY, CRISPRme_DIRS[1], outname
        )
        if not os.path.exists(outdir):  
            # if the output directory does not exists, create it
            os.makedirs(outdir)
        # make sure that the results directory exists
        if not os.path.isdir(outdir):
            parser.error(f"Unable to locate {outdir}")
    # recover PAM sequences from file
    pam_seq, pam_length, pam_total_length, pam_start = parse_PAM_sequence_file(
        pam, args.debug
    )
    # recover directories basename
    ref_genome = os.path.basename(genome)
    annotation_bname = os.path.basename(annotation)
    nuclease = os.path.basename(pam).split(".")[0].split("-")[2]
    # set search index
    search_index = True if bmax != 0 else False
    # set genome indexes
    if variant:  # search accounting for variants
        genome_index_list = []
        try:
            with open(vcf, mode="r") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        if line[-1] == "/":
                            line = line[:-1]
                        vcf_bname = os.path.basename(line)
                        genome_index_list.append(
                            f"{pam_seq}_{bmax}_{ref_genome}+{vcf_bname}"
                        )
        except:
            exception_handler(OSError, f"Unable to parse {vcf}", args.debug)
        genome_index = ",".join(genome_index_list)
        ref_comparison = True  # compare variant results with reference
    else:  # search only on reference genome
        genome_index = f"{pam_seq}_{bmax}_{ref_genome}"
        ref_comparison = False  # no required comparison
    guide_length = pam_total_length - pam_length  # compute guide length
    # recover the guides from sequence file
    if useseqs: 
        guides = parse_guide_sequences_file(
            sequence_guides, 
            genome, 
            pam_seq, 
            pam_length, 
            guide_length,
            pam_start,
            args.debug
        )
        # write guides to guides.txt
        try:
            with open(os.path.join(outdir, "guides.txt"), mode="w") as handle:
                for guide in guides:
                    handle.write(f"{guide}\n")
        except OSError as oserr:
            exception_handler(
                OSError, f"Unable to write `guides.txt`", args.debug
            )
        finally:
            handle.close()  # close out stream
    # force empty mail value
    mail_empty = "_"
    if not useseqs:
        # copy guides file to guides.txt
        cmd = f"cp {guide_file} {os.path.join(outdir, 'guides.txt')}"
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            exception_handler(
                subprocess.SubprocessError,
                f"An error occurred while running {cmd}",
                args.debug
            )
    guides = os.path.join(outdir, "guides.txt")  # assign guides file
    # create complete-search object
    complete_search = CompleteSearch(
        args.threads,
        args.verbose,
        args.debug,
        ref_genome, 
        search_index, 
        genome_index, 
        guides,
        pam_seq, 
        bmax, 
        mm, 
        bdna, 
        brna, 
        annotation,
        nuclease, 
        ref_comparison, 
        outname,
        outdir
    )
    complete_search.write_params_file()  # write the selected input parameters
    # return an object with carrying all the input arguments
    return complete_search 


def main(cmdline_args: Optional[List[str]] = None) -> None:
    """CRISPRme's main.

    ...

    Parameters
    ----------
    cmdline_args : List
        Command-line arguments

    Returns
    -------
    None
    """

    try:
        start = time()  # start CRISPRme
        parser = get_parser()  # parse commad-line args
        if cmdline_args is None:
            cmdline_args = sys.argv[1:]  # read command-line args
        # no argument given --> print help
        if len(cmdline_args) == 0:
            parser.error_noargs()  # print help message
        # check crisprme command
        crisprme_command = cmdline_args[0]
        if (
            crisprme_command != "-h" and 
            crisprme_command != "--help" and
            crisprme_command != "--version" and 
            crisprme_command not in CRISPRme_COMMANDS
        ):
            parser.error(
                "Forbidden second argument. Run \"crisprme --help\" to see usage."
            )
        args = parser.parse_args(cmdline_args)
        if args.verbose:
            sys.stderr.write("Parsing command-line arguments...") 
        # check CRISPRme directory tree
        check_directories_consistency(args.debug)
        # check commandline args consistency
        # - workflow
        if args.command not in CRISPRme_COMMANDS:
            parser.error(
                "Forbidden CRISPRme command provided. Run \"crisprme --help\" "
                "to see usage."
            )
        # - threads
        if args.threads < 0:
            parser.error(f"Wrong number of threads ({args.threads})")
        elif args.threads == 0:  # autodetect number of threads
            args.threads = multiprocessing.cpu_count()
        else:  
            if args.threads > multiprocessing.cpu_count():
                parser.error(
                    f"Unable to create {args.threads} threads (Maximum = {multiprocessing.cpu_count()})."
                )
        # - debug
        if not isinstance(args.debug, bool):
            parser.error("\"--debug\" does not accept any positional argument")
        # complete-search argument check
        if crisprme_command == CRISPRme_COMMANDS[0]:
            workflow = complete_search_input_check(args, parser)
            # # check base editing
            # if bool(args.be_window) and not args.be_nucleotide:
            #     parser.error(
            #         f"Unspecified base(s) editor to check within the specified window"
            #     )
            # if bool(args.be_nucleotide) and not args.be_window:
            #     parser.error(f"Unspecified base window to check for the input base")
            # # check base editor input check
            # base_start = 1
            # base_stop = 0
            # be_nucleotide = "_"
            # if args.be_window:
            #     be_window = args.be_window
            #     try:
            #         base_start, base_stop = be_window.strip().split(",")
            #         base_start = int(base_start)
            #         base_stop = int(base_stop)
            #     except:
            #         parser.error("Wrong base editor window given")
            # if args.be_nucleotide:
            #     be_nucleotide = args.be_nucleotide
            #     for nt in be_nucleotide.strip.split(","):
            #         if nt not in IUPAC_ALPHABET:
            #             parser.error(f"Forbidden IUPAC character found ({nt})")
            # # check guide and sequence existence
            # if not args.guide_file and not args.sequence_guides:
            #     parser.error(f"Missing both guides file and sequence file.")
            # if args.guide_file and args.sequence_guides:
            #     parser.error(
            #         "Only one argument between \"--guide\" and \"--sequence\" is allowed"
            #     )
            # if args.guide_file:
            #     guide_file = os.path.abspath(args.guide_file)
            # if not os.path.isfile(guide_file):
            #     parser.error(f"Unable to locate {args.guide_file}")
            # useseqs = False
            # if args.sequence_guides:
            #     sequence_guides = os.path.abspath(args.sequence_guides)
            #     useseqs = True
            # if not os.path.isfile(sequence_guides):
            #     parser.error(f"Unable to locate {args.sequence_guides}")
            # # check input genome
            # if not args.genome:
            #     parser.error("Missing reference genome")
            # else:
            #     genome = os.path.abspath(args.genome)
            #     if not os.path.isdir(genome):
            #         parser.error(f"Unable to locate {args.genome}")
            # # check VCF input file
            # variant = True
            # if args.vcf == "_":  # no VCF provided
            #     variant = False
            # else:
            #     vcf = os.path.abspath(args.vcf)
            #     if not os.path.isfile(vcf):
            #         parser.error(f"Unable to locate {args.vcf}")
            # # check functional annotation
            # if not args.annotation:
            #     if args.verbose:
            #         sys.stderr.write("WARNING: --annotation not used")
            #     annotation = os.path.join(ORIGIN_PATH, "empty.txt")
            # else:
            #     annotation = os.path.abspath(args.annotation)
            #     if not os.path.isfile(annotation):
            #         parser.error(f"Unable to locate {args.annotation}")
            #     if args.personal_annotation:
            #         personal_annotation = os.path.abspath(args.personal_annotation)
            #         if not os.path.isfile(personal_annotation):
            #             parser.error(f"Unable to locate {args.personal_annotation}")
            #         # merge functional annotation and personal annotation files
            #         annotation = merge_annotation_files(
            #             annotation, personal_annotation
            #         )
            # # check gene annotation input
            # if not args.gene_annotation:
            #     gene_annotation = os.path.join(ORIGIN_PATH, "empty.txt")
            # else:
            #     gene_annotation = os.path.abspath(args.gene_annotation)
            #     if not os.path.isfile(gene_annotation):
            #         parser.error(f"Unable to locate {args.gene_annotation}")
            # # check personal annotation input
            # if args.personal_annotation and not args.annotation:
            #     personal_annotation = os.path.abspath(args.personal_annotation)
            #     if not os.path.isfile(personal_annotation):
            #         parser.error(f"Unable to locate {args.personal_annotation}")
            #     # merge functional annotation and personal annotation files
            #     annotation = merge_annotation_files(
            #         annotation, personal_annotation
            #     )
            # # check input PAM
            # if not args.pam:
            #     parser.error("Missing PAM file")
            # else:
            #     pam = os.path.abspath(args.pam)
            #     if not os.path.isfile(pam):
            #         parser.error(f"Unable to locate {args.pam}")
            # # check input data for variant search (check the existence of all files)
            # samples_file = os.path.join(ORIGIN_PATH, "empty.txt")  # use empty files by default
            # if variant and args.samples_file:
            #     parser.error(
            #         "Samples are required to perform CRISPRme search accounting for variants"
            #     )
            # elif not variant and args.samples_file:
            #     parser.error("Samples provided, but VCF is missing")
            # elif args.samples_file:
            #     samples_file = os.path.abspath(args.samples_file)
            #     if not os.path.isfile(samples_file):
            #         parser.error(f"Unable to locate {args.samples_file}") 
            # # check input mismatches
            # if not args.mm:
            #     parser.error("Missing number of mismatches")
            # else:
            #     try:
            #         mm = int(args.mm)
            #     except ValueError as verr:
            #         parser.error(
            #             f"Forbidden number of mismatches provided ({args.mm})"
            #         )
            #     except Exception as e:
            #         parser.error(
            #             "A problem occurred while reading the number of mismatches"
            #         )
            #     if mm < 0:
            #         parser.error(f"Forbidden number of mismatches given ({mm})")
            # # check input DNA bulges
            # if args.bdna != 0:
            #     assert isinstance(args.bdna, int)
            #     if args.bdna < 0:
            #         parser.error(f"Forbidden number of DNA bulges given {args.bdna}")
            #     bdna = args.bdna
            # # check input RNA bulges
            # if args.brna != 0:
            #     assert isinstance(args.brna, int)
            #     if args.brna < 0:
            #         parser.error(f"Forbidden number of DNA bulges given {args.rdna}")
            #     brna = args.brna
            # # set bmax to generate index as maximum value between DNA and RNA bulges
            # bmax = max(bdna, brna)
            # # check input for merge window
            # if args.merge != 3:
            #     assert isinstance(args.merge, int)
            #     if args.merge < 0:
            #         parser.error(f"Forbidden merge threshold value ({args.merge})")
            #     merge_thresh = args.merge
            # # TODO: maybe move output directory check on top
            # if not args.output_name:
            #     parser.error("Missing results name")
            # else:
            #     outname = args.output_name
            #     outdir = os.path.join(
            #         CURRENT_WORKING_DIRECTORY, CRISPRme_DIRS[1], outname
            #     )
            #     if not os.path.exists(outdir):  
            #         # if the output directory does not exists, create it
            #         os.makedirs(outdir)
            #     # make sure that the results directory exists
            #     if not os.path.isdir(outdir):
            #         parser.error(f"Unable to locate {outdir}")
            # # recover PAM sequences from file
            # pam_seq, pam_length, pam_total_length, pam_start = parse_PAM_sequence_file(
            #     pam, args.debug
            # )
            # # recover directories basename
            # ref_genome = os.path.basename(genome)
            # annotation_bname = os.path.basename(annotation)
            # nuclease = os.path.basename(pam).split(".")[0].split("-")[2]
            # # set search index
            # search_index = True if bmax != 0 else False
            # # set genome indexes
            # if variant:  # search accounting for variants
            #     genome_index_list = []
            #     try:
            #         with open(vcf, mode="r") as handle:
            #             for line in handle:
            #                 line = line.strip()
            #                 if line:
            #                     if line[-1] == "/":
            #                         line = line[:-1]
            #                     vcf_bname = os.path.basename(line)
            #                     genome_index_list.append(
            #                         f"{pam_seq}_{bmax}_{ref_genome}+{vcf_bname}"
            #                     )
            #     except:
            #         exception_handler(OSError, f"Unable to parse {vcf}", args.debug)
            #     genome_index = ",".join(genome_index_list)
            #     ref_comparison = True  # compare variant results with reference
            # else:  # search only on reference genome
            #     genome_index = f"{pam_seq}_{bmax}_{ref_genome}"
            #     ref_comparison = False  # no required comparison
            # # create complete-search object
            # complete_search = CompleteSearch(
            #     ref_genome, 
            #     search_index, 
            #     genome_index, 
            #     pam_seq, 
            #     bmax, 
            #     mm, 
            #     bdna, 
            #     brna, 
            #     annotation,
            #     nuclease, 
            #     ref_comparison, 
            #     outdir
            # )
            # # write Params.txt file
            # complete_search.write_params_file()
            # guide_length = pam_total_length - pam_length  # compute guide length
            # # recover the guides from sequence file
            # if useseqs: 
            #     guides = parse_guide_sequences_file(
            #         sequence_guides, 
            #         genome, 
            #         pam_seq, 
            #         pam_length, 
            #         guide_length,
            #         pam_start,
            #         args.debug
            #     )
            #     # write guides to guides.txt
            #     try:
            #         with open(
            #             os.path.join(outdir, "guides.txt"), mode="w"
            #         ) as handle:
            #             for guide in guides:
            #                 handle.write(f"{guide}\n")
            #     except OSError as oserr:
            #         exception_handler(
            #             OSError, f"Unable to write `guides.txt`", args.debug
            #         )
            #     finally:
            #         handle.close()  # close out stream
            # # force empty mail value
            # mail_empty = "_"
            # if not useseqs:
            #     # copy guides file to guides.txt
            #     cmd = f"cp {guide_file} {os.path.join(outdir, 'guides.txt')}"
            #     code = subprocess.call(cmd, shell=True)
            #     if code != 0:
            #         exception_handler(
            #             subprocess.SubprocessError,
            #             f"An error occurred while running {cmd}",
            #             args.debug
            #         )
            # # job start message to stderr
            # sys.stderr.write(
            #     f"Launching job {outname}. Stdout is redirected to log_verbose.txt. "
            #     "Stderr is redirected to log_error.txt"
            # )
            # start complete search
            # TODO: main script
        if args.verbose:
            sys.stderr.write("Arguments parsing finished") 
    except KeyboardInterrupt:
        sigint_handler()
    finally:
        pass


# entry point 
if __name__ == "__main__":
    main()

