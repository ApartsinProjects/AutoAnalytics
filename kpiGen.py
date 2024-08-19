from llmAgent import LLMAgent
from pydantic import BaseModel
import json
from mngDB import MngDB,sql_text
from schemePrompt import SchemePrompt
from collections import ChainMap

class KPI(BaseModel):
    KPI: str
    trends_or_patterns: str
    
class TaskKPIs(BaseModel):
    KPIs:list[KPI]
                 
class KPIGen:
    def __init__(self):
        self.mngDB=MngDB()
        self.llm=LLMAgent()
        
    def generate_user_kpis(self,user_uid):
        user_info,org_info,tasks_info=self.mngDB.describe_user(user_uid)
        self.schema_prompt=SchemePrompt().get_summary_prompt(user_uid)
        sys_msg=f"You are a business analyst designing a dashboard for a'{self.user_info['user_role']}' at {self.org_info['org_descr']}\
            You receive the following description for the available data including the known data gaps:{self.schema_prompt}"
        all_kpis=ChainMap(*[self.generate_task_kpi(sys_msg,task['task_uid']) for task in tasks])
        self.mngDB.create_objs_batch("kpi",list(all_kpis.values()))
        
    def generate_task_kpi(self,sys_msg, task_uid):
        self.mngDB.delete_task_kpis(task_uid)
        task=self.mngDB.get_obj("task",task_uid)
        user_msg=f"Identify and list KPIs that can be computed from the described data that are useful for accomplishing the task:'{task['task_name']}'\
        Specify KPIs names and descriptions in the terms appearing in the data description above excluding data gaps, don't use other terms.\
            Focus on simple and composite aggregations and distributions by various categories for spotting interesting patterns.\
                Describe the trends or patterns relevant to the task that might be discovered using the generated KPI"
           
        task_kpis=self.llm.struct_query(sys_msg,user_msg,TaskKPIs)
        return {sql_text(kpi.KPI):{'kpi_name':kpi.KPI, 
                                   'kpi_description':kpi.trends_or_patterns,
                                   "kpi_task_uid":task_uid} for kpi in task_kpis.KPIs}           