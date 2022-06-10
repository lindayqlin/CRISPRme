"""CRISPRme directory location within filesystem.
"""

import os


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
CONDA_PATH = "opt/crisprme/src/crisprme/PostProcess"
ORIGIN_PATH = os.path.dirname(os.path.abspath(__file__))[:-3] + CONDA_PATH
WEB_PATH = ORIGIN_PATH[:-3] + "opt/crisprme"
CURRENT_WORKING_DIRECTORY = os.getcwd()

