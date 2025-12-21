import os
import logging
import mysql.connector
from mysql.connector import pooling

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """Bridge between Flask and MySQL using connection pooling."""
    def __init__(self):
        try:
            host = os.getenv("MYSQL_HOST")
            user = os.getenv("MYSQL_USER")
            password = os.getenv("MYSQL_PASSWORD", "")
            database = os.getenv("MYSQL_DB")
            port_env = os.getenv("MYSQL_PORT")
            port = int(port_env) if port_env else 3306

            if not host or not user or not database:
                raise ValueError(
                    "Database configuration error: check .env for MYSQL_HOST, MYSQL_USER, MYSQL_DB"
                )

            self.poolconfig = {
                "host": host,
                "user": user,
                "password": password,
                "database": database,
                "port": port,
            }

            pool_size = int(os.getenv("MYSQL_POOL_SIZE", "10"))

            try:
                self.pool = pooling.MySQLConnectionPool(
                    pool_name="betrivals_pool",
                    pool_size=pool_size,
                    pool_reset_session=True,
                    **self.poolconfig,
                )
            except mysql.connector.Error as err:
                # Unknown database -> create DB then retry
                if getattr(err, "errno", None) == 1049:
                    logger.info("Database '%s' does not exist, attempting to create it.", database)
                    tmp_conn = None
                    tmp_cursor = None
                    try:
                        tmp_conn = mysql.connector.connect(
                            host=host,
                            user=user,
                            password=password,
                            port=port,
                        )
                        tmp_cursor = tmp_conn.cursor()
                        tmp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
                        tmp_conn.commit()
                        logger.info("Database '%s' created or already exists.", database)

                        self.pool = pooling.MySQLConnectionPool(
                            pool_name="betrivals_pool",
                            pool_size=pool_size,
                            pool_reset_session=True,
                            **self.poolconfig,
                        )
                    except mysql.connector.Error as e:
                        logger.exception("Failed to create database '%s': %s", database, e)
                        raise
                    finally:
                        if tmp_cursor:
                            try:
                                tmp_cursor.close()
                            except Exception:
                                pass
                        if tmp_conn:
                            try:
                                tmp_conn.close()
                            except Exception:
                                pass
                else:
                    logger.exception("Error while creating connection pool: %s", err)
                    raise

        except Exception as e:
            logger.exception("Failed to initialize DatabaseConnector: %s", e)
            raise

    def _get_connection(self):
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as err:
            logger.exception("Error while getting connection from pool: %s", err)
            raise

    def execute_query(self, query, params=None, fetch_all=True):
        """
        Execute a single query safely.
        - READ queries: returns rows (list[dict]) if fetch_all=True else single row (dict|None)
        - WRITE queries: commits and returns None
        """
        conn = None
        cursor = None

        # normalize params
        if params is None:
            params = ()

        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(query, params)

            q = query.strip().lower()
            is_read = (
                q.startswith("select")
                or q.startswith("show")
                or q.startswith("describe")
                or q.startswith("with")
            )

            if is_read:
                return cursor.fetchall() if fetch_all else cursor.fetchone()

            # write query
            conn.commit()
            return None

        except mysql.connector.Error as err:
            logger.exception("QUERY ERROR: %s", err)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise

        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                # IMPORTANT: returns connection back to pool
                try:
                    conn.close()
                except Exception:
                    pass

    def execute_script(self, filepath):
        """Execute a .sql file (multiple statements)."""
        conn = None
        cursor = None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            with open(filepath, "r", encoding="utf-8") as f:
                sql_script = f.read()

            for _ in cursor.execute(sql_script, multi=True):
                pass

            conn.commit()
            logger.info("Script executed: %s", filepath)

        except FileNotFoundError:
            logger.exception("SQL script file not found: %s", filepath)
            raise
        except mysql.connector.Error as err:
            logger.exception("Error while executing sql script: %s", err)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
