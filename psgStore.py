postgres_cfg={
        "user": "taskanalytics",
        "password": "leningrad",
        "def_db":"postgres"}

import psycopg2,logging, uuid
from psycopg2.extras import RealDictCursor

class PostGreStore:
    def __init__(self,cfg=postgres_cfg):
        self.cfg=cfg
        self.conn=None
        
    def close(self): 
        if self.conn is not None:
            logging.info("closing connection")
            self.conn.commit()
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
        res=None
        with self.conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute(stmt)
            res=c.fetchall()
            res=[dict(r) for r in res] if res else None
        logging.info(f"fetch {stmt} with nrows:{len(res) if res else 0}")
        return res
    
    def find_objs(self,table_name,criteria):
        logging.info(f"find objs in {table_name} by {criteria}")
        return self.fetchall(f"select * from {table_name} where {criteria}")
        
    def find_obj(self,table_name,criteria):
        res=self.find_objs(table_name,criteria)
        return res[0] if res and len(res) else None
    
    def find_obj_id(self,table_name,pkey_name,criteria):
        res=self.find_obj(table_name,criteria)
        return res[pkey_name] if res else None
      
    def fetch_obj(self,table_name,pkey_name,uid):
        logging.info(f"find obj in {table_name} by {uid}")
        return self.find_obj(table_name,f"{pkey_name}='{uid}'")
    
    def fetch_obj_id(self,table_name,pkey_name,uid):
        return self.find_obj_id(table_name,pkey_name,f"{pkey_name}='{uid}'")
    
    def fetch_parent_obj(self,obj_type, parent_obj_type, value):
        obj=self.fetch_obj(obj_type+"s",obj_type+"_uid", value)
        return self.fetch_obj(parent_obj_type+"s",parent_obj_type+"_uid", obj[obj_type+"_"+parent_obj_type+"_uid"]) if obj else None
       
    def fetch_refs(self, table_name, fkey_name,value):
        res=self.fetchall(f"select * from {table_name} where {fkey_name}='{value}'")
        return res
        
    def del_obj(self, table_name, pkey_name, uid): self.execute(f"delete from {table_name} where {pkey_name}='{uid}'")
    def del_refs(self,table_name,fkey_name, value):return self.execute(f"delete from {table_name} where {fkey_name}='{value}'")
    def del_objs(self, table_name, pkey_name, uids):
        vals=",".join(f"'{uid}'" for uid in uids)
        self.execute(f"delete from {table_name} where {pkey_name} in ({vals})")
    
    def insert_obj(self,table_name, pkey_name,values):
        values[pkey_name]=str(uuid.uuid4())
        cols=",".join([k for k in values.keys()])
        vals=",".join([f"'{v}'" for v in values.values()])
        self.execute(f"insert into {table_name} ({cols}) VALUES ({vals})")
        return values
        
    def insert_objs(self, table_name,pkey_name,values_list):
        for values in values_list: self.insert_obj(table_name,pkey_name,values)
        return values
        
    def insert_objs_batch(self, table_name,pkey_name,values_list):
        for values in values_list: values[pkey_name]=str(uuid.uuid4())
        col_names=",".join(k for k in values_list[0].keys())
        vals=[','.join([f"'{v}'" for v in c.values()]) for c in values_list]
        mvals=",".join(f"({v})" for v in vals)
        self.execute(f"insert into {table_name} ({col_names}) values {mvals}")
        return values_list
        
    def update_obj(self, table_name,pkey_name,values):
        vals=",".join([f"{k}='{v}'" for k,v in values.items() if k!=pkey_name])
        self.execute(f"update {table_name} SET {vals} where {pkey_name}='{values[pkey_name]}'")
        return values
    
    def update_objs(self, table_name,pkey_name,values_list):
        for v in values_list: self.update_obj(table_name,pkey_name,v)
        return values_list
    
    def insert_or_update_obj(self, table_name, pkey_name, values):
        if values.get(pkey_name,None):
            self.update_obj(table_name, pkey_name,values)
        else:
            self.insert_obj(table_name, pkey_name,values)
        return values