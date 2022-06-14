"""Commands classes definiton.

TODO: complete docstring

CRISPRme provides ? commands:
* 
*
*


For each available command, we define the corresponding class.
"""


from crisprme.utils import exception_handler

from typing import List, NoReturn

import os


class CRISPRmeCommand(object):
    """CRISPRme command base class.

    ...

    Attributes
    ----------
    _threads : int
    _verbose : bool
    _debug : bool

    Methods
    -------
    None
    """

    def __init__(self, threads: int, verbose: bool, debug: bool) -> None:
        self._threads = threads
        self._verbose = verbose
        self._debug = debug

    def _get_threads(self):
        return self._threads
    
    @property
    def threads(self):
        return self._get_threads()

    def _get_verbose(self):
        return self._verbose
    
    @property
    def verbose(self):
        return self._get_verbose()

    def _get_debug(self):
        return self._debug

    @property
    def debug(self):
        return self._get_debug()


class CompleteSearch(CRISPRmeCommand):
    """Complete search command class. The class extends `CRISPRmeCommand` class.

    ...

    Attributes
    ----------
    _ref_genome : str
    _search_index : str
    _genome_index : str
    _pam_seq : str
    _bmax : int
    _mm : int
    _bdna : int
    _brna : int
    _annotation_file : str
    _nuclease : str
    _ref_comparison : bool
    _outdir : str
    _guides : List

    Methods
    -------
    write_params_file()
    """

    def __init__(
        self, 
        threads : int,
        verbose : bool,
        debug : bool,
        ref_genome: str,
        search_index: bool,
        genome_index: str,
        guides: str,
        pam_seq: str,
        bmax: int,
        mm: int,
        bdna: int,
        brna: int,
        annotation_file: str,
        nuclease: str,
        ref_comparison: bool,
        outname: str,
        outdir: str,
    ) -> None:
        super.__init__(threads, verbose, debug)  # initialize parent class
        self._ref_genome = ref_genome
        self._search_index = search_index
        self._genome_index = genome_index
        self._guides = guides
        self._pam_seq = pam_seq
        self._bmax = bmax
        self._mm = mm
        self._bdna = bdna
        self._brna = brna
        self._annotation_file = annotation_file
        self._nuclease = nuclease
        self._ref_comparison = ref_comparison
        self._outname = outname
        self._outdir = outdir

    def set_guides(self, guides: List[str]) -> NoReturn:
        """Set _guides attribute.

        ...

        Parameters
        ----------
        guides : List
            Guides

        Returns
        -------
        NoReturn 
        """
        if not isinstance(guides, list):
            exception_handler(
                TypeError,
                f"Expected {list.__name__}, got {type(guides).__name__}",
                True
            )
        self._guides = guides

    def set_main(self, mail_address: str) -> NoReturn:
        """Set mail_address (never used on command-line version).

        ...

        Parameters
        ----------
        mail_address : str
            Mail address

        Returns
        -------
        NoReturn
        """
        if not isinstance(mail_address, str):
            exception_handler(
                TypeError,
                f"Expected {str.__name__}, got {type(mail_address).__name__}",
                True
            )
        self._mail_address = mail_address

    def _get_outname(self):
        return self._outname
    
    @property 
    def outname(self):
        return self._get_outname()


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

        