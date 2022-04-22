"""Define constant variables used throughout all CRISPRme code.
"""


from flask_caching import Cache  # for cache of .targets or .scores

import dash_bootstrap_components as dbc

import dash
import os
import concurrent.futures  # For workers and queue


# base empty URL address
URL = ""  
# CRISPRme directories
CRISPRme_DIRS = [
    "Genomes", 
    "Results", 
    "Dictionaries", 
    "VCFs", 
    "Annotations", 
    "PAMs", 
    "samplesIDs"
]
# CSS style sheets
external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css", dbc.themes.BOOTSTRAP
]
# dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=external_stylesheets, 
    suppress_callback_exceptions=True
)
# get app location
app_location = os.path.realpath(__file__)
# app main directory
app_main_directory = "".join([os.path.dirname(app_location), "/"])  # for scripts
current_working_directory = "".join([os.getcwd(), "/"])  # for python files
# app name
app.title = "CRISPRme"
# necessary if update element in a callback generated in another callback
# app.config['suppress_callback_exceptions'] = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
# get app location
app_location = "".join([os.path.dirname(os.path.abspath(__file__)), "/"])
# operators used while filtering pandas dataframes
operators = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "]
] 
# online options
ONLINE = False  # NOTE change to True for online version, False for offline
DISPLAY_OFFLINE = ""
DISPLAY_ONLINE = ""
if ONLINE:
    DISPLAY_OFFLINE = "none"
    DISPLAY_ONLINE = ""
else:  # offline
    DISPLAY_OFFLINE = ""
    DISPLAY_ONLINE = "none"
# job manager
exeggutor = concurrent.futures.ProcessPoolExecutor(
    max_workers=1
)  # handle max 1 job at a time
# define cache and configuration options
CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": ("Cache")  # os.environ.get('REDIS_URL', 'localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)
