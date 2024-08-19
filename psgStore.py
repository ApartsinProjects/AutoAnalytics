postgres_cfg={
        "user": "taskanalytics",
        "password": "leningrad",
        "def_db":"postgres"}

import psycopg2,logging, uuid
import json
from psycopg2.extras import RealDictCursor

def pkey(obj_type): return obj_type+"_uid"
def tbl(obj_type): return obj_type+"s"
def fkey(obj_type,fobj_type): return f"{obj_type}_{fobj_type}_uid"
def first_obj(objs): return objs[0] if objs and len(objs) else None
def sql_text(s): 
    if s==None : return 'NULL'
    if isinstance(s, dict) or isinstance(s,list): s=json.dumps(s)
    return "'"+s.replace("'","''")+"'" 
def pkey_dict(obj_type,obj_uid): return {pkey(obj_type):obj_uid}
def fkey_dict(obj_type,ref_obj_type,ref_obj_uid): return {fkey(obj_type,ref_obj_type):ref_obj_uid}
def with_pkey(obj_type,obj_uid,obj_vals): return {**obj_vals,**pkey_dict(obj_type,obj_uid)}
def with_fkey(obj_type,ref_obj_type,ref_obj_uid,obj_vals): return {**obj_vals,**fkey_dict(obj_type,ref_obj_type,ref_obj_uid)}

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
        logging.info(f"executing:{stmt}")
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
    
    def find_objs(self,obj_type,criteria):return self.fetchall(f"select * from {tbl(obj_type)} where {criteria}") 
    def find_obj(self,obj_type,criteria): return first_obj(self.find_objs(obj_type,criteria))
        
    def fetch_objs_by_ref(self,obj_type, ref_obj_type, ref_obj_uid):return self.find_objs(obj_type, f"{fkey(obj_type,ref_obj_type)}='{ref_obj_uid}'")
    def fetch_obj_by_ref(self,obj_type, ref_obj_type, ref_obj_uid): return first_obj(self.fetch_objs_by_ref(self,obj_type, ref_obj_type, ref_obj_uid))    
    
    def fetch_objs_by_iref(self,obj_type, ref_obj_type, iref_obj_type, iref_uid):
        return self.fetchall(f"select {tbl(obj_type)}.* from {tbl(obj_type)} join {tbl(ref_obj_type)} on\
            {fkey(obj_type, ref_obj_type)}={pkey(ref_obj_type)} where {fkey(ref_obj_type, iref_obj_type)}='{iref_uid}'")
    
    def fetch_obj(self,obj_type,obj_uid):return self.find_obj(obj_type,f"{pkey(obj_type)}='{obj_uid}'")
    def fetch_ref(self,obj_type, ref_obj_type, obj_uid):
        obj=self.fetch_obj(obj_type, obj_uid)
        return self.fetch_obj(ref_obj_type, obj[fkey(obj_type,ref_obj_type)]) if obj else None   
    def del_objs(self,obj_type,obj_uids):
        vals=",".join(f"'{uid}'" for uid in obj_uids)
        return self.execute(f"delete from {tbl(obj_type)} where {pkey(obj_type)} in ({vals})")
    def del_objs_by_ref(self,obj_type,ref_type, ref_uid):return self.execute(f"delete from {tbl(obj_type)} where {fkey(obj_type,ref_type)}='{ref_uid}'")
    def del_obj(self, obj_type,obj_uid): return self.execute(f"delete from {tbl(obj_type)} where {pkey(obj_type)}='{obj_uid}'")
    def del_objs_by_iref(self,obj_type, ref_obj_type, iref_obj_type, iref_uid):
        objs=self.fetch_objs_by_iref(obj_type,ref_obj_type,iref_obj_type,iref_uid) 
        return self.del_objs(obj_type,[o[pkey(obj_type)] for o in objs]) if objs else None
    
    def insert_objs(self, obj_type,objs_vals): return [self.insert_obj(obj_type,obj_vals) for obj_vals in objs_vals]
    def insert_objs_batch(self, obj_type,objs_vals): #batch insert
        for obj_vals in objs_vals: obj_vals[pkey(obj_type)]=str(uuid.uuid4())
        col_names=",".join(k for k in objs_vals[0].keys())
        col_vals=[','.join([f"{sql_text(v)}" for v in obj_vals.values()]) for obj_vals in objs_vals]
        cols_vals=",".join(f"({v})" for v in col_vals)
        self.execute(f"insert into {tbl(obj_type)} ({col_names}) values {cols_vals}")
        return objs_vals
    def insert_ref_objs(self,obj_type,ref_obj_type, ref_uid,objs_values): return self.insert_objs(obj_type,[with_fkey(obj_type,ref_obj_type,ref_uid,obj_vals) for obj_vals in objs_values])
    def insert_obj(self,obj_type,obj_vals):
        obj_vals[pkey(obj_type)]=str(uuid.uuid4())
        cols=",".join([k for k in obj_vals.keys()])
        vals=",".join([f"{sql_text(v)}" for v in obj_vals.values()])
        self.execute(f"insert into {tbl(obj_type)} ({cols}) VALUES ({vals})")
        return obj_vals    
    
    def update_objs(self, obj_type,objs_vals): return [self.update_obj(obj_type,obj_vals) for obj_vals in objs_vals]    
    def update_obj(self, obj_type,obj_vals):
        vals=",".join([f"{k}={sql_text(v)}" for k,v in obj_vals.items() if k!=pkey(obj_type)])
        self.execute(f"update {tbl(obj_type)} SET {vals} where {pkey(obj_type)}='{obj_vals[pkey(obj_type)]}'")
        return obj_vals
    def update_obj_by_id(self,obj_type, obj_uid, obj_vals): return self.update_obj(obj_type,with_pkey(obj_type, obj_uid,obj_vals))
    def insert_or_update_obj(self, obj_type, obj_vals):return self.update_obj(obj_type, obj_vals) if obj_vals.get(pkey(obj_type),None) else self.insert_obj(obj_type,obj_vals)
    def update_obj_by_criteria(self,obj_type,obj_vals, criteria):
        obj=self.find_obj(obj_type,criteria)
        return self.update_obj(obj_type,with_pkey(obj_type,obj[pkey(obj_type)],obj_vals)) if obj else None
    def insert_or_update_obj_by_criteria(self,obj_type,obj_vals, criteria):
        obj=self.find_obj(obj_type,criteria)
        return self.update_obj(obj_type,obj[pkey(obj_type)],obj_vals) if obj else self.insert_obj(obj_type,obj_vals)
    def insert_or_update_by_name(self,obj_type,obj_vals):return self.insert_or_update_obj_by_criteria(obj_type,obj_vals,f"{obj_type}_name='{obj_vals[obj_type+'_name']}'")
        