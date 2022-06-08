"""CRISPRme extension of ArgumentParser and HelpFormatter.

The ArgumentParser and HelpFormatter classes are customized to assign a different 
style to the help with respect to the default one and when a wrong argument is 
given, CRSPRme reminds the user how to call the command-line help. 
"""


from crisprme.crisprme import __version__

from argparse import ArgumentParser, HelpFormatter, SUPPRESS
from typing import Dict, NoReturn, Optional, Tuple
from colorama import Fore 

import sys


class CrisprmeArgumentParser(ArgumentParser):
    """CRISPRme extension of ArgumentParser class.
    The class extension allows to change argparse's default help style and 
    formatting. 
    Moreover, customize default argparse error messages style and format.

    ...

    Methods
    -------
    error(msg)
        Prints the error message with the new style and format.
    """

    class CrisprmeHelpFormatter(HelpFormatter):
        """CRISPRme extension of HelpFormatter class.

        Define new help format and style.

        ...

        Methods
        -------
        add_usage(usage, actions, groups, prefix=None)
            Format help 
        """

        def add_usage(
            self, 
            usage: str, 
            actions: str, 
            groups: str, 
            prefix: Optional[str] = "None"
        ) -> None:

            assert isinstance(usage, str)  # make sure to have valid data
            if usage is not SUPPRESS:
                args = usage, actions, groups, ""  # create help item
                self._add_item(self._format_usage, args)  # add item to help
    
    def __init__(
        self, *args: Tuple, **kwargs: Dict
    ) -> None:
        
        kwargs["formatter_class"] = self.CrisprmeHelpFormatter  # format help
        # restyle usage message
        kwargs["usage"] = kwargs["usage"].replace("{version}", __version__)
        super().__init__(*args, **kwargs)  # initialize ArgumentParser object


    def error(self, message: str) -> NoReturn:
        """Raise Parser error and print the input message.

        ...

        Parameters
        ----------
        message: str
            error message

        Returns
        -------
        None
        """

        assert isinstance(message, str)
        # color error message in red using colorama 
        errmsg = Fore.RED + f"\nERROR: {message}." + Fore.RESET + "\n\nRun \"crisprme --help\" to see usage\n\n"
        # print error message to stderr
        sys.stderr.write(errmsg)
        sys.exit(2)  # ERRCODE 2 --> args parser error


    def error_noargs(self) -> NoReturn:
        """ When no argument is given from the command-line, CRISPRme prints 
        the help, instead of raising an error.

        ...

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.print_help()  # print help message (new style and format)
        sys.exit(2)  # ERRCODE 2 --> args parser error

