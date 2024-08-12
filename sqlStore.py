postgres_cfg={
        "user": "taskanalytics",
        "password": "leningrad",
        "def_db":"postgres"}

import psycopg2,logging

class SQLStore:
    
    def __init__(self,cfg=postgres_cfg):
        self.cfg=cfg
        self.conn=None
        
    def close(self): 
        if self.conn is not None:
            logging.info("closing connection")
            self.conn.close()
            self.conn=None
        return self
    
    def connect(self,db_name=None,autocommit=True):
        self.close()
        if not db_name: db_name=self.cfg["def_db"]
        logging.info(f"connecting to {db_name}")
        self.conn=psycopg2.connect(f"dbname={db_name} user={self.cfg['user']} password={self.cfg['password']}") 
        self.conn.autocommit=autocommit
        return self
    
    def execute(self, stmt):
        logging.info(f"executing {stmt}")
        self.conn.cursor().execute(stmt)
        return self
    
    def fetchall(self,stmt):
        with self.conn.cursor() as c:
            logging.info(f"fetching{stmt}")
            c.execute(stmt)
            res=c.fetchall()
        return res
    
    def create_db(self,db_name,overwrite=True):
        if overwrite: self.drop_db(db_name)
        return self.connect().execute(f"create database {db_name}").connect(db_name)
        
    def drop_db(self,db_name):
        if self.is_db_exist(db_name):
            logging.info(f"dropping db {db_name}")
            self.connect().execute(f"drop database {db_name} WITH (FORCE)").connect(None)
        return self
        
    def is_db_exist(self,db_name):
        return self.fetchall(f"select exists(SELECT datname FROM pg_catalog.pg_database WHERE datname='{db_name}')")[0][0]
        
    def fetch_columns(self,table_name):
        return self.fetchall(f"SELECT column_name,data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
    
    def fetch_tables(self):
        return self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'")
    
    
        
 
        
        
        
        