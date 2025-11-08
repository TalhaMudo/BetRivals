import mysql.connector
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector: # a bridge between Flask and MySQL Database using connection pooling 
    def __init__(self):
        try:
            host = os.getenv('MYSQL_HOST')
            user = os.getenv('MYSQL_USER')
            password = os.getenv('MYSQL_PASSWORD', '')
            database = os.getenv('MYSQL_DB')
            port_env = os.getenv('MYSQL_PORT')
            port = int(port_env) if port_env else 3306

            # Ensure required values exist (database may be created if missing)
            if not host or not user or not database:
                raise ValueError("Database configuration error: check the .env file for MYSQL_HOST, MYSQL_USER and MYSQL_DB")

            self.poolconfig = {
                'host': host,
                'user': user,
                'password': password,
                'database': database,
                'port': port,
            }

            # Try creating connection pool. If the database does not exist create it and retry.
            try:
                self.pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="betrivals_pool",
                    pool_size=5,
                    **self.poolconfig
                )
            except mysql.connector.Error as err:
                if getattr(err, 'errno', None) == 1049: # (errno 1049) Unknown database
                    logger.info("Database '%s' does not exist, attempting to create it.", database)
                    try:
                        # connect without specifying database
                        tmp_conn = mysql.connector.connect(
                            host=host,
                            user=user,
                            password=password,
                            port=port
                        )
                        tmp_cursor = tmp_conn.cursor()
                        create_sql = f"CREATE DATABASE IF NOT EXISTS {database};"
                        tmp_cursor.execute(create_sql)
                        tmp_cursor.close()
                        tmp_conn.close()
                        logger.info(f"Database '{database}' created or already exists.")
                        # retry pool creation
                        self.pool = mysql.connector.pooling.MySQLConnectionPool(
                            pool_name="betrivals_pool",
                            pool_size=5,
                            **self.poolconfig
                        )
                    except mysql.connector.Error as e:
                        logger.exception(f"Failed to creating database '{database}': {e}")
                        raise
                else:
                    logger.exception(f"Error while connecting database: {err}")
                    raise

        except mysql.connector.Error as err:
            logger.exception(f"MySQL error during initialization: {err}")
            raise
        except Exception as e:
            logger.exception(f"Failed to initialize DatabaseConnector: {err}")
            raise

    def _get_connection(self):
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as err:
            logger.exception(f"Error while getting connection from pool: {err}")
            raise

    def _return_connection(self, conn):
        if conn:
            conn.close()

    def execute_query(self, query, params=None, fetch_all=True):
        conn = None
        cursor = None
        results = None
        
        try:
            conn = self._get_connection()
            # dictionary=True is for returning the results as dictionaries
            cursor = conn.cursor(dictionary=True) 
            
            cursor.execute(query, params)
            
            if fetch_all:
                results = cursor.fetchall() # SELECT
            else:
                conn.commit() # INSERT, UPDATE, DELETE
                
        except mysql.connector.Error as err:
            logger.exception(f"QUERY ERROR: {err}")
            if conn:
                conn.rollback() # if there is an error, rollback the transaction
            raise err
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._return_connection(conn)
            
        return results

    def execute_script(self, filepath): # instead of query, this takes a .sql file path
        conn = None
        cursor = None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            for result in cursor.execute(sql_script, multi=True):
                pass

            conn.commit()
            logger.info(f"Script executed: {filepath}")
            
        except FileNotFoundError:
            logger.exception(f"Error: SQL script file couldn't found: {filepath}")
            raise
        except mysql.connector.Error as err:
            logger.exception(f"Error while executing sql script: {err}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._return_connection(conn)