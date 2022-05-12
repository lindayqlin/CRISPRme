"""Read, filter and merge VCF files. The functions below remove the variants not 
passing the filter and merge multi-variant alleles into a single allele. 
Moreover, call bcftools to left-align and normalize indels.

The results are stored in a new VCF file.
"""


import subprocess
import multiprocessing
import gzip
import sys
import glob
import os
 

def convert_vcf(vcf_fname: str, populations: str) -> str:
    """Read and filter the input VCF file. The filtered data are written in a
    new VCF file, maintaining the same name of the original VCF.

    ...

    Parameters
    ----------
    vcf_fname : str
        Input VCF file
    populations : str
        Populations file

    Returns
    -------
    str
        Output VCF file
    """

    if not isinstance(vcf_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(vcf_fname).__name__}"
        )
    if not os.path.isfile(vcf_fname):
        raise FileNotFoundError(f"Unable to find {vcf_fname}")
    if not isinstance(populations, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(populations).__name__}"
        )
    if not os.path.isfile(populations):
        raise FileNotFoundError(f"Unable to find {populations}")
    outvcf_fname = vcf_fname.replace("bgz", "gz")
    try:
        populations = open(populations, mode="r").readlines()  # populations list
        population_dict = {
            pop.split()[0].strip(): "0/0" 
            for pop in populations
            if "#" not in pop  # skip comments
        }
    except OSError as e:
        raise e
    try:
        vcf_in_handle = gzip.open(vcf_fname, mode="rt")
        vcf_out_handle = gzip.open(outvcf_fname, mode="wt") 
        # read VCF header
        header = []
        for line in vcf_in_handle:
            if "##" in line:  # header lines
                header.append(line.strip())
            else:
                # add populations to header in the new VCF file
                popheader = "\t".join(population_dict.keys())
                header.append(
                    "##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Sample Collapsed Genotype\">"
                )
                header.append(f"{line.strip()}\tFORMAT\t{popheader}\n")
                break 
        # write the header
        vcf_out_handle.write("\n".join(header))
        # read variants in the VCF
        for line in vcf_in_handle:
            line_split = line.strip().split()
            if line_split[6] == "PASS":  # skip rows with PASS on filter
                continue
            info = line_split[7].strip().split(";")
            for pop in population_dict.keys():
                population_dict[pop] = "0/0"
                # read AC for each gnomAD population and insert fake genotypes
                # for each sample
                for i, data in enumerate(info):
                    if f"AC_{pop}=" in data:
                        ac_value = int(data.split("=")[1])
                        if ac_value > 0:
                            population_dict[pop] = "0/1"
            line_split[7] = info[2]
            # write lines passing the filtering step on the out VCF
            outvcf_fname.write(
               f"{'\t'.join(line_split[:8])}\tGT\t{'\t'.join(population_dict.values())}\n"
            )
    except OSError as e:
        raise e
    finally:
        vcf_in_handle.close()
        vcf_out_handle.close()
    assert os.path.isfile(outvcf_fname)  # file should have been created
    assert os.stat(outvcf_fname).st_size > 0  # file should not be empty
    return outvcf_fname


def bcftools_merging(vcf_fname: str) -> None:
    """Call BCF tools to left-align and normalize indels available in the input
    VCF file.

    ...

    Parameters
    ----------
    vcf_fname : str
        Input VCF file
    
    Returns
    -------
    None
    """

    if not isinstance(vcf_fname, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(vcf_fname).__name__}"
        )
    if not os.path.isfile(vcf_fname):
        raise FileNotFoundError(f"Unable to find {vcf_fname}")
    vcf_fname_prefix = vcf_fname.split(".")
    vcf_fname_prefix[-3] = f"{vcf_fname_prefix[-3]}.collapsed"
    outvcf_fname = ".".join(vcf_fname_prefix)
    # call bcftools to left-align and normalize indels
    cmd = f"bcftools norm -m+ -O z -o {outvcf_fname} {vcf_fname}"
    code = subprocess.call(cmd, shell=True)
    if code != 0:
        raise subprocess.SubprocessError(f"An error occurred while running {cmd}")


def process_vcf(vcf_fname: str, populations: str) -> None:
    """Filter the input VCF file to keep only variants passing filtering and 
    collapse multi-variant alleles with shared reference into single entries.

    ...
    
    Parameters
    ----------
    vcf_fname: str
        Input VCF file
    populations : str
        Populations file

    Returns
    -------
    None
    """

    outvcf_fname = convert_vcf(vcf_fname, populations)  # filter VCF
    bcftools_merging(outvcf_fname)  # merge alleles and normalize indels
    # delete old VCF
    cmd = f"rm -f {outvcf_fname}"


# TODO: remove main() use only function
def main():
    vcf_dir = sys.argv[1]
    populations = open(sys.argv[2], mode="r").readlines()
    threads = 0
    try:
        threads = int(sys.argv[3])
    except:
        # limit no. cores to those restricted for current process 
        threads = len(os.sched_getaffinity(0)) - 2 
    pool = multiprocessing.Pool(threads)
    # call convert_vcf() for each VCF in the directory
    vcfs = glob.glob(os.path.join(vcf_dir, "*.vcf.bgz"))
    for vcf in vcfs:
        pool.apply_async(process_vcf, args=(vcf, populations,))
    # wait till all threads completed their job and join
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()

