from mngDB import MngDB
from pprint import pprint

class UserReport:
    def __init__(self):
        self.mngDB=MngDB()
        
    def print_user_stats(self,user_uid):
        user_stats=self.get_user_stats(user_uid)
        pprint(user_stats)
        
    def get_user_stats(self, user_uid):
        user_stats={}
        user_info=self.mngDB.get_obj("user",user_uid)
        org_uid=user_info['user_org_uid']
        
        user_stats['num_tasks']=self.mngDB.store.fetchall(f"select count(*) as num_tasks from tasks where task_user_uid='{user_uid}'")[0]['num_tasks']
        user_stats['num_kpis']=self.mngDB.store.fetchall(f"select count(kpis.*) as num_kpis from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where task_user_uid='{user_uid}'")[0]['num_kpis']
        user_stats['num_passed_sqls']=self.mngDB.store.fetchall(f"select count(kpis.*) as num_passed_sqls from kpis join tasks on kpis.kpi_task_uid=tasks.task_uid where task_user_uid='{user_uid}' and kpis.sql_passed=True")[0]['num_passed_sqls']
        user_stats['num_tables']=self.mngDB.store.fetchall(f"select count(*) as num_tables from tables where table_org_uid='{org_uid}'")[0]['num_tables']
        user_stats['num_cols']=self.mngDB.store.fetchall(f"select count(cols.*) as num_cols from cols join tables on cols.col_table_uid=tables.table_uid where tables.table_org_uid='{org_uid}'")[0]['num_cols']
                                                           
        return user_stats