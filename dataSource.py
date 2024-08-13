from sqlalchemy import create_engine, inspect,text # type: ignore
import logging

def destroy(obj,destructor_fn):
    if not isinstance(destructor_fn,list): destructor_fn=[destructor_fn]
    if obj: [obj.__getattribute__(fn)() for fn in destructor_fn]
    return None
    
class DataSource:
    def __init__(self,def_host="mysql+pymysql://taskanalytics:leningrad@localhost/",def_db="sys"):
        self.engine=None
        self.conn=None
        self.def_host=def_host
        self.def_db=def_db
        
    def close(self):
        self.conn=destroy(self.conn,["commit","close"])
        self.engine=destroy(self.engine,"dispose")
        
    def connect(self,db_name=None,echo=True): 
        if not db_name: db_name,echo=self.def_db,False
        return self.connect_str(self.def_host+db_name,echo=echo)
    
    def connect_str(self,conn_str="mysql+pymysql://taskanalytics:leningrad@localhost/accidents",echo=True):
        self.close()
        self.engine=create_engine(conn_str,echo=echo)
        self.conn=self.engine.connect()
        return self
        
    def fetch_tables(self):return inspect(self.engine).get_table_names()
    def fetch_columns(self,table_name="nesreca"): return inspect(self.engine).get_columns(table_name)
    def fetchall(self, statement):return self.execute(statement).mappings().all()
    def execute(self,statement): return self.conn.execute(text(statement))
    def fetch_samples(self,table_name,num_samples=3): return self.fetchall(f"select * from {table_name} LIMIT {num_samples}")
    
    def create_db(self,db_name,overwrite=True):
        if overwrite: self.drop_db(db_name)
        return self.connect().execute(f"create database {db_name}")
        
    def drop_db(self,db_name):
        if self.is_db_exist(db_name):self.execute(f"drop database {db_name}")
        return self
        
    def is_db_exist(self,db_name):
        existing_databases = self.fetchall("SHOW DATABASES")
        return db_name in [d['Database'] for d in existing_databases]
        
   
        
        
