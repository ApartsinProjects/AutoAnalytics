from sqlalchemy import create_engine, inspect ,event,Engine,text # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.event import listen

statement_timeout=20 #in seconds

@event.listens_for(Engine, "before_cursor_execute")
def _set_timeout(conn, cursor, stmt, params, context, executemany):
    timeout = context.execution_options.get('timeout', None)
    if timeout: 
        cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={timeout*1000}")
        logging.info(f"setting cursor timeout {timeout} sec")

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
    def fetch_table_pkeys(self,table_name): return inspect(self.engine).get_pk_constraint(table_name)
    def fetch_table_fkeys(self,table_name): return inspect(self.engine).get_foreign_keys(table_name)
        
    def fetch_columns(self,table_name="nesreca"): return inspect(self.engine).get_columns(table_name)
    def fetchall(self, statement):
        res=self.execute(statement).mappings().all()
        return [dict(r) for r in res] if res else None
    
    def execute(self,statement): return self.conn.execute(text(statement))
    
    def fetchall_with_diagnostics(self, statement, max_records=None):
        res,error=self.execute_with_diagnostics(statement,max_records)
        if max_records:
            res=[dict(r) for r in res.mappings().fetchmany(max_records)] if res else None
        else:
            res=[dict(r) for r in res.mappings().all()] if res else None
        if error: logging.info(f"fetch error {error}")
        return res,error
    
    def inject_limit(self,stmt,statement_max_records):
        if stmt[-1]==";": stmt=stmt[:-1]
        return stmt+ f" \n LIMIT {statement_max_records};"
     
    def execute_with_diagnostics(self,stmt,max_records=None):
        error,res=None,None
        stmt= self.inject_limit(stmt,max_records)
        try:
            res=self.conn.execute(text(stmt).execution_options(timeout=statement_timeout))
        except SQLAlchemyError as e:
            logging.info(f"exception {e} during execution of {stmt}")
            error=str(e.__dict__['orig'])
            logging.info(f"error executing {stmt} with {error}")
        return res,error
    
    def fetch_samples(self,table_name,num_samples=3): return self.fetchall(f"select * from `{table_name}` LIMIT {num_samples}")
    
    def create_db(self,db_name,overwrite=True):
        if overwrite: self.drop_db(db_name)
        return self.connect().execute(f"create database {db_name}")
        
    def drop_db(self,db_name):
        if self.is_db_exist(db_name):self.execute(f"drop database {db_name}")
        return self
        
    def is_db_exist(self,db_name):
        existing_databases = self.fetchall("SHOW DATABASES")
        return db_name in [d['Database'] for d in existing_databases]
        
   
        
        
