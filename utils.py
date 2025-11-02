import mysql.connector
import os

class DatabaseConnector: # a bridge between Flask and MySQL Database using connection pooling 
    def __init__(self):
        try:
            self.poolconfig = {
                'host': os.getenv('MYSQL_HOST'),
                'user': os.getenv('MYSQL_USER'),
                'password': os.getenv('MYSQL_PASSWORD'),
                'database': os.getenv('MYSQL_DB'),
            }
            
            if not all(self.poolconfig.values()):
                raise ValueError("Database configuration error: check the .env file for missing values.")

            # pool_size: maximum connection count
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="betrivals_pool",
                pool_size=5, 
                **self.poolconfig
            )

        except mysql.connector.Error as err:
            print(f"Error while connecting database: {err}")
            raise

    def _get_connection(self):
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as err:
            print(f"Error while getting connection from pool: {err}")
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
            print(f"QUERY ERROR: {err}")
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
            print(f"Script executed: {filepath}")
            
        except FileNotFoundError:
            print(f"Error: SQL script file couldn't found: {filepath}")
            raise
        except mysql.connector.Error as err:
            print(f"Error while executing sql script: {err}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._return_connection(conn)