"""Create SQL database from ```sg1617.total.scored.txt``` file.

First, preprocess table's column names, then create the table using the columns
inside a list.

To add columns to the table, it has to be added a column element "{} TYPE" 
inside the string. The allowed types are:
- TEXT
- INTEGER
- NUMERIC

The file rows are inserted in the table one by one. To add columns add a "?".

Finally, creates the indexes to speed-up results querying and visualization.
If column names are changed, to maintain indexes consistency the indexes parameters 
must be changed accordingly.

Example:

# create the index to speedup columns ordering by Total_1
# always include Real_Guide_1 to use multiple guides
c.execute("CREATE INDEX IF NOT EXISTS rgt ON final_table(Real_Guide_1, Total_1)")

NOTE: The same type of indexes are created when using multiple orders.
"""


from .postprocess_utils import DTYPE_SQLTYPE_MAP, DB_COLNAMES

from typing import List

import pandas as pd

import sqlite3
import time
import sys
import os


def dtype_to_sqltype(dtype: str) -> str:
    """Convert pandas data types to SQL types.

    ...

    Parameters
    ----------
    dtype : str
        pandas datatype
    
    Returns
    -------
    str
    """

    if not isinstance(dtype, str):
        raise TypeError(f"Expected {str.__name__}, got {type(dtype).__name__}")
    try:
        sql_type = DTYPE_SQLTYPE_MAP[dtype]
    except KeyError:  # type not listed (unlikely)
        sql_type = "TEXT"  # assign TEXT SQL type by default
    return sql_type


def add_data(data: List, conn: sqlite3.Connect, c: sqlite3.Cursor) -> None:
    """Add data chunks to the database table.
    
    ...
    
    Parameters
    ----------
    data : List
        Data to enter in the table
    conn : sqllite3.Connection
        Opened connection to the database
    c : sqlite3.Cursor
        Database cursor

    Returns
    -------
    None
    """

    sys.stderr.write("Adding chunk of data\n")
    qmarks = ["?"] * len(data[0])
    qmarks = ",".join(qmarks)
    # insert data in the table
    c.executemany(f"INSERT INTO final_table VALUES ({qmarks})", data)
    # communicate to the database
    conn.commit()


def index_db(conn: sqlite3.Connection, c: sqlite3.Cursor) -> None:
    """Create database index.
    
    ...
    
    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection
    c : sqlite3.Cursor
        Cursor to Database
    
    Returns
    -------
    None
    """

    try:
        # index each database column
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_mm ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[1]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_blg ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[2]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_tot ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[3]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_cfd ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[4]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_risk ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[5]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_chrom_pos ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[8]}\",\"{DB_COLNAMES[6]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_samples ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[7]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_mm_blg_blgt ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[1]}\",\"{DB_COLNAMES[2]}\",\"{DB_COLNAMES[9]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_mm_tot ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[1]}\",\"{DB_COLNAMES[3]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_mm_cfd ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[1]}\",\"{DB_COLNAMES[4]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_blg_tot ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[2]}\",\"{DB_COLNAMES[3]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_blg_cfd ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[2]}\",\"{DB_COLNAMES[4]}\")"
        )
        c.execute(
            f"CREATE INDEX IF NOT EXISTS g_tot_cfd ON final_table(\"{DB_COLNAMES[0]}\",\"{DB_COLNAMES[3]}\",\"{DB_COLNAMES[4]}\")"
        )
        conn.commit()  # commit index to database
    except:
        raise sqlite3.DatabaseError(
            f"An error occurred during database indexing"
        )


def create_db(infile: str, outfile: str) -> None:
    """Create SQL3 database to efficiently query CRISPRme search results.

    ...

    Parameters
    ----------
    infile : str
        CRISPRme search results
    outfile : str
        Database filename prefix

    Returns
    -------
    None
    """
    
    if not isinstance(infile, str):
        raise TypeError(f"Expected {str.__name__}, got {type(infile).__name__}")
    if not os.path.isfile(infile):
        raise FileNotFoundError(f"Unable to locate {infile}")
    if not isinstance(outfile, str):
        raise TypeError(f"Expected {str.__name__}, got {type(outfile).__name__}")
    if not os.path.isfile(outfile):
        raise FileNotFoundError(f"Unable to locate {outfile}")
    print("Starting database creation...")
    # open database connection
    conn = sqlite3.connect(f"{outfile}.db")
    c = conn.cursor()  # create cursor to db file
    # define database structure
    db_schema = None
    try:
        # read and load results
        results = pd.read_csv(
            infile, sep="\t", index_col=False, na_filter=False, nrows=1000
        )
        # convert pandas data types to SQL data types
        sql_types = [dtype_to_sqltype(dtype) for dtype in results.dtypes]
        # build database schema
        db_schema = [
            f"\"{col}\" {sql_types[i]}" for i, col in enumerate(df.columns)
        ]
        
    except:
        # if something fails, read the report and force all columns to TEXT 
        # SQL type
        try:
            with open(infile, mode="r") as handle:
                cols = handle.readline().strip().split()  # read only the first line
                # force all columns to TEXT type
                db_schema = [f"\"{col}\" TEXT" for col in cols]
        except OSError as e:
            raise e     
    assert db_schema is not None  # schema should have been created
    db_schema = ", ".join(db_schema)
    # create database table
    q = f"CREATE TABLE IF NOT EXISTS final_table ({db_schema})"
    c.execute(q)
    try:
        with open(infile, mode="r") as handle:
            data = []
            handle.readline()  # skip header line
            chunk_size = 0
            for line in handle:
                g = line.strip().split()
                data.append(g)
                chunk_size += 1
                if chunk_size == 500000:  # stop when reached data chunk limit
                    # insert data chunk to database table
                    add_data(data, conn, c)
                    # reset data and size
                    data = []
                    chunk_size = 0
            if chunk_size > 0:  # insert last chunk of data
                add_data(data, conn, c)
    except OSError as e:
        raise e
    print("Indexing the database...")
    index_db(conn, c)
    conn.close()  # close database connection
    print("Database correctly created")


def main():
    infile = sys.argv[1]
    outfile = sys.argv[2]
    create_db(infile, outfile)


if __name__ == "__main__":
    main()
