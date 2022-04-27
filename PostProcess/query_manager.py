"""Perform efficient queries on the SQL results database.

Two main querying policies are defined to recover the requested results:
- queries applying threshold values on the recovered results
- queries without applying thresholds

The input parameters of each querying function are modified in order to be 
consistent with the column names available in the database tables
"""


from .postprocess_utils import GUIDE_COLUMN, FILTERING_CRITERIA

import pandas as pd
import sqlite3
import os


def threshold_query(
    filter_target: str, 
    n_clicks: int, 
    page_current: int, 
    page_size: int, 
    radio_order: str, 
    order_drop: str, 
    thresh_drop: str, 
    maxdrop: str, 
    ascending: str, 
    job_url: str, 
    guide: str, 
    current_working_directory: str
) -> pd.DataFrame:
    """Perform efficient queries on the search results. The search results are 
    stored in a SQL database in order to improve query running time.
    
    The queries are performed furtherly filtering the results according to the
    input threshold.

    ...

    Parameters
    ----------
    filter_target : str
        Filtering target
    n_clicks : int
        Clicks
    page_current : int
        Current page
    page_size : int
        Page size
    radio_order : str
    order_drop : str
    thresh_drop : str
    maxdrop : str
    ascending : str
    job_url : str
    guide: str
    current_working_directory : str
    """

    if not isinstance(filter_target, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(filter_target).__name__}"
        )
    if filter_target not in FILTERING_CRITERIA:
        raise ValueError(f"Forbidden filtering criterion ({filter_target})")
    if ascending is not None:
        if not isinstance(ascending, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(ascending).__name__}"
            )
    if not isinstance(job_url, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(job_url).__name__}"
        )
    if not isinstance(current_working_directory, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(current_working_directory).__name__}"
        )
    if not isinstance(guide, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(guide).__name__}"
        )
    if not os.path.isdir(current_working_directory):
        raise FileNotFoundError(f"Unable to locate {current_working_directory}")
    if ascending is None:
        ascending = "DESC"  # sort results in descending 
    job_name = job_url[5:]
    # path to db
    db_path = os.path.join(
        current_working_directory, "Results", job_name, f".{job_name}.db"
    )
    # open connection to db
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    params = [guide, page_size, page_current * page_size]  # query parameters
    # check which filtering criterion has been chosen
    if filter_target == FILTERING_CRITERIA[0]:  # CFD score 
        radio_order = f"{radio_order}_(highest_CFD)"
        order_drop = f"{order_drop}_(highest_CFD)"
    elif filter_target == FILTERING_CRITERIA[1]:  # mismatches and bulges
        radio_order = f"{radio_order}_(fewest_mm+b)"
        order_drop = f"{order_drop}_(fewest_mm+b)"
    elif filter_target == FILTERING_CRITERIA[2]:  # CRISTA score
        if FILTERING_CRITERIA[0] in radio_order:
            radio_order = replace_cfd_crista(radio_order)
        if FILTERING_CRITERIA[0] in order_drop:
            order_drop = replace_cfd_crista(order_drop)
        radio_order = f"{radio_order}_(highest_CRISTA)"
        order_drop = f"{order_drop}_(highest_CRISTA)"
    # double sorting
    if order_drop != "None_(highest_CFD)": 
        if maxdrop is None:
            maxdrop = 1000
        # perform query
        res_table = pd.read_sql_query(
            "SELECT * FROM final_table WHERE \"{}\"=? AND \"{}\" BETWEEN {} AND {} ORDER BY \"{}\" {},\"{}\" {}  LIMIT ? OFFSET ?".format(
                GUIDE_COLUMN, 
                radio_order, 
                thresh_drop, 
                maxdrop, 
                radio_order, 
                ascending, 
                order_drop, 
                ascending
            ), 
            conn, 
            params=params
        )
    else:  # single sorting
        if maxdrop is None:  
            maxdrop = 1000
        res_table = pd.read_sql_query(
            "SELECT * FROM final_table WHERE \"{}\"=? AND \"{}\" BETWEEN {} AND {} ORDER BY \"{}\" {} LIMIT ? OFFSET ?".format(
                GUIDE_COLUMN, 
                radio_order, 
                thresh_drop, 
                maxdrop, 
                radio_order, 
                ascending
            ), 
            conn, 
            params=params
        ) 
    # close connection to db
    conn.commit()
    conn.close()
    return res_table


def nothreshold_query(
    filter_target: str, 
    n_clicks: int, 
    page_current: int, 
    page_size: int, 
    radio_order: str, 
    order_drop: str, 
    ascending: str, 
    job_url: str, 
    guide: str, 
    current_working_directory: str
) -> pd.DataFrame:
    """Perform efficient queries on the search results. The search results are 
    stored in a SQL database in order to improve query running time.

    ...

    Parameters
    ----------
    filter_target : str
        Filtering target
    n_clicks : int
        Clicks
    page_current : int
        Current page
    page_size : int
        Page size
    radio_order : str
    order_drop : str
    thresh_drop : str
    maxdrop : str
    ascending : str
    job_url : str
    current_working_directory : str
    """

    if not isinstance(filter_target, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(filter_target).__name__}"
        )
    if filter_target not in FILTERING_CRITERIA:
        raise ValueError(f"Forbidden filtering criterion ({filter_target})")
    if ascending is not None:
        if not isinstance(ascending, str):
            raise TypeError(
                f"Expected {str.__name__}, got {type(ascending).__name__}"
            )
    if not isinstance(job_url, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(job_url).__name__}"
        )
    if not isinstance(current_working_directory, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(current_working_directory).__name__}"
        )
    if not isinstance(guide, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(guide).__name__}"
        )
    if not os.path.isdir(current_working_directory):
        raise FileNotFoundError(f"Unable to locate {current_working_directory}")
    if ascending == None:
        ascending = "DESC"
    job_name = job_url[5:]
    # path to db
    db_path = os.path.join(
        current_working_directory, "Results", job_name, f".{job_name}.db"
    )
    # open connection to db
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    params = [guide, page_size, page_current * page_size]
    # check which filtering criterion has been chosen
    if filter_target == FILTERING_CRITERIA[0]:  # CFD score
        radio_order = f"{radio_order}_(highest_CFD)"
        order_drop = f"{order_drop}_(highest_CFD)"
    elif filter_target == FILTERING_CRITERIA[1]:  # mismatches and bulges
        radio_order = f"{radio_order}_(fewest_mm+b)"
        order_drop = f"{order_drop}_(fewest_mm+b)"
    elif filter_target == FILTERING_CRITERIA[2]:  # CRISTA score
        if FILTERING_CRITERIA[0] in radio_order:
            radio_order = replace_cfd_crista(radio_order)
        if FILTERING_CRITERIA[0] in order_drop:
            order_drop = replace_cfd_crista(order_drop)
        radio_order = f"{radio_order}_(highest_CRISTA)"
        order_drop = f"{order_drop}_(highest_CRISTA)"
    if order_drop != "None_(highest_CFD)":
        # multiple sorting
        res_table = pd.read_sql_query(
            "SELECT * FROM final_table WHERE \"{}\"=? ORDER BY \"{}\" {}, \"{}\" {} LIMIT ? OFFSET ?".format(
                GUIDE_COLUMN, 
                radio_order, 
                ascending, 
                order_drop, 
                ascending
            ), 
            conn, 
            params=params
        )
    else:
        # single sorting
        res_table = pd.read_sql_query(
            "SELECT * FROM final_table WHERE \"{}\"=? ORDER BY \"{}\" {} LIMIT ? OFFSET ?".format(
                GUIDE_COLUMN, 
                radio_order, 
                ascending
            ), 
            conn, 
            params=params
        )
    # close connection to db
    conn.commit()
    conn.close()
    return res_table


def replace_cfd_crista(order_element: str) -> str:
    """Replace CFD with CRISTA in the given order element.

    ...

    Paramters
    ---------
    order_element : str
        Order element

    Returns
    -------
    str
    """

    if not isinstance(order_element, str):
        raise TypeError(
            f"Expected {str.__name__}, got {type(order_element).__name__}"
        )
    assert "CFD" in order_element
    order_element = order_element.replace("CFD", "CRISTA")
    return order_element
