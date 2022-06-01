"""Create the area graph to describe CFD distribution. 

CFD scores (0-100) are placed on the x axis, while the y axis counts the number
of targets for each score, found in the REF and VAR genomes.

The graph is created starting from ```*.CFDGraph.txt``` file.

TODO: Make the graph interactive, so that the user could choose a CFD score and 
visualize the targets with that score. NOTE the function 
```display_selected_data``` perform the first part, it doesn't work with the 
current area graph.

NOTE take a look at:

https://plotly.com/python/filled-area-plots/ 
https://dash.plotly.com/dash-core-components/graph
https://dash.plotly.com/interactive-graphing

NOTE 127.0.0.1:8050 to open the page (or 0.0.0.0:8050 on localhost)
"""


from typing import Dict, List

import plotly.graph_objects as go  # or plotly.express as px
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html

import os


def create_graph(
    cfd_distribution: Dict, showlog: bool
) -> go.Figure:
    """Create the CFD distribution graph.

    ...

    Parameters
    ----------
    cfd_distribution : Dict
        CFD score distribution
    showlog : bool
        Show graph in logarithmic scale

    Returns
    -------
    plotly.graph_objects.Figure
    """

    if not isinstance(cfd_distribution, dict):
        raise TypeError(
            f"Expected {dict.__name__}, got {type(cfd_distribution).__name__}"
        )
    # create the figure and the graph
    fig = go.Figure()  # alternatively we caould use any Plotly Express function
    fig.add_trace(
        go.Scatter(
            x=list(range(101)),
            y=list(cfd_distribution["ref"]),
            fill="tozeroy",
            name="Targets in Reference",
        )
    )
    fig.add_trace(
        go.Scatter(
            go.Scatter(
                x=list(range(101)),
                y=list(cfd_distribution["var"]),
                fill="tozeroy",
                name="Targets in Enriched"
            )
        )
    )
    if showlog:
        fig.update_layout(
            yaxis_type="log", 
            xaxis_type="CFD Value", 
            yaxis_title="Number of Targets (log scale)", 
            hovermode="x"
        )
    else:
        fig.update_layout(
            xaxis_title="CFD Value",
            yaxis_title="Number of Targets",
            hovermode="x"
        )
    return fig


def CFD_graph(cfd_data_path: str) -> List:
    """Compute the CFD graph and create the corresponding HTML div.

    ...

    Parameters
    ----------
    cfd_data_path : str
        Path to CFD data

    Returns
    -------
    List
    """

    if cfd_data_path is None:
        return ""
    if not isinstance(cfd_data_path, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(cfd_data_path).__name__}"
        )
    if not os.path.exists(cfd_data_path):
        raise FileNotFoundError(f"Unable to locate {cfd_data_path}")
    # begin HTML div creation
    final_list = []
    final_list.append(
        html.P(
            str(
                "Number of targets found in the Reference and Enriched Genome "
                "for each CFD Score value (0-100)"
            )
        )
    )
    # read CFD scores distribution
    cfd_distribution = pd.read_csv(cfd_data_path, sep="\t") 
    final_list.append(
        html.Div(
            dcc.Graph(
                figure=create_graph(cfd_distribution, True), id="CFD-graph-id"
            ),
            id="div-CFD-graph"
        )
    )
    final_list.append(html.Div(id="selected-data"))
    # add new line to HTML div
    final_list.append(html.Br())
    # return th HTML page with the CFD graph
    return final_list
