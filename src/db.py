import duckdb
import pandas as pd
import os
import re


class PitchDB:
    """
    Database manager using DuckDB for high-performance analytical queries.
    Handles storage and retrieval of raw and processed Statcast data.

    DuckDB is chosen over PostgreSQL because it operates directly on
    Parquet files and in-memory DataFrames with no server setup required,
    while delivering query speeds 3-10x faster for analytical workloads
    at our data scale (1-2M rows).
    """

    def __init__(self, db_path: str = "data/pitching_data.db") -> None:
        self.db_path = db_path
        # Create the data directory if it doesn't exist yet
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _validate_table_name(self, name: str) -> None:
        """
        Validate table name to prevent SQL injection.
        Only allows alphanumerics and underscores, must start with a letter.
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValueError(f"Invalid table name: '{name}'")

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return a connection to the local DuckDB database file."""
        return duckdb.connect(self.db_path)

    def save_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        mode: str = "replace"
    ) -> None:
        """
        Save a pandas DataFrame to a DuckDB table.

        Args:
            df: DataFrame to persist.
            table_name: Target table name in the database.
            mode: 'replace' drops and recreates the table (default).
                  'append' inserts rows into an existing table,
                  or creates it if it doesn't exist yet.
        """
        self._validate_table_name(table_name)

        with self.get_connection() as con:
            if mode == "replace":
                con.execute(f"DROP TABLE IF EXISTS {table_name}")
                con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            elif mode == "append":
                existing_tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
                if table_name in existing_tables:
                    con.execute(f"INSERT INTO {table_name} SELECT * FROM df")
                else:
                    # Table doesn't exist yet — create it from this DataFrame
                    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            else:
                raise ValueError(f"Invalid mode '{mode}'. Use 'replace' or 'append'.")

        print(f"[db] Saved {len(df):,} rows → '{table_name}' (mode={mode})")

    def query_to_df(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return the result as a pandas DataFrame.

        Args:
            sql: Any valid DuckDB SQL string.

        Returns:
            Query result as a DataFrame.
        """
        with self.get_connection() as con:
            return con.execute(sql).df()

    def table_info(self, table_name: str) -> pd.DataFrame:
        """
        Return schema information (column names and types) for a given table.
        Useful for quickly inspecting what's stored without loading all rows.
        """
        self._validate_table_name(table_name)
        return self.query_to_df(f"PRAGMA table_info('{table_name}')")

    def list_tables(self) -> list[str]:
        """Return a list of all tables currently in the database."""
        with self.get_connection() as con:
            result = con.execute("SHOW TABLES").fetchall()
            return [t[0] for t in result]