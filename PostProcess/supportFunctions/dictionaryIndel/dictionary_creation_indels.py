"""Create dictionaries to handle samples indels and efficiently recover the 
indels associated to each considered individual.
"""


import gzip
import sys
import json
import time
import os


def create_variant_dictionary(vcf_file: str, sample: str, outdir: str) -> None:
    """Compute dictionaries to store indels for each sample in the dataset. 
    The indel position written in the dictionary is adjusted accordingly
    to the number of nucleotides added or removed by the indel.

    CAVEAT: The FASTA filename and the #CHROM column name must match.

    The processing of each VCF file could take up to ~20 minutes and use 
    ~80 GB of memory.

    ...

    Parameters
    ----------
    vcf_file : str
        VCF file
    sample : str
        Sample
    outdir : str
        Output directory
    
    Returns
    -------
    None
    """

    if not isinstance(vcf_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(vcf_file).__name__}"
        )
    if not os.path.isfile(vcf_file):
        raise FileNotFoundError(f"Unable to locate {vcf_file}")
    if not isinstance(sample, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(sample).__name__}"
        )
    if not isinstance(outdir, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(outdir).__name__}"
        )
    if not os.path.isdir(outdir):
        raise FileNotFoundError(f"Unable to locate {outdir}")
    # recover the chromosome
    chrom = None
    for e in vcf_file.split("."):
        if "chrom" in e:
            chrom = e
            break
    assert chrom is not None
    start_time = time.time()
    variants_dict = {}
    # prefix to add to chromosome name (if hg38 OK, otherwise add "chr", e.g. hg19)
    chrom_prefix = ""  
    offset = 0  # value to sum to the variant position --> adjusted for each indel
    try:
        vcf_handle = gzip.open(vcf_file, mode="rb")  # read the GZipped VCF
        for line in vcf_handle:
            line = line.decode("ascii")  # decode bits lines
            if "#CHROM" in line:  # header column
                vcf_cols = line.strip().split()  
                sample_col = vcf_cols.index(sample)  # sample column index
                break  # proceed reading variants
        line_split = vcf_handle.readline().decode("ascii").strip().split()
        if "chr" not in line_split[0]:  # check if chromosome name has the right format
            chrom_prefix = "chr"
        samples = []
        nucs = []
        haplotype = line_split[sample_col].split("|")
        # TODO: complete this procedure
        # NOTE: is possible to also have 2|1 cases
        for hap in haplotype: 
            if hap == "0":
                continue
            try:
                # EXAMPLE: let us assume VAR v is TT, TTA, TTT and SAMPLE
                #   genotype is 0|2, the variant is TTA
                variant = int(hap) - 1
            except ValueError as e:
                raise e
            samples.append(sample)  # add sample
            # compute offset
            offset += (len(line[3]) - len(line[4].split(",")[variant]))
            if len(line[3]) != 1 or len(line[4].split(",")[variant]) != 1:
                break  # store only the SNP
            chrom_pos = f"{chrom_prefix}{line[0]},{offset + int(line[1])}"
            # add ref and alt nuc in the last two positions
            # E.g. chrX,100 --> sample1,sample5,sample10;A,T
            # if no sample is found the dict key would be chrX,100 --> ;A,T
            nucs.append(line[3])  # REF
            nucs.append(line[4].split(",")[variant])  # VAR
            try:
                variants_dict[chrom_pos] = ";".join(
                    [",".join(samples), ",".join([nucs])]
                )  # sample found
            except KeyError:
                variants_dict[chrom_pos] = f";{','.join(nucs)}"  # no sample
        for line in vcf_handle:
            line = line.decode("ascii").strip().split("\t")
            samples = []
            nucs = []
            if "1" in line_split[sample_col]:  # variant found for current sample
                samples.append(sample)
                chrom_pos = f"{chrom_prefix}{line[0],{line[1]}}"
                nucs.append(line[3])  # REF
                nucs.append(line[4])  # VAR
                try:
                    variants_dict[chrom_pos] = ";".join(
                        [",".join(samples), ",".join([nucs])]
                    )  # sample found
                except KeyError:
                    variants_dict[chrom_pos] = f";{','.join(nucs)}"  # no sample
    except OSError as e:
        raise e
    finally:
        vcf_handle.close()
    # store dictionaries in JSON file
    try:
        out_json_fname = os.path.join(
            f"{outdir}_{sample}", f"my_dict_{chrom}.json"
        )
        json_handle = open(out_json_fname, mode="w")
        json.dump(variants_dict, json_handle)  # write the JSON
    except OSError as e:
        raise e
    finally:
        json_handle.close()
    stop_time = time.time()
    sys.stderr.write(
        str(
            f"Creation of my_dict_{chrom}.json completed for sample {sample} "
            "in %.2fs" % (stop_time - start_time)
        )
    )
