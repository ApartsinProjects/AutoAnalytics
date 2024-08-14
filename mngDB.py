from psgStore import PostGreStore
import logging

def sql_text(s): return s.replace("'","''")

class MngDB:
    def __init__(self):
        self.store=PostGreStore().connect(db_name="taskanalytics")
        
    def describe_user(self, user_uid):
        user_info=self.get_obj("user",user_uid)
        org_info=self.get_obj("org",user_info["user_org_uid"]) if user_info else None
        tasks=self.store.fetch_refs("tasks","task_user_uid",user_uid) if user_info else None
        return user_info,org_info,tasks

    def update_obj(self,obj_type,value): return self.store.update_obj(obj_type+"s",obj_type+"_uid",value)
    def update_objs(self,obj_type,values):return self.store.update_objs(obj_type+"s",obj_type+"_uid",values)
    def get_org_tables(self,org_uid): return self.store.fetch_refs("tables","table_org_uid",org_uid)
    def get_table_columns(self, table_uid): return self.store.fetch_refs("cols","col_table_uid",table_uid)
    def get_obj(self,obj_type,uid): return self.store.fetch_obj(obj_type+"s",obj_type+"_uid",uid)
    def get_user_org(self): return self.store.get_obj("orgs")
    def get_user_kpis_ids(self, user_uid):
        res=self.store.fetchall(f"select kpis.kpi_uid from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where tasks.task_user_uid='{user_uid}'")
        return [r["kpi_uid"] for r in res]
    def create_objs_batch(self,obj_type,values): return self.store.insert_objs_batch(obj_type+"s",obj_type+"_uid",values)
    def create_or_update_obj(self, obj_type, vals): return self.store.insert_or_update_obj(obj_type+"s",obj_type+"_uid",vals)
    def find_update_obj(self, obj_type,criteria, values):
        values[obj_type+"_uid"]=self.store.find_obj_id(obj_type+"s",obj_type+"_uid",criteria)
        return self.store.update_obj(obj_type+"s",obj_type+"_uid",values)
        
    def create_or_update_user(self,user_info,org_info):
        user_info["user_org_uid"]=self.create_or_update_org(org_info)['org_uid']
        user_info["user_uid"]=self.store.find_obj_id("users","user_uid",f"user_name='{user_info['user_name']}'")
        return self.store.insert_or_update_obj("users","user_uid",user_info)
        
    def create_or_update_org(self, org_info):
        org_name=org_info["org_name"]
        org_info["org_uid"]=self.store.find_obj_id("orgs","org_uid",f"org_name='{org_name}'")
        return self.store.insert_or_update_obj("orgs","org_uid",org_info)
    
    def delete_org_scheme(self,org_uid):
        tables=self.store.fetch_refs("tables","table_org_uid",org_uid)
        for table in tables: self.store.del_refs("cols","col_table_uid",table['table_uid'])
        self.store.del_refs("tables","table_org_uid",org_uid)
        
    def delete_org(self,org_uid):
        self.delete_org_scheme()
        self.delete_org_users(org_uid)
        self.store.del_obj("orgs","orgs_uid",org_uid)   
        
    def delete_user(self, user_uid):
        self.delete_user_tasks(user_uid)
        self.store.del_obj("users", "user_uid",user_uid)       
   
    def delete_task_kpis(self, task_uid): self.store.del_refs("kpis","kpi_task_uid",task_uid)     
    def delete_task(self, task_uid): 
        self.delete_task_kpis(task_uid)
        self.store.del_obj("tasks", "task_uid",task_uid)   
        
    def delete_org_users(self,org_uid): 
        org_users=self.store.fetch_refs("users","user_uid","user_org_id",org_uid)
        for user in org_users: self.delete_user(user['user_uid'])
        
    def delete_user_tasks(self, user_uid):
        user_tasks=self.store.fetch_refs("tasks","task_user_uid",user_uid)
        for task in user_tasks: self.delete_task(task['task_uid'])
        
    def create_or_update_task(self, task_info):self.store.insert_or_update_obj("tasks","task_uid",task_info)
                
                
    
