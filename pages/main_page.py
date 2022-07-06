"""Build the layout of the main webopage of CRISPRme.
The main webpage read the input data and manages the analysis.
"""


from seq_script import extract_seq, convert_pam
from .pages_utils import (
    ANNOTATIONS_DIR,
    DNA_ALPHABET,
    EMAIL_FILE,
    GENOMES_DIR,
    GITHUB_LINK,
    GUIDES_FILE,
    JOBID_ITERATIONS_MAX,
    JOBID_MAXLEN,
    LOG_FILE,
    PAMS_DIR,
    PAMS_FILE,
    PARAMS_FILE,
    POSTPROCESS_DIR,
    PREPRINT_LINK,
    QUEUE_FILE,
    RESULTS_DIR,
    SAMPLES_FILE_LIST,
    VALID_CHARS,
    VARIANTS_DATA,
    select_same_len_guides,
    get_available_PAM,
    get_available_CAS,
    get_custom_VCF,
    get_available_genomes,
    get_custom_annotations,
)
from app import (
    URL,
    app,
    operators,
    current_working_directory,
    app_main_directory,
    DISPLAY_OFFLINE,
    ONLINE,
    exeggutor,
)

from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from typing import Dict, List, Tuple
from datetime import datetime

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

import collections
import subprocess
import filecmp
import random
import string
import os


# Allowed mismatches and bulges
# ONLINE = False  # NOTE change to True for online version, False for offline
if ONLINE:
    MAX_MMS = 7  # max allowed mismatches
    MAX_BULGES = 3  # max allowed bulges
else:
    # NOTE modify value for increasing/decreasing max mms or bulges available on
    # Dropdown selection
    MAX_MMS = 7  # max allowed mismatches
    MAX_BULGES = 3  # max allowed bulges
# mismatches, bulges and guides values
AV_MISMATCHES = [{"label": i, "value": i} for i in range(MAX_MMS)]
AV_BULGES = [{"label": i, "value": i} for i in range(MAX_BULGES)]
AV_GUIDE_SEQUENCE = [{"label": i, "value": i} for i in range(15, 26)]
# base editing options
BE_NTS = [{"label": nt, "value": nt} for nt in DNA_ALPHABET]  


def split_filter_part(filter_part: str) -> Tuple:
    """Recover filtering operator.

    ...

    Paramters
    --------
    filter_part : str
        Filter

    Returns
    -------
    Tuple
    """

    if not isinstance(filter_part, str):
        raise TypeError(f"Expected {str.__name__}, got {type(filter_part).__name__}")
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[(name_part.find("{") + 1) : name_part.rfind("}")]
                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace(f"\\{v0}", v0)
                else:
                    try:
                        value = float(value_part)
                    except:
                        value = value_part
                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value
    return [None] * 3


# load example data
@app.callback(
    [
        Output("text-guides", "value"),
        Output("available-cas", "value"),
        Output("available-pam", "value"),
        Output("available-genome", "value"),
        Output("checklist-variants", "value"),
        Output("mms", "value"),
        Output("dna", "value"),
        Output("rna", "value"),
        Output("be-window-start", "value"),
        Output("be-window-stop", "value"),
        Output("be-nts", "value"),
    ],
    [Input("load-example-button", "n_clicks")],
)
def load_example_data(load_button_click: int) -> List[str]:
    """Load data for CRISPRme example run.

    ...

    Parameters
    ----------
    load_button_click : int
        Click on "Load Example" button

    Returns
    -------
    List
        Example parameters
    """

    return [
        "CTAACAGTTGCTTTTATCAC",
        "SpCas9",
        "20bp-NGG-SpCas9",
        "hg38",
        ["1000G"],
        "6",
        "2",
        "2",
        "4",
        "8",
        "A"
    ]


# Job submission and results URL definition
@app.callback(
    [Output("url", "pathname"), Output("url", "search")],
    [Input("submit-job", "n_clicks")],
    [
        State("url", "href"),
        State("available-cas", "value"),
        State("available-genome", "value"),
        State("checklist-variants", "value"),
        State("checklist-annotations", "value"),
        State("vcf-dropdown", "value"),
        State("annotation-dropdown", "value"),
        State("available-pam", "value"),
        State("radio-guide", "value"),
        State("text-guides", "value"),
        State("mms", "value"),
        State("dna", "value"),
        State("rna", "value"),
        State("be-window-start", "value"),
        State("be-window-stop", "value"),
        State("be-nts", "value"),
        State("checklist-mail", "value"),
        State("example-email", "value"),
        State("job-name", "value"),
    ],
)
def change_url(
    n: int,
    href: str,
    nuclease: str,
    genome_selected: str,
    ref_var: List,
    annotation_var: List,
    vcf_input: str,
    annotation_input: str,
    pam: str,
    guide_type: str,
    text_guides: List[str],
    mms: int,
    dna: int,
    rna: int,
    be_start: int,
    be_stop: int,
    be_nt: str,
    adv_opts: List,
    dest_email: str,
    job_name: str,
) -> Tuple[str, str]:
    """Launch the targets search and generates the input files for
    post-processing operations, and results visualization.

    It manages the input data given by the user in the main webpage of CRISPRme
    and run the search, notify the user by sending an email when the job is
    completed, and produce the link to the webpage used to visualize the results.

    ** Further details **

    Perform checks on input parameters' consistency.

    To each received job is assigned a different identifier (or job name). This
    allows to easily recognize different job submissions. The job IDs consist
    in alpha-numeric strings of 10 characters (A-z 0-9). The IDs are randomly
    generated. If the generated ID is already assigned to some other job,
    compute another ID. Every 7 iterations, add +1 to ID length (up to 20 chars
    as max length). Once generated the ID, create the job directory. Within the
    job directory, create the `queue.txt` file (for job queueing).

    If the input parameters match those of an already processed search, the
    current job ID is modified to match that of the available analysis (even if
    completed/currently submitted/in queue). Update the email address associated
    to the job and reset the 3 days availability of the results.

    The current policy of CRISPRme allows up to 2 jobs to run concurrently. The
    others are put in queue.

    ...

    Parameters
    ----------
    n : int
        Clicks
    href : str
        URL
    nuclease : str
        Selected nuclease
    genome_selected : str
        Selected genome
    ref_var : List
        Variants
    annotation_var : str
        Annotation variants
    vcf_input : str
        Input VCF
    annotation_input : str
        Annotation file
    pam : str
        Selected PAM
    guide_type : str
        RNA guide type
    text_guides : str
        Input guides
    mms : int
        Number of mismatches
    dna : int
        Number of DNA bulges
    rna : int
        Number of RNA bulges
    adv_opts : List
        Selected advanced options
    dest_email : str
        User mail address
    job_name : str
        Submitted job ID

    Returns
    -------
    Tuple[str, str]
        URL to retrieve CRISPRme analysis results
    """

    if n is not None:
        if not isinstance(n, int):
            raise TypeError(f"Expected {int.__name__}, got {type(n).__name__}")
    if not isinstance(href, str):
        raise TypeError(f"Expected {str.__name__}, got {type(href).__name__}")
    if nuclease is not None:
        if not isinstance(nuclease, str):
            raise TypeError(f"Expected {str.__name__}, got {type(nuclease).__name__}")
    if genome_selected is not None:
        if not isinstance(genome_selected, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(genome_selected).__name__}"
            )
    if not isinstance(ref_var, list):
        raise TypeError(f"Expected {list.__name__}, got {type(ref_var).__name__}")
    if pam is not None:
        if not isinstance(pam, str):
            raise TypeError(f"Exepcted {str.__name__}, got {type(pam).__name__}")
    if text_guides is not None:
        if not isinstance(text_guides, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(text_guides).__name__}"
            )
    # if rna is not None:
    #     if not isinstance(rna, int):
    #         raise TypeError(f"Expected {str.__name__}, got {type(rna).__name__}")
    # if dna is not None:
    #     if not isinstance(dna, int):
    #         raise TypeError(f"Expected {str.__name__}, got {type(dna).__name__}")
    if adv_opts is not None:
        if not isinstance(adv_opts, list):
            raise TypeError(f"Expected {list.__name__}, got {type(adv_opts).__name__}")
    if dest_email is not None:
        if not isinstance(dest_email, str):
            raise TypeError(f"Expected {str.__name__}, got {type(dest_email).__name__}")
    if job_name is not None:
        if not isinstance(job_name, str):
            raise TypeError(f"Expected {str.__name__}, got {type(job_name).__name__}")
    if n is None:
        raise PreventUpdate  # do not update the page
    # job start
    print("Launching JOB")
    # ---- Check input. If fails, give simple input
    if (genome_selected is None) or (not genome_selected):
        genome_selected = "hg38_ref"  # use hg38 by default
    if (pam is None) or (not pam):
        pam = "20bp-NGG-SpCas9"  # use Cas9 PAM
        guide_seqlen = 20  # set guide length to 20
    else:
        for c in pam.split("-"):
            if "bp" in c:  # use length specified in PAM
                guide_seqlen = int(c.replace("bp", ""))
    if (text_guides is None) or (not text_guides):
        text_guides = "A" * guide_seqlen
    elif guide_type != "GS":
        text_guides = text_guides.strip()
        if not all(
            [
                len(guide) == len(text_guides.split("\n")[0])
                for guide in text_guides.split("\n")
            ]
        ):
            text_guides = select_same_len_guides(text_guides)
    # remove Ns from guides
    guides_tmp = "\n".join(
        [guide.replace("N", "") for guide in text_guides.split("\n")]
    )
    text_guides = guides_tmp.strip()
    # ---- Generate random job ids
    id_len = 10
    for i in range(JOBID_ITERATIONS_MAX):
        # get already assigned job ids
        assigned_ids = [
            d
            for d in os.listdir(os.path.join(current_working_directory, RESULTS_DIR))
            if (
                os.path.isdir(os.path.join(current_working_directory, RESULTS_DIR, d))
                and not d.startswith(".")  # avoid hidden files/directories
            )
        ]
        job_id = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=id_len)
        )
        if job_id not in assigned_ids:  # suitable job id
            break
        if i > 7:
            i = 0  # restart
            id_len += 1  # increase ID length
            if id_len > JOBID_MAXLEN:  # reached maximum length
                break
    if job_name and job_name != "None":
        assert isinstance(job_name, str)
        job_id = f"{job_name}_{job_id}"
    result_dir = os.path.join(current_working_directory, RESULTS_DIR, job_id)
    # create results directory
    cmd = f"mkdir {result_dir}"
    code = subprocess.call(cmd, shell=True)
    if code != 0:
        raise ValueError(f"An error occurred while running {cmd}")
    # NOTE test command for queue
    cmd = f"touch {os.path.join(current_working_directory, RESULTS_DIR, job_id, QUEUE_FILE)}"
    code = subprocess.call(cmd, shell=True)
    if code != 0:
        raise ValueError(f"An error occurred while running {cmd}")
    # ---- Set search parameters
    # ANNOTATION CHECK
    gencode_name = "gencode.protein_coding.bed"
    annotation_name = ".dummy.bed"  # to proceed without annotation file
    if "EN" in annotation_var:
        annotation_name = "encode+gencode.hg38.bed"
        if "MA" in annotation_var:
            annotation_name = "".join(
                [
                    f"{annotation_name}+",
                    "".join(annotation_input.split(".")[:-1]),
                    ".bed",
                ]
            )
            annotation_dir = os.path.join(current_working_directory, ANNOTATIONS_DIR)
            annotation_tmp = os.path.join(annotation_dir, f"ann_tmp_{job_id}.bed")
            cmd = f"cp {os.path.join(annotation_dir, annotation_name)} {annotation_tmp}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
            annotation_input_tmp = (
                f"{os.path.join(annotation_dir, annotation_input)}.tmp"
            )
            cmd = f"awk '$4 = $4\"_personal\"' {os.path.join(annotation_dir, annotation_input)} > {annotation_input_tmp}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
            cmd = f"mv {annotation_input_tmp} {os.path.join(annotation_dir, annotation_input)}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
            cmd = f"tail -n +1 {os.path.join(annotation_dir, annotation_input)} >> {annotation_tmp}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
            cmd = f"mv {annotation_tmp} {os.path.join(annotation_dir, annotation_name)}"
            code = subprocess.call(cmd, shell=True)
            if code != 0:
                raise ValueError(f"An error occurred while running {cmd}")
    elif "MA" in annotation_var:
        annotation_input_tmp = f"{os.path.join(annotation_dir, annotation_input)}.tmp"
        cmd = f"awk '$4 = $4\"_personal\"' {os.path.join(annotation_dir, annotation_input)} > {annotation_input_tmp}"
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            raise ValueError(f"an error occurred while running {cmd}")
        annotation_name = f"{annotation_input}.tmp"
    if "EN" not in annotation_var:
        cmd = f"rm -rf {os.path.join(annotation_dir, '.dummy.bed')}"
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            raise ValueError(f"An error occurred while running {cmd}")
        cmd = f"touch {os.path.join(annotation_dir, '.dummy.bed')}"
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            raise ValueError(f"An error occurred while running {cmd}")
        gencode_name = ".dummy.bed"
    # GENOME TYPE CHECK
    ref_comparison = False
    genome_type = "ref"  # search is 'ref' or 'both'
    if len(ref_var) > 0:
        ref_comparison = True
        genome_type = "both"
    search_index = True
    genome_selected = genome_selected.replace(" ", "_")
    genome_ref = genome_selected
    # NOTE indexed genomes names format:
    # PAM + _ + bMax + _ + genome_selected
    # VCF CHECK
    # TODO: check here
    if genome_type == "ref":
        sample_list = None
    sample_list = []
    try:
        with open(os.path.join(result_dir, ".list_vcfs.txt"), mode="w") as handle_vcf:
            if not ref_var:
                vcf_folder = "_"
                handle_vcf.write(f"{vcf_folder}\n")
            if VARIANTS_DATA[0] in ref_var:  # 1000 genomes
                vcf_folder = "hg38_1000G"
                sample_list.append("hg38_1000G.samplesID.txt")  # 1KGP samples
                handle_vcf.write(f"{vcf_folder}\n")
            if VARIANTS_DATA[1] in ref_var:  # human genome diversity project
                vcf_folder = "hg38_HGDP"
                sample_list.append("hg38_HGDP.samplesID.txt")  # HGDP samples
                handle_vcf.write(f"{vcf_folder}\n")
            if VARIANTS_DATA[2] in ref_var:  # custom data
                vcf_folder = vcf_input
                sample_list.append(f"{vcf_input}.samplesID.txt")  # custom samples
                handle_vcf.write(f"{vcf_folder}\n")
    except OSError as e:
        raise e
    try:
        with open(
            os.path.join(result_dir, ".samplesID.txt"), mode="w"
        ) as handle_samples:
            for e in sample_list:
                handle_samples.write(f"{e}\n")
    except OSError as e:
        raise e
    # manage email sending
    send_email = False
    if adv_opts is None:
        adv_opts = []
    if "email" in adv_opts and check_mail_address(dest_email):
        send_email = True
        try:
            with open(os.path.join(result_dir, EMAIL_FILE), mode="w") as handle_mail:
                handle_mail.write(f"{dest_email}\n")
                handle_mail.write(
                    f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                )
                handle_mail.write(
                    f"{datetime.utcnow().strftime('%m/%d/%Y, %H:%M:%S')}\n"
                )
        except OSError as e:
            raise e
    else:
        dest_email = "_"  # null value
    # manage PAM
    pam_len = 0
    pam_begin = False
    try:
        with open(
            os.path.join(current_working_directory, PAMS_DIR, f"{pam}.txt")
        ) as handle_pam:
            pam_char = handle_pam.readline()
            index_pam_value = pam_char.split()[-1]
            if int(index_pam_value) < 0:
                end_idx = -int(index_pam_value)
                pam_char = pam_char.split()[0][:end_idx]
                pam_begin = True
            else:
                end_idx = int(index_pam_value)
                pam_char = pam_char.split()[0][-end_idx:]
            pam_len = end_idx
    except OSError as e:
        raise e
    # manage guide type
    if guide_type == "GS":
        # text_sequence = text_guides
        # Extract sequence and create the guides
        guides = []
        for seqname_and_seq in text_guides.split(">"):
            if not seqname_and_seq:
                continue
            seqname = seqname_and_seq[:seqname_and_seq.find("\n")]
            seq = seqname_and_seq[seqname_and_seq.find("\n") :]
            seq = seq.strip()  # remove endline
            if "chr" in seq:
                for line in seq.split("\n"):
                    if not line:
                        continue
                    line_split = line.strip().split()
                    seq_read = f"{line_split[0]}:{line_split[1]}-{line_split[2]}"
                    assert bool(seqname)
                    assert bool(seq_read)
                    assert bool(genome_ref)
                    seq_read = extract_seq.extractSequence(
                        seqname, seq_read, genome_ref.replace(" ", "_")
                    )
            else:
                seq_read = "".join(seq.split()).strip()
            guides.append(
                convert_pam.getGuides(seq_read, pam_char, guide_seqlen, pam_begin)
            )
        guides = list(set(guides))  # remove potential duplicate guides
        # create new guides dataset
        if not guides:
            guides = "A" * guide_seqlen
        text_guides = "\n".join(guides).strip()
        assert bool(guides)
    # force guides to be upper case
    text_guides = text_guides.upper()
    text_guides_tmp = [
        guide for guide in text_guides.split("\n") if len(guide) == guide_seqlen
    ]
    if not text_guides_tmp:  # no suitable guide found
        text_guides_tmp.append("A" * guide_seqlen)
    text_guides = "\n".join(text_guides_tmp)
    for guide in text_guides.split("\n"):
        for nt in guide:
            if nt not in VALID_CHARS:
                # remove forbidden characters from guide
                text_guides = text_guides.replace(nt, "")
    # set limit to 100 guides per run in the website
    if len(text_guides.split("\n")) > 100:
        text_guides = "\n".join(text_guides.split("\n")[:100]).strip()
    # Adjust guides by adding Ns (compatible with Crispritz)
    if pam_begin:
        pam_to_file = pam_char + ("N" * guide_seqlen) + " " + index_pam_value
        pam_to_indexing = pam_char + ("N" * 25) + " " + index_pam_value
    else:
        pam_to_file = ("N" * guide_seqlen) + pam_char + " " + index_pam_value
        pam_to_indexing = ("N" * 25) + pam_char + " " + index_pam_value
    # store PAMs file
    try:
        with open(os.path.join(result_dir, PAMS_FILE), mode="w") as handle_pam:
            handle_pam.write(pam_to_file)
    except OSError as e:
        raise e
    pams_file = os.path.join(result_dir, PAMS_FILE)
    guides_file = os.path.join(result_dir, GUIDES_FILE)
    if text_guides:
        try:
            with open(guides_file, mode="w") as handle_guides:
                if pam_begin:
                    text_guides = "N" * pam_len + text_guides.replace(
                        "\n", "\n" + "N" * pam_len
                    )
                else:
                    text_guides = (
                        text_guides.replace("\n", "N" * pam_len + "\n") + "N" * pam_len
                    )
                handle_guides.write(text_guides)
        except OSError as e:
            raise e
    # bulges
    dna = int(dna)
    rna = int(rna)
    max_bulges = rna
    assert isinstance(dna, int)
    assert isinstance(rna, int)
    if dna > rna:
        max_bulges = dna
    # base editing 
    if be_start is None or not bool(be_start):
        be_start = 1
    else:
        be_start = int(be_start)
    if be_stop is None or not bool(be_stop):
        be_stop = 0
    else:
        be_stop = int(be_stop)
    if be_nt is None or not bool(be_nt):
        be_nt = "_"
    else:
        assert be_nt in DNA_ALPHABET
    assert isinstance(be_start, int)
    assert isinstance(be_stop, int)
    assert isinstance(be_nt, str)
    if search_index:
        search = False
    # Check if index exists, otherwise set generate_index to true
    genome_idx_list = []
    if genome_type == "ref":
        genome_idx = f"{pam_char}_{max_bulges}_{genome_selected}"
        genome_idx_list.append(genome_idx)
    else:
        if VARIANTS_DATA[0] in ref_var:
            genome_idx = f"{pam_char}_{max_bulges}_{genome_selected}+hg38_1000G"
            genome_idx_list.append(genome_idx)
        if VARIANTS_DATA[1] in ref_var:
            genome_idx = f"{pam_char}_{max_bulges}_{genome_selected}+hg38_HGDP"
            genome_idx_list.append(genome_idx)
        if VARIANTS_DATA[2] in ref_var:
            genome_idx = f"{pam_char}_{max_bulges}_{genome_selected}+{vcf_input}"
            genome_idx_list.append(genome_idx)
    genome_idx = ",".join(genome_idx_list)
    # Create .Params.txt file
    try:
        with open(os.path.join(result_dir, PARAMS_FILE), mode="w") as handle_params:
            handle_params.write(f"Genome_selected\t{genome_selected}\n")
            handle_params.write(f"Genome_ref\t{genome_ref}\n")
            if search_index:
                handle_params.write(f"Genome_idx\t{genome_idx}\n")
            else:
                handle_params.write(f"Genome_idx\tNone\n")
            handle_params.write(f"Pam\t{pam_char}\n")
            handle_params.write(f"Max_bulges\t{max_bulges}\n")
            handle_params.write(f"Mismatches\t{mms}\n")
            handle_params.write(f"DNA\t{dna}\n")
            handle_params.write(f"RNA\t{rna}\n")
            handle_params.write(f"Annotation\t{annotation_name}\n")
            handle_params.write(f"Nuclease\t{nuclease}\n")
            handle_params.write(f"Ref_comp\t{ref_comparison}\n")
    except OSError as e:
        raise e
    # ---- Check if input parameters (mms, bulges, pam, guides, genome) match
    # those of previous searches
    computed_results_dirs = [
        d
        for d in os.listdir(os.path.join(current_working_directory, RESULTS_DIR))
        if (
            os.path.isdir(os.path.join(current_working_directory, RESULTS_DIR, d))
            and not d.startswith(".")  # ignore hidden directories
        )
    ]
    computed_results_dirs.remove(job_id)  # remove current job results
    for res_dir in computed_results_dirs:
        if os.path.exists(
            os.path.join(current_working_directory, RESULTS_DIR, res_dir, PARAMS_FILE)
        ):
            if filecmp.cmp(
                os.path.join(
                    current_working_directory, RESULTS_DIR, res_dir, PARAMS_FILE
                ),
                os.path.join(result_dir, PARAMS_FILE),
            ):
                try:
                    # old job guides
                    guides_old = open(
                        os.path.join(
                            current_working_directory,
                            RESULTS_DIR,
                            res_dir,
                            GUIDES_FILE,
                        )
                    ).read().split("\n")
                    # current job guides
                    guides_current = open(
                        os.path.join(
                            current_working_directory,
                            RESULTS_DIR,
                            job_id,
                            GUIDES_FILE,
                        )
                    ).read().split("\n")
                except OSError as e:
                    raise e
                if (
                    collections.Counter(guides_old) == collections.Counter(
                        guides_current
                    )
                ):
                    if os.path.exists(
                        os.path.join(
                            current_working_directory, RESULTS_DIR, res_dir, LOG_FILE
                        )
                    ):  # log file found
                        adj_date = False
                        try:
                            with open(
                                os.path.join(
                                    current_working_directory,
                                    RESULTS_DIR,
                                    res_dir,
                                    LOG_FILE,
                                )
                            ) as handle_log:
                                log_data = handle_log.read().strip()
                                if "Job\tDone" in log_data:
                                    adj_date = True
                                    log_data = log_data.split("\n")
                                    date_new = subprocess.Popen(
                                        ["echo $(date)"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True,
                                    )
                                    out, err = date_new.communicate()
                                    log_to_write = "\n".join(log_data[:-1])
                                    date_write = str(
                                        f"{log_to_write}\nJob\nDone\t"
                                        f"{out.decode('UTF-8').strip()}"
                                    )
                        except OSError as e:
                            raise e
                        if adj_date:
                            try:
                                with open(
                                    os.path.join(
                                        current_working_directory,
                                        RESULTS_DIR,
                                        res_dir,
                                        LOG_FILE,
                                    ),
                                    mode="w+",
                                ) as handle_log:
                                    assert date_write
                                    handle_log.write(date_write)
                            except OSError as e:
                                raise e
                            if send_email:
                                # Send mail with file in job_id dir with link to
                                # job already done, note that job_id directory
                                # will be deleted
                                try:
                                    with open(
                                        os.path.join(
                                            current_working_directory,
                                            RESULTS_DIR,
                                            res_dir,
                                            EMAIL_FILE,
                                        ),
                                        mode="w+",
                                    ) as handle_email:
                                        handle_email.write(f"{dest_email}\n")
                                        handle_email.write(
                                            f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                                        )
                                        handle_email.write(
                                            "".join(
                                                [
                                                    datetime.utcnow().strftime(
                                                        "%m/%d/%Y, %H:%M:%S"
                                                    ),
                                                    "\n",
                                                ]
                                            )
                                        )
                                except OSError as e:
                                    raise e
                        elif send_email:
                            # Job is not finished yet. Add current user's email
                            # to email.txt
                            if os.path.exists(
                                os.path.join(
                                    current_working_directory,
                                    RESULTS_DIR,
                                    res_dir,
                                    EMAIL_FILE,
                                )
                            ):
                                try:
                                    with open(
                                        os.path.join(
                                            current_working_directory,
                                            RESULTS_DIR,
                                            res_dir,
                                            EMAIL_FILE,
                                        ),
                                        mode="a+",
                                    ) as handle_email:
                                        handle_email.write("--OTHEREMAIL--")
                                        handle_email.write(f"{dest_email}\n")
                                        handle_email.write(
                                            f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                                        )
                                        handle_email.write(
                                            "".join(
                                                [
                                                    datetime.utcnow().strftime(
                                                        "%m/%d/%Y, %H:%M:%S"
                                                    ),
                                                    "\n",
                                                ]
                                            )
                                        )
                                except OSError as e:
                                    raise e
                            else:
                                try:
                                    with open(
                                        os.path.join(
                                            current_working_directory,
                                            RESULTS_DIR,
                                            res_dir,
                                            EMAIL_FILE,
                                        ),
                                        mode="w+",
                                    ) as handle_email:
                                        handle_email.write(f"{dest_email}\n")
                                        handle_email.write(
                                            f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                                        )
                                        handle_email.write(
                                            "".join(
                                                [
                                                    datetime.utcnow().strftime(
                                                        "%m/%d/%Y, %H:%M:%S"
                                                    ),
                                                    "\n",
                                                ]
                                            )
                                        )
                                except OSError as e:
                                    raise e
                        current_job_dir = os.path.join(
                            current_working_directory, RESULTS_DIR, job_id
                        )
                        cmd = f"rm -r {current_job_dir}"
                        code = subprocess.call(cmd, shell=True)
                        if code != 0:
                            raise ValueError(f"An error occurred while running {cmd}")
                        return "/load", f"?job={res_dir}"
                    else: 
                        # log file not found 
                        # we may have entered a job directory that was in queue
                        if os.path.exists(
                            os.path.join(
                                current_working_directory, 
                                RESULTS_DIR, 
                                res_dir, 
                                QUEUE_FILE
                            )
                        ):
                            if send_email:
                                if os.path.exists(
                                    os.path.join(
                                        current_working_directory,
                                        RESULTS_DIR,
                                        res_dir,
                                        EMAIL_FILE,
                                    )
                                ):
                                    try:
                                        with open(
                                            os.path.join(
                                                current_working_directory,
                                                RESULTS_DIR,
                                                res_dir,
                                                EMAIL_FILE,
                                            ),
                                            mode="a+",
                                        ) as handle_email:
                                            handle_email.write("--OTHEREMAIL--")
                                            handle_email.write(f"{dest_email}\n")
                                            handle_email.write(
                                                f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                                            )
                                            handle_email.write(
                                                "".join(
                                                    [
                                                        datetime.utcnow().strftime(
                                                            "%m/%d/%Y, %H:%M:%S"
                                                        ),
                                                        "\n",
                                                    ]
                                                )
                                            )
                                    except OSError as e:
                                        raise e
                                else:
                                    try:
                                        with open(
                                            os.path.join(
                                                current_working_directory,
                                                RESULTS_DIR,
                                                res_dir,
                                                EMAIL_FILE,
                                            ),
                                            mode="w+",
                                        ) as handle_email:
                                            handle_email.write(f"{dest_email}\n")
                                            handle_email.write(
                                                f"{''.join(href.split('/')[:-1])}/load?job={job_id}\n"
                                            )
                                            handle_email.write(
                                                "".join(
                                                    [
                                                        datetime.utcnow().strftime(
                                                            "%m/%d/%Y, %H:%M:%S"
                                                        ),
                                                        "\n",
                                                    ]
                                                )
                                            )
                                    except OSError as e:
                                        raise e
                            return ("/load", f"?job={res_dir}")
    # merge default is 3 nt wide
    merge_default = 3
    print(
        str(
            f"Submitted JOB {job_id}. STDOUT > log_verbose.txt; STDERR > "
            "log_error.txt"
        )
    )
    # TODO: use functions rather than calling scripts
    run_job_sh = os.path.join(
        app_main_directory, POSTPROCESS_DIR, "submit_job_automated_new_multiple_vcfs.sh"
    )
    genome = os.path.join(current_working_directory, GENOMES_DIR, genome_ref)
    vcfs = os.path.join(result_dir, ".list_vcfs.txt")
    annotation = os.path.join(
        current_working_directory, ANNOTATIONS_DIR, annotation_name
    )
    pam_file = os.path.join(
        app_main_directory, PAMS_DIR, f"{pam}.txt"
    )
    samples_ids = os.path.join(result_dir, SAMPLES_FILE_LIST)
    postprocess = os.path.join(app_main_directory, POSTPROCESS_DIR)
    gencode = os.path.join(current_working_directory, ANNOTATIONS_DIR, gencode_name)
    log_verbose = os.path.join(result_dir, "log_verbose.txt")
    log_error = os.path.join(result_dir, "log_error.txt")
    assert isinstance(dna, int)
    assert isinstance(rna, int)
    cmd = f"{run_job_sh} {genome} {vcfs} {guides_file} {pam_file} {annotation} {samples_ids} {max(dna, rna)} {mms} {dna} {rna} {merge_default} {result_dir} {postprocess} {8} {current_working_directory} {gencode} {dest_email} {be_start} {be_stop} {be_nt} 1> {log_verbose} 2>{log_error}"
    # run job
    exeggutor.submit(subprocess.run, cmd, shell=True)
    return ("/load", f"?job={job_id}")


# Check input presence
@app.callback(
    [
        Output("submit-job", "n_clicks"),
        Output("modal", "is_open"),
        Output("available-genome", "className"),
        Output("available-pam", "className"),
        Output("text-guides", "style"),
        Output("mms", "className"),
        Output("dna", "className"),
        Output("rna", "className"),
        Output("len-guide-sequence-ver", "className"),
        Output("warning-list", "children"),
    ],
    [Input("check-job", "n_clicks"), Input("close", "n_clicks")],
    [
        State("available-genome", "value"),
        State("available-pam", "value"),
        State("radio-guide", "value"),
        State("text-guides", "value"),
        State("mms", "value"),
        State("dna", "value"),
        State("rna", "value"),
        State("modal", "is_open"),
    ],
)
# len_guide_seq, active_tab ,
def check_input(
    n: int,
    n_close: int,
    genome_selected: str,
    pam: str,
    guide_type: str,
    text_guides: List[str],
    mms: int,
    dna: int,
    rna: int,
    is_open: bool,
) -> Tuple:
    """Check the correctness of input data and fields. If the input data are
    missing or wrong the borders of the corresponding box are colored in red.
    If input are missing, a Modal element is displayed listing the missing
    elements. The callback is triggered when clicking on the "Submit" button or
    when the Modal object is closed ("Close" button or clicking on-screen when
    the Modal object is open).

    ...

    Parameters
    ----------
    n : int
        Clicks
    n_close : int
        Clicks
    genome_selected : str
        Selected genome
    pam : str
        PAM
    guide_type : str
        Guide type
    text_guides : List[str]
        List of selected guides
    mms : str
        Number of mismatches
    dna : str
        Number of DNA bulges
    rna : str
        Number of RNA bulges
    is_open : bool
        True if Modal object is open

    Returns
    -------
    Tuple
        Input data used during CRISPRme analysis
    """

    if n is not None:
        if not isinstance(n, int):
            raise TypeError(f"Expected {int.__name__}, got {type(n).__name__}")
    if is_open is not None:
        if not isinstance(is_open, bool):
            raise TypeError(f"Expected {bool.__name__}, got {type(is_open).__name__}")
    print("Check input for JOB")
    if n is None:
        raise PreventUpdate  # do not check data --> no trigger
    if is_open is None:
        is_open = False
    classname_red = "missing-input"
    genome_update = None
    pam_update = None
    text_update = {"width": "300px", "height": "30px"}
    mms_update = None
    dna_update = None
    rna_update = None
    be_start_update = None
    be_stop_update = None
    len_guide_update = None
    update_style = False
    miss_input_list = []  # recover missing inputs
    # display missing genome
    if genome_selected is None or not bool(genome_selected):
        genome_update = classname_red
        update_style = True
        miss_input_list.append("Genome")
    if genome_selected is None or not bool(genome_selected):
        genome_selected = "hg38_ref"
    genome_ref = genome_selected
    if pam is None or not bool(pam):
        pam_update = classname_red
        update_style = True
        miss_input_list.append("PAM")
    if mms is None:
        mms_update = classname_red
        update_style = True
        miss_input_list.append("Allowed Mismatches")
    if dna is None:
        dna_update = classname_red
        update_style = True
        miss_input_list.append("Bulge DNA size")
    if rna is None:
        rna_update = classname_red
        update_style = True
        miss_input_list.append("Bulge RNA size")
    if pam is None or not bool(pam):
        pam = "20bp-NGG-SpCas9"
        len_guide_sequence = 20
    else:
        for e in pam.split("-"):
            if "bp" in e:
                len_guide_sequence = int(e.replace("bp", ""))
    no_guides = False
    if text_guides is None or not bool(text_guides):
        text_guides = "A" * len_guide_sequence
        no_guides = True
    elif guide_type != "GS":
        text_guides = text_guides.strip()
        if not all(
            [len(g) == len(text_guides.split("\n")[0]) for g in text_guides.split("\n")]
        ):
            text_guides = select_same_len_guides(text_guides)
    # check PAM
    try:
        with open(
            os.path.join(current_working_directory, PAMS_DIR, f"{pam}.txt")
        ) as handle_pam:
            pam_char = handle_pam.readline()
            index_pam_value = int(pam_char.split()[-1])
            if index_pam_value < 0:
                end_idx = index_pam_value * (-1)
                pam_char = pam_char.split()[0][:end_idx]
                pam_begin = True
            else:
                end_idx = index_pam_value
                pam_char = pam_char.split()[0][(end_idx * (-1)) :]
                pam_begin = False
    except OSError as e:
        raise e
    if guide_type == "GS":
        # Extract sequence and create the guides
        guides = []
        for seqname_and_seq in text_guides.split(">"):
            if not seqname_and_seq:
                continue
            seqname = seqname_and_seq[: seqname_and_seq.find("\n")]
            seq = seqname_and_seq[seqname_and_seq.find("\n") :]
            seq = seq.strip()
            if "chr" in seq:
                for line in seq.split("\n"):
                    if not line.strip():
                        continue
                    line_split = line.strip().split()
                    seq_read = f"{line_split[0]}:{line_split[1]}-{line_split[2]}"
                    assert bool(seqname)
                    assert bool(seq_read)
                    assert bool(genome_ref)
                    seq_read = extract_seq.extractSequence(
                        seqname, seq_read, genome_ref.replace(" ", "_")
                    )
                    guides.extend(
                        convert_pam.getGuides(
                            seq_read, pam_char, len_guide_sequence, pam_begin
                        )
                    )
            else:
                seq_read = "".join(seq.split()).strip()
                guides.extend(
                    convert_pam.getGuides(
                        seq_read, pam_char, len_guide_sequence, pam_begin
                    )
                )
        guides = list(set(guides))  # remove potential duplicates
        if not guides:
            guides = "A" * len_guide_sequence
            no_guides = True
        text_guides = "\n".join(guides).strip()
    text_guides = text_guides.upper()
    text_guides_tmp = [
        guide.replace("N", "")
        for guide in text_guides.split("\n")
        if len(guide.replace("N", "")) == len_guide_sequence
    ]
    if not text_guides_tmp:  # no guide found
        text_guides_tmp.append("A" * len_guide_sequence)
        no_guides = True
    text_guides = "\n".join(text_guides_tmp)
    # remove forbidden characters from guides
    for guide in text_guides.split("\n"):
        for nt in guide:
            if nt not in VALID_CHARS:
                text_guides = text_guides.replace(nt, "")
    # set limit to 1000000000 guides per run
    if len(text_guides.split("\n")) > 1000000000:
        text_guides = "\n".join(text_guides.split("\n")[:1000000000]).strip()
    if no_guides:
        text_update = {"width": "300px", "height": "30px", "border": "1px solid red"}
        update_style = True
        miss_input_list.append(
            str(
                "Input at least one correct guide, correct guides must have the "
                "length requested for the selected PAM sequence (e.g., 20bp, "
                "21bp, etc)"
            )
        )
    miss_input = html.Div(
        [
            html.P("The following inputs are missing:"),
            html.Ul([html.Li(x) for x in miss_input_list]),
            html.P("Please fill in the values before submitting the job"),
        ]
    )
    if not update_style:
        print("All input read correctly")
        return (
            1,
            False,
            genome_update,
            pam_update,
            text_update,
            mms_update,
            dna_update,
            rna_update,
            len_guide_update,
            miss_input,
        )
    return (
        None,
        (not is_open),
        genome_update,
        pam_update,
        text_update,
        mms_update,
        dna_update,
        rna_update,
        len_guide_update,
        miss_input,
    )


@app.callback(
    Output("fade-len-guide", "is_in"),
    [Input("tabs", "active_tab")],
    [State("fade-len-guide", "is_in")],
)
def reset_tab(current_tab: str, is_in: bool) -> bool:
    """Manages the fading of the dropdown bar for the guide length, when the tab
    'Sequence' is active.

    ...

    Parameters
    ----------
    current_tab : str
        Current active tab
    is_in : bool
        True if dropdown's guide length is displayed

    Returns
    -------
    bool
    """

    if current_tab is not None:
        if not isinstance(current_tab, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(current_tab).__name__}"
            )
    if current_tab is None:
        raise PreventUpdate  # do not do anything
    if current_tab == "guide-tab":
        return False
    return True


# Check if email address is valid
@app.callback(Output("example-email", "style"), [Input("example-email", "value")])
def is_email_valid(email: str) -> Dict[str, str]:
    """Check if the provided mail address is valid.
    Change the mail box borders to green or red, accordingly.

    ...

    Parameters
    ----------
    email: str
        Email address

    Returns
    -------
    Dict[str, str]
        Email box borders color
    """
    if email is not None:
        if not isinstance(email, str):
            raise TypeError(f"Expected {str.__name__}, got {type(email).__name__}")
    if email is None:
        raise PreventUpdate  # do not do anything
    if ("@" in email) and (len(email.split("@")) == 2):
        # mail address should be valid
        return {"border": "1px solid #94f033", "outline": "0"}
    return {"border": "1px solid red"}


# Fade in/out email
@app.callback(Output("example-email", "disabled"), [Input("checklist-mail", "value")])
def disabled_mail(checklist_value: List) -> bool:
    """Disable email if not in the checklist.

    ...

    Parameters
    ----------
    checklist_value : List

    Returns
    -------
    bool
    """

    if not isinstance(checklist_value, list):
        raise TypeError(
            f"Expected {list.__name__}, got {type(checklist_value).__name__}"
        )
    if "email" not in checklist_value:
        return True
    return False


# disable job ID
@app.callback(Output("job-name", "disabled"), [Input("checklist-job-name", "value")])
def disable_job_name(checklist_value: List) -> bool:
    """Disable job name if not in the checklist.

    ...

    Parameters
    ----------
    checklist_value : List

    Returns
    -------
    bool
    """

    if not isinstance(checklist_value, list):
        raise TypeError(
            f"Expected {list.__name__}, got {type(checklist_value).__name__}"
        )
    if "job_name" not in checklist_value:
        return True
    return False


@app.callback(
    [Output("vcf-dropdown", "disabled"), Output("vcf-dropdown", "value")],
    [Input("checklist-variants", "value")],
)
def change_disabled_vcf_dropdown(checklist_value: List) -> Tuple[bool, str]:
    """Disable VCF dropdown if not in the checklist.

    ...

    Parameters
    ----------
    checklist_value : List

    Returns
    -------
    Tuple[bool, str]
    """

    if not isinstance(checklist_value, list):
        raise TypeError(
            f"Expected {list.__name__}, got {type(checklist_value).__name__}"
        )
    if "PV" in checklist_value:
        return False, ""
    return True, ""


@app.callback(
    [Output("annotation-dropdown", "disabled"), Output("annotation-dropdown", "value")],
    [Input("checklist-annotations", "value")],
)
def change_disabled_annotation_dropdown(checklist_value: List) -> Tuple[bool, str]:
    """Disable annotation dropdown if not in the checklist.

    ...

    Parameters
    ----------
    checklist_value : List

    Returns
    -------
    Tuple[bool, str]
    """

    if not isinstance(checklist_value, list):
        raise TypeError(
            f"Expected {list.__name__}, got {type(checklist_value).__name__}"
        )
    if "MA" in checklist_value:
        return False, ""
    return True, ""


# select Cas protein from dropdown
@app.callback([Output("available-pam", "options")], [Input("available-cas", "value")])
def select_cas_pam_dropdown(casprot: str) -> List:
    """Select the available Cas proteins and their corresponding PAMs.

    ...

    Parameters
    ----------
    casprot : str
        Cas protein

    Returns
    -------
    List
    """

    if not isinstance(casprot, str):
        raise TypeError(f"Expected {str.__name__}, got {type(casprot).__name__}")
    available_pams = get_available_PAM()
    options = [
        {"label": pam["label"], "value": pam["value"]}
        for pam in available_pams
        if casprot == pam["label"].split(".")[0].split("-")[2]
    ]
    return [options]


# add place holder to guide box
@app.callback([Output("text-guides", "placeholder")], [Input("radio-guide", "value")])
def change_placeholder_guide_textbox(guide_type: str) -> List:
    """Add place holders to guides text box.

    ...

    Parameters
    ----------
    guide_type : str
        Guide type

    Returns
    -------
    List
    """

    if not isinstance(guide_type, str):
        raise TypeError(f"Expected {str.__name__}, got {type(guide_type).__name__}")
    place_holder_text = ""
    if guide_type == "IP":  # individual spacers
        place_holder_text = str("GAGTCCGAGCAGAAGAAGAA\n" "CCATCGGTGGCCGTTTGCCC")
    elif guide_type == "GS":  # genomic sequences
        place_holder_text = str(
            ">sequence1\n"
            "AAGTCCCAGGACTTCAGAAGagctgtgagaccttggc\n"
            ">sequence_bed\n"
            "chr1 11130540 11130751\n"
            "chr1 1023000 1024000"
        )
    else:
        raise ValueError(f"Forbidden guide type ({guide_type})")
    assert bool(place_holder_text)
    return [place_holder_text]


# change variants options
@app.callback(
    [Output("checklist-variants", "options"), Output("vcf-dropdown", "options")],
    [Input("available-genome", "value")],
)
def change_variants_checklist_state(genome_value: str) -> List:
    """Change available variants options, according to the selected genome.

    ...

    Parameters
    ----------
    genome_value : str
        Genome

    Returns
    -------
    List
    """

    if genome_value is not None:
        if not isinstance(genome_value, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(genome_value).__name__}"
            )
        checklist_variants_options = [
            {
                "label": " plus 1000 Genome Project variants",
                "value": "1000G",
                "disabled": False,
            },
            {"label": " plus HGDP variants", "value": "HGDP", "disabled": False},
            {"label": " plus personal variants*", "value": "PV", "disabled": True},
        ]
    personal_vcf = get_custom_VCF(genome_value)
    return [checklist_variants_options, personal_vcf]


def index_page() -> html.Div:
    """Construct the layout of CRISPRme main page.
    When a new genome is added to /Genomes directory, reload genomes and PAMs
    dropdowns (via page reloading).

    ...

    Parameters
    ----------
    None

    Returns
    -------
    html.Div
    """

    # begin main page construction
    final_list = []
    # page intro
    introduction_content = html.Div(
        [
            html.Div(
                str(
                    "CRISPRme is a web application, also available offline or "
                    "command line, for comprehensive off-target assessment. It "
                    "integrates human genetic variant datasets with orthogonal "
                    "genomic annotations to predict and prioritize CRISPR-Cas "
                    "off-target sites at scale. The method considers both "
                    "single-nucleotide variants (SNVs) and indels, accounts for "
                    "bona fide haplotypes, accepts spacer:protospacer mismatches "
                    "and bulges, and is suitable for population and personal "
                    "genome analyses."
                )
            ),
            html.Div(
                [
                    "Check out our preprint on bioRxiv ",
                    html.A("here!", target="_blank", href=PREPRINT_LINK),
                ]
            ),
            html.Div(
                [
                    "CRISPRme offline version can be downloaded from ",
                    html.A("Github", target="_blank", href=GITHUB_LINK),
                ]
            ),
            html.Br(),  # add newline
        ]
    )
    # warnings
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader("WARNING! Missing inputs"),
                    dbc.ModalBody(
                        str(
                            "The following inputs are missing, please select "
                            "values before submitting the job"
                        ),
                        id="warning-list",
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="modal-button")
                    ),
                ],
                id="modal",
                centered=True,
            ),
        ]
    )
    # guides table
    tab_guides_content = html.Div(
        [
            html.H4("Select gRNA"),
            dcc.RadioItems(
                id="radio-guide",
                options=[
                    {"label": " Input individual spacer(s)", "value": "IP"},
                    {"label": " Input genomic sequence(s)", "value": "GS"},
                ],
                value="IP",
            ),
            dcc.Textarea(
                id="text-guides",
                placeholder=str("GAGTCCGAGCAGAAGAAGAA\n" "CCATCGGTGGCCGTTTGCCC"),
                style={"width": "300px", "height": "30px"},
            ),
            dbc.FormText(
                str(
                    "Spacer must be provided as a DNA sequence without a PAM. "
                    "A maximum of 100 spacer sequences can be provided . If "
                    "using the sequence extraction feature, only the first 100 "
                    "spacer sequences (starting from the top strand) will be "
                    "extracted.*"
                ),
                color="secondary",
            ),
        ],
        style={"width": "300px"},  # NOTE same as text-area
    )
    # cas protein dropdown
    cas_protein_content = html.Div(
        [
            html.H4("Select Cas protein"),
            html.Div(
                dcc.Dropdown(
                    options=get_available_CAS(),
                    clearable=False,
                    id="available-cas",
                    style={"width": "300px"},
                )
            ),
        ]
    )
    # PAM dropdown
    pam_content = html.Div(
        [
            html.H4("Select PAM"),
            html.Div(
                dcc.Dropdown(
                    options=[],
                    clearable=False,
                    id="available-pam",
                    style={"width": "300px"},
                )
            ),
        ],
    )
    personal_data_management_content = html.Div(
        [
            html.Br(),
            html.A(
                html.Button(
                    "Personal Data Management",
                    id="add-genome",
                    style={"display": DISPLAY_OFFLINE},
                ),
                href=os.path.join(URL, "genome-dictionary-management"),
                target="",
                style={"text-decoration": "none", "color": "#555"},
            ),
        ]
    )
    # genome dropdown
    genome_content = html.Div(
        [
            html.H4("Select genome"),
            html.Div(
                dcc.Dropdown(
                    options=get_available_genomes(),
                    clearable=False,
                    id="available-genome",
                ),
                style={"width": "300px"},
            ),
            html.Div(
                dcc.Checklist(
                    options=[
                        {
                            "label": " plus 1000 Genome Project variants",
                            "value": "1000G",
                            "disabled": True,
                        },
                        {
                            "label": " plus HGDP variants",
                            "value": "HGDP",
                            "disabled": True,
                        },
                        {
                            "label": " plus personal variants*",
                            "value": "PV",
                            "disabled": True,
                        },
                    ],
                    id="checklist-variants",
                    value=[],
                )
            ),
            html.Div(
                dcc.Dropdown(
                    options=[],
                    id="vcf-dropdown",
                    style={"width": "300px"},
                    disabled=True,
                ),
                id="div-browse-PV",
            ),
        ]
    )
    # thresholds boxes
    thresholds_content = html.Div(
        [
            html.H4("Select thresholds"),
            html.Div(  # mismatches box
                [
                    html.P("Mismatches"),
                    dcc.Dropdown(
                        options=AV_MISMATCHES,
                        clearable=False,
                        id="mms",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block", "margin-right": "20px"},
            ),
            html.Div(  # DNA bulges box
                [
                    html.P(["DNA", html.Br(), "Bulges"]),
                    dcc.Dropdown(
                        options=AV_BULGES,
                        clearable=False,
                        id="dna",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block", "margin-right": "20px"},
            ),
            html.Div(  # RNA bulges box
                [
                    html.P(["RNA", html.Br(), "Bulges"]),
                    dcc.Dropdown(
                        options=AV_BULGES,
                        clearable=False,
                        id="rna",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block"},
            ),
        ],
        style={"margin-top": "10%"},
    )
    # base editing boxes
    base_editing_content = html.Div(
        [
            html.H4("Base Editing"),
            html.Div(  # BE window start dropdown
                [
                    html.P("Window start"),
                    dcc.Dropdown(
                        clearable=False,
                        id="be-window-start",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block", "margin-right": "20px"},
            ),
            html.Div(  # BE window stop dropdown
                [
                    html.P("Window stop"),
                    dcc.Dropdown(
                        clearable=False,
                        id="be-window-stop",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block", "margin-right": "20px"},
            ),
            html.Div(  # BE nucleotides dropdown
                [
                    html.P(["Nucleotide"]),
                    dcc.Dropdown(
                        options=BE_NTS,
                        clearable=False,
                        id="be-nts",
                        style={"width": "60px"},
                    ),
                ],
                style={"display": "inline-block", "margin-right": "20px"},
            ),
        ],
        style={"margin-top": "10%"},
    )
    # annotations dropdown
    annotation_content = html.Div(
        [
            html.H4("Select annotation"),
            html.Div(
                dcc.Checklist(
                    options=[
                        {"label": " ENCODE cCREs + GENCODE gene", "value": "EN"},
                        {
                            "label": " Personal annotations*",
                            "value": "MA",
                            "disabled": True,
                        },
                    ],
                    id="checklist-annotations",
                    value=["EN"],
                )
            ),
            html.Div(
                dcc.Dropdown(
                    options=[i for i in get_custom_annotations()],
                    id="annotation-dropdown",
                    style={"width": "300px"},
                    disabled=True,
                ),
                id="div-browse-annotation",
            ),
        ]
    )
    # mail box
    mail_content = html.Div(
        [
            dcc.Checklist(
                options=[
                    {
                        "label": " Notify me by email",
                        "value": "email",
                        "disabled": False,
                    }
                ],
                id="checklist-mail",
                value=[],
            ),
            dbc.FormGroup(
                dbc.Input(
                    type="email",
                    id="example-email",
                    placeholder="name@mail.com",
                    className="exampleEmail",
                    disabled=True,
                    style={"width": "300px"},
                )
            ),
        ]
    )
    # job name box
    job_name_content = html.Div(
        [
            dcc.Checklist(
                options=[
                    {"label": " Job name", "value": "job_name", "disabled": False}
                ],
                id="checklist-job-name",
                value=[],
            ),
            dbc.FormGroup(
                dbc.Input(
                    type="text",
                    id="job-name",
                    placeholder="my_job",
                    className="jobName",
                    disabled=True,
                    style={"width": "300px"},
                )
            ),
        ]
    )
    # submit button
    submit_content = html.Div(
        [
            html.Button(
                "Submit",
                id="check-job",
                style={"background-color": "#E6E6E6", "width": "260px"},
            ),
            html.Button("", id="submit-job", style={"display": "none"}),
        ]
    )
    # load example button
    example_content = html.Div(
        [
            html.Button(
                "Load Example",
                id="load-example-button",
                style={"background-color": "#E6E6E6", "width": "260px"},
            ),
        ]
    )
    # terms and conditions link
    terms_and_conditions_content = html.Div(
        [
            html.Div("By clicking submit you are agreeing to the"),
            html.Div(
                html.A(
                    "Terms and Conditions.",
                    target="_blank",
                    href=f"{GITHUB_LINK}/blob/main/LICENSE",
                )
            ),
        ]
    )
    # insert introduction in the page layout
    final_list.append(introduction_content)
    # add other content
    final_list.append(
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(  # first column of the box
                            [
                                modal,
                                dbc.Row(dbc.Col(tab_guides_content)),
                                dbc.Row(dbc.Col(cas_protein_content)),
                                dbc.Row(dbc.Col(pam_content)),
                            ],
                            width="auto",
                        ),
                        dbc.Col(  # second column of the box
                            [
                                dbc.Row(dbc.Col(genome_content)),
                                dbc.Row(dbc.Col(thresholds_content)),
                                dbc.Row(dbc.Col(base_editing_content)),
                                html.Br(),
                                dbc.Row(dbc.Col(example_content)),
                            ],
                            width="auto",
                        ),
                        dbc.Col(  # third column of the box
                            [
                                dbc.Row(annotation_content),
                                dbc.Row(mail_content),
                                dbc.Row(job_name_content),
                                html.Br(),
                                dbc.Row(dbc.Col(submit_content)),
                                dbc.Row(terms_and_conditions_content),
                            ],
                            width="auto",
                        ),
                    ],
                    justify="center",
                    style={"margin-bottom": "1%"},
                )
            ],
            style={
                "background-color": "rgba(157, 195, 230, 0.39)",
                "border-radius": "5px",
                "border": "1px solid black",
            },
            id="steps-background",
        )
    )
    final_list.append(html.Br())
    final_list.append(
        html.P(
            str(
                "*The offline version of CRISPRme can be downloaded from GitHub "
                "and offers additional functionalities, including the option to "
                "input personal data (such as genetic variants, annotations, "
                "and/or empirical off-target results) as well as custom PAMs and "
                "genomes. There is no limit on the number of spacers, mismatches, "
                "and/or bulges used in the offline search."
            )
        )
    )
    index_page = html.Div(final_list, style={"margin": "1%"})
    return index_page


@app.callback(
    [Output("be-window-start", "options"), Output("be-window-stop", "options")],
    [Input("text-guides", "value")],
    [State("radio-guide", "value"), State("available-genome", "value")],
)
def update_base_editing_dropdown(
    text_guides: str, guide_type: str, genome: str
) -> Tuple:
    """Update base editing dropdown dinamically. The start and stop values for 
    base editing are changed accordingly to the guides provided in input by
    the user.
    
    ...
    
    Parameters
    ----------
    text_guides : str
        Guides
    guide_type : str
        Guide type
    genome : str
        Reference genome
        
    Returns
    -------
    Tuple
    """

    if text_guides is not None:
        if not isinstance(text_guides, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(text_guides).__name__}"
            )
    if not isinstance(guide_type, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(guide_type).__name__}"
        )
    dropdown_options = [{"label": "", "value": ""}]
    if text_guides is None:
        return dropdown_options, dropdown_options
    if guide_type == "IP":  # individual spacers
        guides = text_guides.strip()
    elif guide_type == "GS":  # genomic sequences
        guides = []
        for seqname_and_seq in text_guides.split(">"):
            if not seqname_and_seq: 
                continue
            seqname = seqname_and_seq[:seqname_and_seq.find("\n")]
            seq = seqname_and_seq[seqname_and_seq.find("\n"):].strip()
            if "chr" in seq:  # BED regions
                for line in seq.split("\n"):
                    if not line:
                        continue
                    line_split = line.strip().split()
                    seq_read = f"{line_split[0]}:{line_split[1]}-{line_split[2]}"
                    seq_read = extract_seq.extractSequence(
                        seqname, seq_read, genome.replace(" ", "_")
                    )
            else:
                seq_read = "".join(seq.split()).strip()
            guides.append(seq_read)
        guides = "\n".join(list(set(guides)))
    if not all(
            [
                len(guide) == len(guides.split("\n")[0]) 
                for guide in guides.split("\n")
            ]
        ):
            guides = select_same_len_guides(guides)
    guides = guides.split("\n")
    dropdown_options = [
        {"label": i, "value": i} for i in range(1, len(guides[0]) + 1)
    ]
    return dropdown_options, dropdown_options


def check_mail_address(mail_address: str) -> bool:
    """Check mail address consistency.

    ...

    Parameters
    ----------
    mail_address : str
        Mail address

    Returns
    -------
    bool
    """

    if not mail_address:  # check wether is None or empty
        return False
    assert mail_address is not None
    if not isinstance(mail_address, str):
        raise TypeError(f"Expected {str.__name__}, got {type(mail_address).__name__}")
    mail_address_fields = mail_address.split("@")
    if len(mail_address_fields) > 1 and bool(mail_address_fields[-1]):
        return True
    return False
