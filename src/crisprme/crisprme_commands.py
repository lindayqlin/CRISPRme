"""Commands classes definiton.

TODO: complete docstring

CRISPRme provides ? commands:
* 
*
*


For each available command, we define the corresponding class.
"""


from tkinter import OUTSIDE
from crisprme.utils import exception_handler

import sys
import os


class CRISPRmeCommand(object):
    """CRISPRme command base class.

    ...

    Attributes
    ----------
    None

    Methods
    -------
    None
    """

    def __init__(self) -> None:
        pass


class CompleteSearch(CRISPRmeCommand):
    """Complete search command class. The class extends `CRISPRmeCommand` class.

    ...

    Attributes
    ----------
    None

    Methods
    -------
    None
    """

    def __init__(
        self, 
        ref_genome: str,
        search_index: bool,
        genome_index: str,
        pam_seq: str,
        bmax: int,
        mm: int,
        bdna: int,
        brna: int,
        annotation_file: str,
        nuclease: str,
        ref_comparison: bool,
        outdir: str,
    ) -> None:

        self._ref_genome = ref_genome
        self._search_index = search_index
        self._genome_index = genome_index,
        self._pam_seq = pam_seq
        self._bmax = bmax
        self._mm = mm
        self._bdna = bdna
        self._brna = brna
        self._annotation_file = annotation_file
        self._nuclease = nuclease
        self._ref_comparison = ref_comparison
        self._outdir = outdir


    def write_params_file(self) -> None:
        """Write complete search Paramaters in a TXT file.
        
        ...

        Parameters
        ----------
        self

        Returns
        -------
        None
        """

        try:
            with open(
                os.path.join(self._outdir, "Params.txt"), mode="w"
            ) as handle:
                handle.write(
                    f"Genome_selected\t{self._ref_genome.replace(' ', '_')}\n"
                )
                handle.write(f"Genome_ref\t{self._ref_genome}\n")
                if self._search_index:
                    handle.write(f"Genome_idx\t{self._genome_index}\n")
                else:
                    handle.write(f"Genome_idx\tNone\n")
                handle.write(f"Pam\t{self._pam_seq}\n")
                handle.write(f"Max_bulges\t{self._bmax}\n")
                handle.write(f"Mismatches\t{self._mm}\n")
                handle.write(f"DNA\t{self._bdna}\n")
                handle.write(f"RNA\t{self._brna}\n")
                handle.write(f"Annotation\t{self._annotation_file}\n")
                handle.write(f"Nuclease\t{self._nuclease}\n")
                handle.write(f"Ref_comp\t{self._ref_comparison}\n")
        except:
            # aleays better to trace this kind of errors ;)
            exception_handler(OSError, "Unable to write 'Params.txt'", True)
        finally:
            handle.close()  # close channel

        