"""Associate samples to their corresponding population and superpopulation.
Moreover, associate the superpopulations to the list of availbale populations 
and the populations to the list of considered samples.

Return the list of all available samples, populations and superpopulations in 
the input file. 

The input file is a TXT file containing four tab-separated columns:
- The first column contain the samples ID
- The second column the population ID
- The thirdcolumn contains the superpopulation ID
- The fourth column contains the sample's gender (if not available, the value 
    is 'n/a') (OPTIONAL)

The final result is a dictionary to associate in constant time samples to 
populations, superpopulations, etc. and the lists of the available , samples, 
populations, superpopulations, and samples gender.

If the input file does not exists or its format is not correct `None` is 
returned.
"""


from typing import Dict, List, Tuple

import os


def load_samples_association(
    sample_file: str
) -> Tuple[Dict, Dict, Dict, Dict, List, List, List, Dict]:
    """Check the input file format correctness and compute the dictionaries
    to associate in constant time the samples to populations, superpopulations,
    etc. and the lists of available samples, their geneder, populations, and 
    superpopulations.

    ...

    Parameters
    ----------
    sample_file : str   
        Input samples file

    Returns
    -------
    None
    """

    if not isinstance(sample_file, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(sample_file).__name__}"
        )
    if not os.path.isfile(sample_file):
        raise FileNotFoundError(f"Unable to locate {sample_file}")
    # define dictionaries
    samples_to_pops = {}
    pops_to_superpops = {}
    samples_to_gender = {}
    try:
        handle = open(sample_file, mode="r")
        for line in handle:
            if "#" in line:  # skip header lines
                continue
            line_split = line.strip().split()
            if len(line_split) < 3:
                raise ValueError(
                    str(
                        "Wrong input file format. The input TXT file must have "
                        "columns SAMPLE_ID, POPULATION_ID, SUPERPOPULATION_ID, "
                        "GENDER [Optional]"
                )
            )
            samples_to_pops[line_split[0]] = line_split[1]
            pops_to_superpops[line_split[1]] = line_split[2]
            try:
                samples_to_gender[line_split[0]] = line_split[3]
            except:  # gender not available
                samples_to_gender[line_split[0]] = "n/a"
    except OSError as e:
        raise e
    finally:
        handle.close()
    pops_to_samples = {}
    for sample in samples_to_pops.keys():
        try:
            pops_to_samples[samples_to_pops[sample]].add(sample)
        except KeyError:
            pops_to_samples[samples_to_pops[sample]] = set()
            pops_to_samples[samples_to_pops[sample]].add(sample)
    superpops_to_pops = {}
    for pop in pops_to_superpops.keys():
        try:
            superpops_to_pops[pops_to_superpops[pop]].add(pop)
        except KeyError:
            superpops_to_pops[pops_to_superpops[pop]] = set()
            superpops_to_pops[pops_to_superpops[pop]].add(pop)
    # get lists of samples, populations and superpopulations
    samples = list(samples_to_pops.keys())
    pops = list(pops_to_samples.keys())
    superpops = list(superpops_to_pops.keys())
    return (
        samples_to_pops, 
        pops_to_superpops, 
        superpops_to_pops, 
        pops_to_samples,
        samples,
        pops,
        superpops,
        samples_to_gender,
    )
