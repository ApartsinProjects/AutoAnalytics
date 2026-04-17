from psgStore import PostGreStore,sql_text
import logging

class MngDB:
    def __init__(self):
        self.store=PostGreStore().connect(db_name="taskanalytics")
        
    def get_user(self,user_uid): return self.store.fetch_obj("user",user_uid)
    def get_org(self,org_uid): return self.store.fetch_obj("org",org_uid)
    def get_user_tasks(self, user_uid): return self.store.fetch_objs_by_ref("task", "user",user_uid)
    def get_org_tables(self,org_uid): return self.store.fetch_objs_by_ref("table","org",org_uid)
    def get_table_columns(self, table_uid): return self.store.fetch_objs_by_ref("col","table",table_uid)
    def get_user_kpis(self, user_uid):return self.store.fetch_objs_by_iref("kpi","task","user",user_uid)
    def update_or_insert_org(self,org_info): return self.store.insert_or_update_by_name("org",org_info)
    def update_or_insert_user(self,user_info): return self.store.insert_or_update_by_name("user",user_info)
    def get_org_tables(self,org_uid): return self.store.fetch_objs_by_ref('table','org',org_uid)
    def del_table_columns(self,table_uid): return self.store.del_objs_by_ref('col','table',table_uid)
    def del_org_cols(self,org_uid): return self.store.del_objs_by_iref('col','table','org',org_uid)
    def del_org_tables(self, org_uid): return self.store.del_objs_by_ref('table','org',org_uid)
    def del_org_users(self,org_uid):return self.store.del_objs_by_ref('user','org',org_uid)
    def del_org_scheme(self,org_uid):
        self.del_org_cols(org_uid)
        self.del_org_tables(org_uid)
    def del_org(self,org_uid): return self.store.del_obj('org',org_uid)
    def del_user(self,user_uid): return self.store.del_obj('user',user_uid)
    def del_user_kpis(self, user_uid): return self.store.del_objs_by_iref('kpi','task','user',user_uid)
    def del_user_tasks(self, user_uid): return self.store.del_objs_by_ref('task','user',user_uid)
    def insert_or_update_task(self, task_info): return self.store.insert_or_update_obj("task",task_info)
    def find_user(self, user_name): return self.store.find_obj("user",f"user_name='{user_name}'")
    def insert_org_tables(self,org_uid,tables):return self.store.insert_ref_objs('table','org',org_uid,tables)
    def insert_table_cols(self,table_uid,cols):return self.store.insert_ref_objs('col','table',table_uid,cols)
    def get_org_conn_str(self,org_uid): return self.get_org(org_uid)['org_conn_str']
    def update_org(self, org_uid, org_vals): return self.store.update_obj_by_id("org",org_uid,org_vals)
    def find_org_table(self,org_uid,table_name): return self.store.find_obj("table",f"table_name='{table_name}' and org_table_uid='{org_uid}'")
    def update_org_table_by_name(self, org_uid,table_info): 
        return self.store.update_obj_by_criteria("table",table_info,f"table_name='{table_info['table_name']}' and table_org_uid='{org_uid}'")
    def update_table_col_by_name(self,table_uid,col_info):
        return self.store.update_obj_by_criteria("col",col_info,f"col_name='{col_info['col_name']}' and col_table_uid='{table_uid}'")
        
    def describe_user(self, user_uid):
        user_info,user_tasks=self.get_user(user_uid),self.get_user_tasks(user_uid)
        org_info=self.get_org(user_info["user_org_uid"]) if user_info else None
        return user_info,org_info,user_tasks
    
    def delete_case_data(self,user_name):
        user_info=self.find_user(user_name)
        if user_info:
            user_uid,org_uid=user_info['user_uid'],user_info['user_org_uid']
            self.del_org_cols(org_uid)
            self.del_org_tables(org_uid)
            self.del_user_kpis(user_uid)
            self.del_user_tasks(user_uid)
            self.del_org_users(org_uid)
            self.del_org(org_uid)   
            
    def create_case(self,user_info,org_info):
        org_info=self.update_or_insert_org(org_info)
        user_info['user_org_uid']=org_info['org_uid']
        return self.update_or_insert_user(user_info)
