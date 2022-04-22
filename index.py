#!/usr/bin/env python


from app import app, URL, CRISPRme_DIRS, current_working_directory, cache
from pages import (
    main_page, 
    navbar_creation, 
    results_page,
    load_page,
    history_page,
    help_page, 
    contacts_page,
)

from dash.dependencies import Input, Output, State
from typing import Tuple

import dash_core_components as dcc
import dash_html_components as html

import os
import sys


# create navigation bar on top of the webpage
navbar = navbar_creation.navbar()
# hanlde multipage
app.layout = html.Div(
    [
        navbar,
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
        html.P(id="signal", style={"visibility": "hidden"})
    ]
)


def check_directories() -> None:
    """Check the existence of all the directories required by CRISPRme to 
    correctly run. The missing directories are created.

    ...

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    
    for d in CRISPRme_DIRS:
        if not os.path.exists(os.path.join(current_working_directory, d)):
            os.makedirs(os.path.join(current_working_directory, d))


# trigger page change
@app.callback(
    [Output('page-content', 'children'),
     Output('job-link', 'children')],
    [Input('url', 'href'),
     Input('url', 'pathname'),
     Input('url', 'search')],
    [State('url', 'hash')]
)
def changePage(
    href: str, path: str, search: str, hash_guide: str
) -> Tuple[html.Div, str]:
    """Change the displayed webpage, accordingly to the current URL address.

    ...

    Parameters
    ----------
    href : str
        URL
    path : str
        Path
    search : str
        Search
    hash_guide : str
        Guide hash

    Returns
    -------
    Tuple[html.Div, str]
    """

    if not isinstance(href, str):
        raise TypeError(f"Expected {str.__name__}, got {type(href).__name__}")
    if not bool(href):
        raise ValueError(f"Forbidden URL received ({href})")
    if not isinstance(path, str):
        raise TypeError(f"Expected {str.__name__}, got {type(path).__name__}")
    if not isinstance(search, str):
        raise TypeError(f"Expected {str.__name__}, got {type(search).__name__}")
    if path == "/load":
        return (
            load_page.load_page(), 
            f"{''.join(href.split('/'))[:-1]}/load{search}"
        )
    if path == "/result":
        job_id = search.split("=")[-1]
        if hash_guide is None or not bool(hash_guide):
            return (
                results_page.result_page(job_id),
                f"{URL}/load{search}" 
            )
        if "new" in hash_guide:  
            return (
                results_page.guide_page(job_id, hash_guide.split("#")[1]),
                f"{URL}/load{search}"
            )
        if "-Sample-" in hash_guide:
            return (
                results_page.sample_page(job_id, hash_guide.split("#")[1]), 
                f"{URL}/load{search}"
            )
        if "-Pos-" in hash_guide:
            return (
                results_page.cluster_page(job_id, hash_guide.split("#")[1]), 
                f"{URL}/load{search}"
            )
        return (
            results_page.result_page(job_id),
            f"{URL}/load{search}" 
        )
    if path == "/user-guide":
        return (
            help_page.helpPage(), 
            f"{URL}/load{search}"
        )
    if path == "/contacts":
        return (
            contacts_page.contact_page(), 
            f"{URL}/load{search}"
        )
    if path == "/history":
        return (
            history_page.history_page(), 
            f"{URL}/load{search}"
        )
    if path == "/index":
        return main_page.index_page(), "/index"
    return main_page.index_page(), "/index"


if __name__ == "__main__":
    check_directories()
    if "--website" in sys.argv[1:]:  # online
        app.run_server(
            host="0.0.0.0", 
            port=80, 
            debug=False,
            dev_tools_ui=False, 
            dev_tools_props_check=False
        )
        cache.clear()  # delete cache when server is closed
    else:  # offline
        app.run_server(
            host="0.0.0.0", 
            port=8080, 
            debug=False,
            dev_tools_ui=False, 
            dev_tools_props_check=False
        )
        cache.clear()  # delete cache when server is close
