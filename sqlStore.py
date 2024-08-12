postgres_cfg={
        "user": "taskanalytics",
        "password": "leningrad",
        "def_db":"postgres"}

import psycopg2,logging, uuid
from psycopg2.extras import RealDictCursor

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
    
    def connect_str(self,conn_str,autocommit=True):
        self.conn=psycopg2.connect(conn_str) 
        self.conn.autocommit=autocommit
        return self
    
    def connect(self,db_name=None,autocommit=True):
        self.close()
        if not db_name: db_name=self.cfg["def_db"]
        logging.info(f"connecting to {db_name}")
        return self.connect_str(f"dbname={db_name} user={self.cfg['user']} password={self.cfg['password']}",autocommit) 
        
    def execute(self, stmt):
        logging.info(f"executing {stmt}")
        self.conn.cursor().execute(stmt)
        return self
    
    def fetchall(self,stmt):
        with self.conn.cursor(cursor_factory=RealDictCursor) as c:
            logging.info(f"fetching{stmt}")
            c.execute(stmt)
            res=c.fetchall()
        return res
    
    def find_obj(self,table_name,pkey_name,criteria):
        logging.info(f"find obj in {table_name} by {criteria}")
        res=self.fetchall(f"select {pkey_name} from {table_name} where {criteria}")
        return res[0][pkey_name] if len(res) else None
    
    def fetch_obj(self,table_name,pkey_name,uid):
        logging.info(f"find obj in {table_name} by {uid}")
        res=self.fetchall(f"select * from {table_name} where {pkey_name}='{uid}'")
        return res[0] if len(res) else None
    
    def del_obj(self, table_name, pkey_name, uid): self.execute(f"delete * from {table_name} where {pkey_name}='{uid}'")
    def del_objs(self, table_name, pkey_name, uids):
        vals=",".join(f"'{uid}'" for uid in uids)
        self.execute("delete * from {table_name} where {pkey_name} in ({vals})")
    
    def fetch_refs(self, table_name, pkey_name, fkey_name,value):
        res=self.fetchall(f"select {pkey_name} from {table_name} where '{fkey_name}'='{value}'")
        return [r[0] for r in res]
    
    def insert_or_update_obj(self, table_name, pkey_name, values):
        if values.get(pkey_name,None):
            vals=",".join([f"{k}='{v}'" for k,v in values.items() if k!=pkey_name])
            self.execute(f"update {table_name} SET {vals} where {pkey_name}='{values[pkey_name]}'")
        else:
            values[pkey_name]=str(uuid.uuid4())
            cols=",".join([k for k in values.keys()])
            vals=",".join([f"'{v}'" for v in values.values()])
            self.execute(f"insert into {table_name} ({cols}) VALUES ({vals})")
        return values[pkey_name]
            
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
    
    
        
 
        
        
        
        