from baseAgent import BaseAgent
from sqlStore import SQLStore
import logging,uuid
from pydantic import BaseModel

user_info={"user_name":"John","user_role":"Fleet manager"}

org_info={"org_name":"Egged",
          "org_descr":"bus public transportation company",
          "org_conn_str":"dbname='acmebus' user='taskanalytics' password='leningrad' host='localhost' port='5432'",
          "org_data_app":"telematics solution"}


#generate job role responsibilities and tasks for each generated responsibility
class RoleResponsibility(BaseModel):
    job_responsibility: str 
    responsibility_tasks: list[str]
    
class RoleResponsibilities(BaseModel):
    job_responsibilities: list[RoleResponsibility]
  
class MetaDB:
    def __init__(self):
        self.store=SQLStore().connect(db_name="taskanalytics")
        self.llm=BaseAgent()
            
    def create_or_update_user(self,user_info,org_info):
        user_info["user_org_uid"]=self.create_or_update_org(org_info)
        user_name=user_info["user_name"]
        user_info["user_uid"]=self.store.find_obj("users","user_uid",f"user_name='{user_name}'")
        return self.store.insert_or_update_obj("users","user_uid",user_info)
        
    def create_or_update_org(self, org_info):
        org_name=org_info["org_name"]
        org_info["org_uid"]=self.store.find_obj("orgs","org_uid",f"org_name='{org_name}'")
        return self.store.insert_or_update_obj("orgs","org_uid",org_info)
        
    def delete_org(self,org_uid):
        self.delete_org_users(org_uid)
        self.store.del_obj("orgs","orgs_uid",org_uid)   
        
    def delete_user(self, user_uid):
        self.delete_user_tasks(user_uid)
        self.store.del_obj("users", "user_uid",user_uid)       
        
    def delete_task(self, task_uid): 
        self.delete_task_kpis(task_uid)
        self.store.del_obj("tasks", "task_uid",task_uid)   
        
    def delete_org_users(self,org_uid): 
        org_users_ids=self.store.fetch_refs("users","user_uid","user_org_id",org_uid)
        for user_uid in org_users_ids: self.delete_user(user_uid)
        
    def delete_user_tasks(self, user_uid):
        user_tasks_ids=self.store.fetch_refs("tasks","task_uid","task_user_uid",user_uid)
        for task_uid in user_tasks_ids: self.delete_task(task_uid)
          
    def delete_task_kpis(self, task_uid):
        self.store.del_refs("kpis", "kpi_uid","kpi_task_uid",task_uid)
        self.store.del_obj("task","task_uid",task_uid)
        
    def generate_user_tasks(self,user_uid):
        self.delete_user_tasks(user_uid)
        user_info=self.store.fetch_obj("users","user_uid",user_uid)
        org_info=self.store.fetch_obj("orgs","org_uid",user_info['user_org_uid'])
        sys_msg="You are a helpful business analyst"
        user_msg=f"Describe job responsibilities and tasks for each responsibility for job role:'{user_info['user_role']}' at {org_info['org_descr']}"
        role_responsibilities=self.llm.struct_query(sys_msg, user_msg,RoleResponsibilities)
        return self.insert_tasks(role_responsibilities.job_responsibilities,user_info['user_uid'])
        
    def insert_tasks(self, responsibilities, user_uid):
        self.delete_user_tasks(user_uid)
        for responsibility in responsibilities:
            for task in responsibility.responsibility_tasks:
                task_info={"task_name":task,"task_responsibility": responsibility.job_responsibility, "task_user_uid":user_uid}
                self.store.insert_or_update_obj("tasks","task_uid",task_info)
                
    def fetch_schema(self, org_uid):
        org_info=self.store.fetch_obj("orgs","org_uid",org_uid)
        remote_ds=SQLStore().connect_str(org_info["org_conn_str"])
        tables=remote_ds.fetch_tables()
        for t in tables:self.insert_cols(t,remote_ds.fetch_columns(t["tablename"]),org_uid)
    
    def insert_cols(self,t,cols,org_uid):
        col_dict=[{'col_uid':str(uuid.uuid4()),'col_name':c['column_name'],'col_type':c['data_type'],"table_name":t["tablename"],"table_org_uid":org_uid} for c in cols]
        col_names=",".join(k for k in col_dict[0].keys())
        vals=[','.join([f"'{v}'" for v in c.values()]) for c in col_dict]
        mvals=",".join(f"({v})" for v in vals)
        return self.store.execute(f"insert into cols ({col_names}) values {mvals}")
            
        
